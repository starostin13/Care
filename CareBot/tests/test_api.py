"""
Tests for the Android REST API (api.py).

These tests exercise the Flask blueprint using the test client so they run
fully in-memory without a real database or Telegram connection.
"""
import os
import sys
import types
import json
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

MODULE_DIR = os.path.join(os.path.dirname(__file__), '..', 'CareBot')
sys.path.insert(0, os.path.abspath(MODULE_DIR))

os.environ['CAREBOT_TEST_MODE'] = 'true'
sys.modules.setdefault("config", types.SimpleNamespace(TEST_MODE=True))

# ---------------------------------------------------------------------------
# Stub heavy dependencies so imports succeed in the test environment.
# ---------------------------------------------------------------------------

_telegram_stub = types.ModuleType("telegram")
sys.modules.setdefault("telegram", _telegram_stub)
sys.modules.setdefault("telegram.ext", types.ModuleType("telegram.ext"))

_ns = types.SimpleNamespace(
    ContextTypes=MagicMock(),
    Application=MagicMock(),
    CommandHandler=MagicMock(),
    MessageHandler=MagicMock(),
    ConversationHandler=MagicMock(),
    filters=MagicMock(),
    CallbackQueryHandler=MagicMock(),
)
sys.modules["telegram.ext"] = _ns

for mod in [
    "notification_service",
    "mission_message_builder",
    "schedule_helper",
    "localization",
    "keyboard_constructor",
    "settings_helper",
    "register_features",
    "common_resource_feature",
]:
    sys.modules.setdefault(mod, types.ModuleType(mod))

from flask import Flask  # noqa: E402
from api import api_bp  # noqa: E402


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def make_app() -> Flask:
    app = Flask(__name__)
    app.register_blueprint(api_bp)
    app.config["TESTING"] = True
    return app


_BOOTSTRAP_PAYLOAD = {
    "generated_at": "2025-01-01T00:00:00Z",
    "alliances": [
        {"id": 1, "name": "Ultramarines", "common_resource": 10},
    ],
    "warmasters": [
        {
            "telegram_id": "100",
            "alliance": 1,
            "nickname": "Cato",
            "faction": "Space Marines",
            "language": "ru",
            "notifications_enabled": True,
            "is_admin": False,
        }
    ],
    "map": {
        "cells": [{"id": 1, "planet_id": 1, "state": None, "patron": 1, "has_warehouse": False}],
        "edges": [{"id": 1, "left_hexagon": 1, "right_hexagon": 2, "state": None}],
    },
    "pending_missions": [],
}

_MOCK_MISSION_DETAILS = MagicMock()
_MOCK_MISSION_DETAILS.id = 7
_MOCK_MISSION_DETAILS.deploy = "Hammer & Anvil"
_MOCK_MISSION_DETAILS.rules = "killteam"
_MOCK_MISSION_DETAILS.cell = 1
_MOCK_MISSION_DETAILS.mission_description = "Loot"
_MOCK_MISSION_DETAILS.winner_bonus = None
_MOCK_MISSION_DETAILS.status = 1
_MOCK_MISSION_DETAILS.created_date = "2025-01-01"
_MOCK_MISSION_DETAILS.map_description = None
_MOCK_MISSION_DETAILS.reward_config = None


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

class TestBootstrapEndpoint:
    def test_returns_200_with_full_payload(self):
        """GET /api/bootstrap should return 200 with game state data."""
        app = make_app()
        with patch("api.build_bootstrap_payload", new=AsyncMock(return_value=_BOOTSTRAP_PAYLOAD)):
            with app.test_client() as client:
                resp = client.get("/api/bootstrap")
        assert resp.status_code == 200
        data = json.loads(resp.data)
        assert "alliances" in data
        assert "warmasters" in data
        assert "map" in data
        assert "pending_missions" in data
        assert data["alliances"][0]["name"] == "Ultramarines"


class TestCreateMissionEndpoint:
    def test_returns_400_when_fields_missing(self):
        """POST /api/missions without required fields returns 400."""
        app = make_app()
        with app.test_client() as client:
            resp = client.post(
                "/api/missions",
                json={"rules": "killteam"},
            )
        assert resp.status_code == 400
        data = json.loads(resp.data)
        assert "error" in data

    def test_creates_mission_successfully(self):
        """POST /api/missions with valid payload returns 201 and battle_id."""
        app = make_app()

        mock_mission_tuple = (
            "Hammer & Anvil", "Strategic Reserves", "killteam", 1, 7, None
        )

        with (
            patch("api.mission_helper.get_mission", new=AsyncMock(return_value=mock_mission_tuple)),
            patch("api.mission_helper.start_battle", new=AsyncMock(return_value=42)),
            patch("api.sqllite_helper.lock_mission", new=AsyncMock()),
            patch(
                "api.sqllite_helper.get_mission_details",
                new=AsyncMock(return_value=_MOCK_MISSION_DETAILS),
            ),
        ):
            with app.test_client() as client:
                resp = client.post(
                    "/api/missions",
                    json={"rules": "killteam", "attacker_id": "1", "defender_id": "2"},
                )

        assert resp.status_code == 201
        data = json.loads(resp.data)
        assert data["battle_id"] == 42
        assert data["mission"]["id"] == 7
        assert data["mission"]["rules"] == "killteam"


