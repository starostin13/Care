import sqllite_helper
import random

def generate_new_one():
    return ('Side by Side', 'Onlu War', 2, 'Onlu War')

async def get_mission(one_warmaster, another_warmaster):
    mission = await sqllite_helper.get_mission()
    
    if not mission:
        # ���� ������ �� �������, ���������� �����
        mission = generate_new_one()
    else:    
        sqllite_helper.lock_mission(mission[4])

    # ������� ��������� ������� ������� ��� �� ���� �������
    if random.choice([True, False]):
        attacker = one_warmaster
        defender = another_warmaster
    else:
        attacker = another_warmaster
        defender = one_warmaster

    mission[4] = f'{mission[4]} \n ������: {attacker} \n �������: {defender}'
    # ���������� ����� ����������� ���������� �� ����� ���������������
    # ���� ��� ����� �������������� �� ��������� ��������� �����������
    
    return mission

async def write_battle_result(battle_id, user_reply):
    counts = user_reply.split(' ')
    bid = battle_id[1:]
    await sqllite_helper.add_battle_result(int(bid), counts[0], counts[1])
