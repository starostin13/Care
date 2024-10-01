import sqllite_helper

def generate_new_one():
    return ('Onlu War', 'Onlu War', 2, 'Onlu War')

async def get_mission():
    mission = await sqllite_helper.get_mission()
    
    if not mission:
        # ≈сли мисси€ не найдена, генерируем новую
        mission = generate_new_one()
    
    sqllite_helper.lock_mission(mission[4])
    
    return mission
