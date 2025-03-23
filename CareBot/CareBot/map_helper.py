import sqllite_helper

def check_patronage(battle_id, battle_result, user_telegram_id):
    # Разделяем результат битвы на два числа
    scores = battle_result.split()
    user_score = int(scores[0])
    opponent_score = int(scores[1])

    # Если ничья, то ничего не делаем
    if user_score == opponent_score:
        return

    # get cell id by battle id
    cell_id = sqllite_helper.get_cell_id_by_battle_id(battle_id)

    # Определяем победителя
    winner_telegram_id = user_telegram_id if user_score > opponent_score else sqllite_helper.get_opponent_telegram_id(battle_id, user_telegram_id)

    # todo: get alliance id of winner
    winner_alliance_id = sqllite_helper.get_alliance_of_warmaster(winener_telegram_id)
    # todo: update db - set up winner id as patron of cell
    sqllite_helper.set_cell_patron(cell_id, winner_alliance_id)