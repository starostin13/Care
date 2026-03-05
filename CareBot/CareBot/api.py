"""REST API surface to support Android client workflows.

Provides endpoints for offline caching, mission generation, and battle
result synchronization using existing mission/map helpers.
"""

import asyncio
from datetime import datetime
from typing import Any, Dict, List, Optional

from flask import Blueprint, jsonify, request

import map_helper
import mission_helper
import sqllite_helper

api_bp = Blueprint("api", __name__, url_prefix="/api")


def run_async(coro):
    """Run an async coroutine from sync Flask handlers."""
    return asyncio.run(coro)


def mission_details_to_dict(details) -> Optional[Dict[str, Any]]:
    if details is None:
        return None
    return {
        "id": details.id,
        "deploy": details.deploy,
        "rules": details.rules,
        "cell": details.cell,
        "mission_description": details.mission_description,
        "winner_bonus": details.winner_bonus,
        "status": details.status,
        "created_date": details.created_date,
        "map_description": getattr(details, "map_description", None),
        "reward_config": getattr(details, "reward_config", None),
    }


async def build_bootstrap_payload() -> Dict[str, Any]:
    alliances, warmasters, map_cells, edges, pending = await asyncio.gather(
        sqllite_helper.get_all_alliances_detailed(),
        sqllite_helper.get_all_warmasters_full(),
        sqllite_helper.get_map_cells_snapshot(),
        sqllite_helper.get_map_edges_snapshot(),
        sqllite_helper.get_all_pending_missions(),
    )
    return {
        "generated_at": datetime.utcnow().isoformat() + "Z",
        "alliances": alliances,
        "warmasters": warmasters,
        "map": {
            "cells": map_cells,
            "edges": edges,
        },
        "pending_missions": [
            {
                "id": row[0],
                "deploy": row[1],
                "rules": row[2],
                "cell": row[3],
                "mission_description": row[4],
                "created_date": row[5],
            }
            for row in pending
        ],
    }


@api_bp.get("/bootstrap")
def get_bootstrap():
    """Return cached data needed for offline mission generation."""
    payload = run_async(build_bootstrap_payload())
    return jsonify(payload)


@api_bp.post("/missions")
def create_mission():
    """Generate mission and create battle for two participants."""
    payload = request.get_json(silent=True) or {}
    rules = payload.get("rules")
    attacker_id = payload.get("attacker_id")
    defender_id = payload.get("defender_id")

    if not rules or not attacker_id or not defender_id:
        return (
            jsonify(
                {
                    "error": "rules, attacker_id, and defender_id are required",
                }
            ),
            400,
        )

    attacker_id = str(attacker_id)
    defender_id = str(defender_id)

    try:
        mission_tuple = run_async(
            mission_helper.get_mission(
                rules=rules, attacker_id=attacker_id, defender_id=defender_id
            )
        )
        mission_id = mission_tuple[4]
        battle_id = run_async(
            mission_helper.start_battle(mission_id, attacker_id, defender_id)
        )
        run_async(sqllite_helper.lock_mission(mission_id))
        mission_details = run_async(sqllite_helper.get_mission_details(mission_id))
    except Exception as exc:  # pragma: no cover - defensive
        return jsonify({"error": str(exc)}), 500

    response = {
        "battle_id": battle_id,
        "mission": mission_details_to_dict(mission_details),
    }
    return jsonify(response), 201


async def process_battle_result(
    battle_id: int, fstplayer_score: int, sndplayer_score: int, submitter_id: str
) -> Dict[str, Any]:
    mission_id = await sqllite_helper.get_mission_id_for_battle(battle_id)
    if not mission_id:
        return {"status": "not_found", "battle_id": battle_id}

    mission_details = await sqllite_helper.get_mission_details(mission_id)
    if mission_details and mission_details.status == 3:
        return {
            "status": "already_confirmed",
            "battle_id": battle_id,
            "mission_id": mission_id,
        }

    user_reply = f"{fstplayer_score} {sndplayer_score}"
    await mission_helper.write_battle_result(battle_id, user_reply)
    rewards = await mission_helper.apply_mission_rewards(
        battle_id, user_reply, submitter_id
    )
    scenario = mission_details.rules if mission_details else None
    await map_helper.update_map(battle_id, user_reply, submitter_id, scenario)
    await sqllite_helper.update_mission_status(mission_id, 3)

    return {
        "status": "applied",
        "battle_id": battle_id,
        "mission_id": mission_id,
        "mission_status": 3,
        "rewards": rewards,
    }


def _extract_scores(payload: Dict[str, Any]) -> Optional[List[int]]:
    try:
        return [int(payload["fstplayer_score"]), int(payload["sndplayer_score"])]
    except Exception:
        return None


@api_bp.post("/battles/<int:battle_id>/result")
def submit_battle_result(battle_id: int):
    """Store battle result and apply consequences."""
    payload = request.get_json(silent=True) or {}
    submitter_id = payload.get("submitter_id")
    scores = _extract_scores(payload)
    if submitter_id is None or scores is None:
        return (
            jsonify(
                {
                    "error": "submitter_id, fstplayer_score, sndplayer_score are required",
                }
            ),
            400,
        )

    try:
        result = run_async(
            process_battle_result(
                battle_id, scores[0], scores[1], str(submitter_id)
            )
        )
    except Exception as exc:  # pragma: no cover - defensive
        return jsonify({"error": str(exc)}), 500

    status = 200
    if result["status"] == "not_found":
        status = 404
    elif result["status"] == "already_confirmed":
        status = 409

    return jsonify(result), status


@api_bp.post("/battles/sync")
def sync_battle_results():
    """Process multiple battle results in one request."""
    payload = request.get_json(silent=True) or {}
    results_payload = payload.get("results")
    if not isinstance(results_payload, list):
        return jsonify({"error": "results array is required"}), 400

    processed: List[Dict[str, Any]] = []
    for entry in results_payload:
        scores = _extract_scores(entry) if isinstance(entry, dict) else None
        battle_id = entry.get("battle_id") if isinstance(entry, dict) else None
        submitter_id = entry.get("submitter_id") if isinstance(entry, dict) else None
        if (
            battle_id is None
            or submitter_id is None
            or scores is None
        ):
            processed.append(
                {
                    "status": "invalid",
                    "battle_id": battle_id,
                    "message": "battle_id, submitter_id, fstplayer_score, sndplayer_score are required",
                }
            )
            continue

        try:
            processed.append(
                run_async(
                    process_battle_result(
                        int(battle_id), scores[0], scores[1], str(submitter_id)
                    )
                )
            )
        except Exception as exc:  # pragma: no cover - defensive
            processed.append(
                {
                    "status": "error",
                    "battle_id": battle_id,
                    "message": str(exc),
                }
            )

    return jsonify({"results": processed})
