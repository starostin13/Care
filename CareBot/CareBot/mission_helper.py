import array
from sqlite3 import sqlite_version
import sqllite_helper
import map_helper

def generate_new_one():
    return ('Onlu War', 'Onlu War', 2, 'Onlu War')

async def get_mission():
    mission = await sqllite_helper.get_mission()
    
    if not mission:
        # Если миссия не найдена, генерируем новую
        mission = generate_new_one()
        await sqllite_helper.save_mission(mission)
    
    cell_id = mission[2]
    sqllite_helper.lock_mission(cell_id)
    number_of_safe_next_cells = await sqllite_helper.get_number_of_safe_next_cells(cell_id)
    mission = mission + (f"Бой на {(number_of_safe_next_cells + 1) * 500} pts",)
    history = await sqllite_helper.get_cell_histrory(cell_id)
    state = await sqllite_helper.get_state(cell_id)
    if state is not None:
        mission = mission + (state[0])
    
    for point in history:
        mission = mission + point

    return mission

async def get_situation(battle_id, telegram_ids):
    cell_id = await sqllite_helper.get_cell_id_by_battle_id(battle_id)
    result = []
    
    for particpant_telegram in telegram_ids:
        has_route_to_warehouse = await map_helper.has_route_to_warehouse(cell_id, particpant_telegram)
        if(has_route_to_warehouse is False):
            result.append(f"{particpant_telegram} не получает CP. Вместо этого использует колоду со страгеммами.")

    return result

async def write_battle_result(battle_id, user_reply):
    counts = user_reply.split(' ')
    await sqllite_helper.add_battle_result(int(battle_id), counts[0], counts[1])

async def start_battle(mission_id, participants):
    battle_id = await sqllite_helper.add_battle(mission_id)
    for participant in participants:
        await sqllite_helper.add_battle_participant(battle_id[0], participant[0])
    return battle_id[0]
