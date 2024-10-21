import sqllite_helper

def generate_new_one():
    return ('Onlu War', 'Onlu War', 2, 'Onlu War')

async def get_mission():
    mission = await sqllite_helper.get_mission()
    
    if not mission:
        # ≈сли мисси€ не найдена, генерируем новую
        mission = generate_new_one()
    else:    
        sqllite_helper.lock_mission(mission[4])
    
    return mission

async def write_battle_result(battle_id, user_reply):
    counts = user_reply.split(' ')
    bid = battle_id[1:]
    await sqllite_helper.add_battle_result(int(bid), counts[0], counts[1])
