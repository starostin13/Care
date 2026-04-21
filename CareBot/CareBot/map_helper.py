#!/usr/bin/env python
# -*- coding: utf-8 -*-
# vim:fileencoding=utf-8
from ast import Tuple
from math import e, fabs
from typing import Optional
import config

# Автоматическое переключение на mock версию в тестовом режиме
if config.TEST_MODE:
    import mock_sqlite_helper as sqllite_helper
    print("🧪 Map Helper using MOCK SQLite helper")
else:
    import sqllite_helper
    print("✅ Map Helper using REAL SQLite helper")
import logging
import random

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
# set higher logging level for httpx to avoid all GET and POST requests being logged
logging.getLogger("httpx").setLevel(logging.WARNING)

logger = logging.getLogger(__name__)

async def update_map(battle_id, battle_result, user_telegram_id, scenario: Optional[str]):
    # Results are stored in fstplayer/sndplayer order.
    scores = battle_result.split()
    if len(scores) != 2:
        logger.error("Invalid battle_result format: %s", battle_result)
        return

    fstplayer_score = int(scores[0])
    sndplayer_score = int(scores[1])

    # If draw, do nothing.
    if fstplayer_score == sndplayer_score:
        logger.info("Draw in battle")
        return

    mission_id = await sqllite_helper.get_mission_id_for_battle(battle_id)
    if not mission_id:
        logger.error("Missing mission_id for battle %s", battle_id)
        return

    mission_details = await sqllite_helper.get_mission_details(mission_id)
    rules = mission_details.rules if mission_details else scenario
    mission_type = mission_details.deploy if mission_details else None
    if mission_type is None and scenario and scenario not in ("killteam", "wh40k"):
        mission_type = scenario
    if isinstance(rules, str):
        rules = rules.lower()
    if isinstance(mission_type, str):
        mission_type = mission_type.lower()

    participants = await sqllite_helper.get_battle_participants(battle_id)
    if not participants:
        logger.error("Missing participants for battle %s", battle_id)
        return

    fstplayer_id, sndplayer_id = participants

    # Determine winner/loser from fstplayer/sndplayer scores.
    if fstplayer_score > sndplayer_score:
        winner_telegram_id = fstplayer_id
        loser_telegram_id = sndplayer_id
    else:
        winner_telegram_id = sndplayer_id
        loser_telegram_id = fstplayer_id

    # Ensure ids are plain strings.
    if isinstance(winner_telegram_id, tuple):
        winner_telegram_id = winner_telegram_id[0]
    if isinstance(loser_telegram_id, tuple):
        loser_telegram_id = loser_telegram_id[0]

    if rules == "wh40k":
        cell_id = await sqllite_helper.get_cell_id_by_battle_id(battle_id)
        logger.info("Cell id: %s", cell_id)

        winner_alliance_id = await sqllite_helper.get_alliance_of_warmaster(
            winner_telegram_id)
        logger.info("Winner alliance id: %s", winner_alliance_id)

        if winner_alliance_id:
            await sqllite_helper.set_cell_patron(cell_id, winner_alliance_id[0])

            new_patron_faction = await sqllite_helper.get_faction_of_warmaster(
                winner_telegram_id)
            await sqllite_helper.add_to_story(
                cell_id,
                f"Находилась под контролем {new_patron_faction[0]}"
            )
        return

    if rules == "killteam":
        cell_id = await sqllite_helper.get_cell_id_by_battle_id(battle_id)

        # Attacker is always fstplayer in start_battle().
        if winner_telegram_id == fstplayer_id:
            winner_alliance_id = await sqllite_helper.get_alliance_of_warmaster(
                winner_telegram_id)
            if winner_alliance_id:
                await sqllite_helper.set_cell_patron(cell_id, winner_alliance_id[0])

        if mission_type == "secure":
            # For secure: winner creates a warehouse on a random owned hex.
            winner_alliance_id = await sqllite_helper.get_alliance_of_warmaster(
                winner_telegram_id)
            if winner_alliance_id:
                alliance_hexes = await sqllite_helper.get_hexes_by_alliance(
                    winner_alliance_id[0])

                available_hexes = [
                    hex_id[0]
                    for hex_id in alliance_hexes
                    if not await sqllite_helper.has_warehouse_in_hex(hex_id[0])
                ]

                if available_hexes:
                    random_hex = random.choice(available_hexes)
                    await sqllite_helper.create_warehouse(random_hex)
                    logger.info(
                        "Created warehouse in hex %s for alliance %s",
                        random_hex,
                        winner_alliance_id[0],
                    )
                    await sqllite_helper.add_to_story(
                        cell_id,
                        f"Склад создан на гексе {random_hex} альянсом {winner_alliance_id[0]}"
                    )

        elif mission_type == "sabotage":
            warehouses = await sqllite_helper.get_warehouses_of_warmaster(
                loser_telegram_id)
            if warehouses:
                random_warehouse = random.choice(warehouses)
                await sqllite_helper.destroy_warehouse(random_warehouse[0])
                logger.info(
                    "Destroyed warehouse %s belonging to %s",
                    random_warehouse[0],
                    loser_telegram_id,
                )


async def has_route_to_warehouse(cell_id, particpant_telegram):
    if not isinstance(particpant_telegram, str):
        particpant_telegram = particpant_telegram[0]
    alliance = await sqllite_helper.get_alliance_of_warmaster(particpant_telegram)
    # проверка принадлежит ли cell_id игроку
    is_current_hex_patron = await sqllite_helper.is_hex_patroned_by(cell_id, alliance[0])
    if is_current_hex_patron:
        return await sqllite_helper.has_route_to_warehouse(cell_id, particpant_telegram)
    else:
        # получить все соседние hexы и для каждого принадлежащего participant вызвать has_route_to_warhouse, после первого true выйти из цикла
        next_hexes = await sqllite_helper.get_next_hexes_filtered_by_patron(cell_id, particpant_telegram)
        for next_hex in next_hexes:
            current_hex_has_route_to_warhouse = await sqllite_helper.has_route_to_warehouse(next_hex, particpant_telegram)
            if current_hex_has_route_to_warhouse == True:
                return True
        return False