import sqllite_helper
import random
import re

def generate_new_one():
    return (None, 'Side by Side', 'Onlu War', 2, 'Onlu War')

async def get_mission(schedule_string, telegramid):
    rules = sqllite_helper.get_rules_by_schedule(int(re.search(r"sch_(\d+)", schedule_string).group(1)))[0]
    if rules[0] in ["wh40k", "boardingaction", "combatpatrol"]:
        one_warmaster = sqllite_helper.get_warmasterid_bytelegramid(
            int(*sqllite_helper.get_warmasterid_ofshedule(int(re.search(r"sch_(\d+)", schedule_string).group(1))))
        )
        another_warmaster = sqllite_helper.get_warmasterid_bytelegramid(telegramid)

        mission = await sqllite_helper.get_mission()
    
        if not mission:
            # Если миссия не найдена, генерируем новую
            mission = generate_new_one()
        else:    
            sqllite_helper.lock_mission(mission[4])

        # сначала случайным образом выбрать кто на кого нападат
        if random.choice([True, False]):
            attacker = one_warmaster
            defender = another_warmaster
        else:
            attacker = another_warmaster
            defender = one_warmaster

        mission_aslist = list(mission)
        mission_aslist[3] = f'{mission_aslist[3]} \n Атакер: {sqllite_helper.get_warmastername_by_id(*attacker)[0]} \n Дефендр: {sqllite_helper.get_warmastername_by_id(*defender)[0]}'
        # попытаться найти возззможную территорию на линии соприкосновения
        hexagons = sqllite_helper.get_hexs_on_frontline(*attacker, *defender)
        
        # если нет линии соприкосновния то случайная трритория защищающгоя
        if not hexagons:
            hexagons = sqllite_helper.get_hex_behind_frontline(*attacker, *defender)

        if mission[0]:
            sqllite_helper.mission_assert_hex(mission[0], random.choice(hexagons))

        return mission_aslist
    
    return None

async def write_battle_result(battle_id, user_reply):
    counts = user_reply.split(' ')
    bid = battle_id[1:]
    await sqllite_helper.add_battle_result(int(bid), counts[0], counts[1])
