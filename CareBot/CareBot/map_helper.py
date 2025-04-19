#!/usr/bin/env python
# -*- coding: utf-8 -*-
# vim:fileencoding=utf-8
from ast import Tuple
import sqllite_helper
import logging

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
# set higher logging level for httpx to avoid all GET and POST requests being logged
logging.getLogger("httpx").setLevel(logging.WARNING)

logger = logging.getLogger(__name__)

async def check_patronage(battle_id, battle_result, user_telegram_id):
    # Разделяем результат битвы на два числа
    scores = battle_result.split()
    user_score = int(scores[0])
    opponent_score = int(scores[1])

    # Если ничья, то ничего не делаем
    if user_score == opponent_score:
        logger("Draw in battle")
        return

    # Получаем cell id по battle id
    cell_id = await sqllite_helper.get_cell_id_by_battle_id(battle_id)
    logger.info(f"Cell id: {cell_id}")

    # Определяем победителя
    if user_score > opponent_score:
        winner_telegram_id = user_telegram_id
    else:
        winner_telegram_id = await sqllite_helper.get_opponent_telegram_id(battle_id, user_telegram_id)
    logger.info(f"Winner: {winner_telegram_id}")

    if isinstance(winner_telegram_id, tuple):
        winner_telegram_id = winner_telegram_id[0]

    # Получаем alliance id победителя
    winner_alliance_id = await sqllite_helper.get_alliance_of_warmaster(winner_telegram_id)
    logger.info(f"Winner alliance id: {winner_alliance_id}")

    # Обновляем базу данных - устанавливаем победителя как патрона клетки
    await sqllite_helper.set_cell_patron(cell_id, winner_alliance_id[0])

    new_patron_faction = await sqllite_helper.get_faction_of_warmaster(winner_telegram_id)
    await sqllite_helper.add_to_story(cell_id, f"Находилась под контролем {new_patron_faction[0]}")