class TestSubmitBattleResultEndpoint:
    def test_returns_400_when_fields_missing(self):
        """POST /api/battles/<id>/result without required fields returns 400."""
        app = make_app()
        with app.test_client() as client:
            resp = client.post("/api/battles/1/result", json={})
        assert resp.status_code == 400

    def test_returns_404_when_battle_not_found(self):
        """POST /api/battles/<id>/result returns 404 for unknown battle."""
        app = make_app()
        with patch(
            "api.sqllite_helper.get_mission_id_for_battle",
            new=AsyncMock(return_value=None),
        ):
            with app.test_client() as client:
                resp = client.post(
                    "/api/battles/999/result",
                    json={
                        "fstplayer_score": 5,
                        "sndplayer_score": 3,
                        "submitter_id": "42",
                    },
                )
        assert resp.status_code == 404
        data = json.loads(resp.data)
        assert data["status"] == "not_found"

    def test_returns_409_when_already_confirmed(self):
        """POST /api/battles/<id>/result returns 409 for already-confirmed battle."""
        app = make_app()
        mock_details = MagicMock()
        mock_details.status = 3
        mock_details.rules = "killteam"

        with (
            patch("api.sqllite_helper.get_mission_id_for_battle", new=AsyncMock(return_value=1)),
            patch("api.sqllite_helper.get_mission_details", new=AsyncMock(return_value=mock_details)),
        ):
            with app.test_client() as client:
                resp = client.post(
                    "/api/battles/5/result",
                    json={
                        "fstplayer_score": 5,
                        "sndplayer_score": 3,
                        "submitter_id": "42",
                    },
                )
        assert resp.status_code == 409
        data = json.loads(resp.data)
        assert data["status"] == "already_confirmed"

    def test_applies_result_successfully(self):
        """POST /api/battles/<id>/result returns 200 and rewards on success."""
        app = make_app()
        mock_details = MagicMock()
        mock_details.status = 1
        mock_details.rules = "killteam"

        with (
            patch("api.sqllite_helper.get_mission_id_for_battle", new=AsyncMock(return_value=1)),
            patch("api.sqllite_helper.get_mission_details", new=AsyncMock(return_value=mock_details)),
            patch("api.mission_helper.write_battle_result", new=AsyncMock()),
            patch("api.mission_helper.apply_mission_rewards", new=AsyncMock(return_value={"xp": 50})),
            patch("api.map_helper.update_map", new=AsyncMock()),
            patch("api.sqllite_helper.update_mission_status", new=AsyncMock()),
        ):
            with app.test_client() as client:
                resp = client.post(
                    "/api/battles/1/result",
                    json={
                        "fstplayer_score": 8,
                        "sndplayer_score": 4,
                        "submitter_id": "42",
                    },
                )
        assert resp.status_code == 200
        data = json.loads(resp.data)
        assert data["status"] == "applied"
        assert data["rewards"] == {"xp": 50}


class TestSyncBattleResultsEndpoint:
    def test_returns_400_when_no_results_array(self):
        """POST /api/battles/sync without results array returns 400."""
        app = make_app()
        with app.test_client() as client:
            resp = client.post("/api/battles/sync", json={})
        assert resp.status_code == 400

    def test_processes_multiple_entries(self):
        """POST /api/battles/sync processes each entry and returns results array."""
        app = make_app()
        mock_details = MagicMock()
        mock_details.status = 1
        mock_details.rules = "killteam"

        with (
            patch("api.sqllite_helper.get_mission_id_for_battle", new=AsyncMock(return_value=1)),
            patch("api.sqllite_helper.get_mission_details", new=AsyncMock(return_value=mock_details)),
            patch("api.mission_helper.write_battle_result", new=AsyncMock()),
            patch("api.mission_helper.apply_mission_rewards", new=AsyncMock(return_value={})),
            patch("api.map_helper.update_map", new=AsyncMock()),
            patch("api.sqllite_helper.update_mission_status", new=AsyncMock()),
        ):
            with app.test_client() as client:
                resp = client.post(
                    "/api/battles/sync",
                    json={
                        "results": [
                            {
                                "battle_id": 1,
                                "fstplayer_score": 5,
                                "sndplayer_score": 3,
                                "submitter_id": "42",
                            },
                            {
                                "battle_id": 2,
                                "fstplayer_score": 7,
                                "sndplayer_score": 2,
                                "submitter_id": "42",
                            },
                        ]
                    },
                )
        assert resp.status_code == 200
        data = json.loads(resp.data)
        assert len(data["results"]) == 2
        assert all(r["status"] == "applied" for r in data["results"])

    def test_marks_invalid_entries(self):
        """Entries missing required fields are marked as invalid."""
        app = make_app()
        with app.test_client() as client:
            resp = client.post(
                "/api/battles/sync",
                json={"results": [{"battle_id": 1}]},
            )
        assert resp.status_code == 200
        data = json.loads(resp.data)
        assert data["results"][0]["status"] == "invalid"
