import array
from sqlite3 import sqlite_version
from typing import Optional
import sqllite_helper
import map_helper
import random

def generate_new_one(rules):
    # Base mission types and objectives for different rule sets
    if rules == "killteam":
        deploy_types = ["Breach", "Sabotage", "Escape"]
        missions = [
            "Recon Sweep", "Data Recovery", "Assassination", 
            "Asset Denial", "Supply Drop", "Scan and Locate"
        ]
        description = f"{random.choice(missions)}: Operatives must {random.choice(['secure objectives', 'eliminate targets', 'retrieve intelligence', 'establish control points'])}"
        
    elif rules == "boarding_action":
        deploy_types = ["Breach Points", "Ship Interface", "Void Strike"]
        missions = [
            "Void Assault", "Engine Sabotage", "Bridge Takeover", 
            "Datacore Theft", "Life Support Sabotage", "Vessel Capture"
        ]
        description = f"{random.choice(missions)}: Forces must {random.choice(['secure critical ship systems', 'eliminate enemy crew', 'download ship schematics', 'establish control of key areas'])}"
        
    elif rules == "combat_patrol":
        deploy_types = ["Strategic Reserves", "Tactical Deployment", "Flanking Maneuvers"]
        missions = [
            "Forward Assault", "Strategic Seizure", "Patrol Encounter", 
            "Hold Ground", "Supply Line Disruption", "Priority Target"
        ]
        description = f"{random.choice(missions)}: Patrol forces must {random.choice(['secure and hold territory', 'eliminate enemy patrols', 'establish forward operating base', 'capture strategic assets'])}"
        
    elif rules == "wh40k":
        deploy_types = ["Dawn of War", "Hammer and Anvil", "Search and Destroy"]
        missions = [
            "No Mercy", "Vital Intelligence", "The Relic", 
            "Scorched Earth", "Retrieval Mission", "Cleanse and Capture"
        ]
        description = f"{random.choice(missions)}: Armies must {random.choice(['secure critical objectives', 'destroy enemy forces', 'hold strategic positions', 'capture enemy intelligence'])}"
        
    elif rules == "battlefleet":
        deploy_types = ["Convoy Pattern", "Battle Line", "Orbital Superiority"]
        missions = [
            "Fleet Engagement", "Convoy Protection", "Planetary Bombardment", 
            "Naval Blockade", "Ship Hunter", "Defense Platform Assault"
        ]
        description = f"{random.choice(missions)}: Fleet must {random.choice(['destroy enemy vessels', 'protect supply ships', 'establish orbital dominance', 'disable enemy stations'])}"
        
    else:
        # Default case if rules type is not recognized
        return ('Only War', rules, 2, f'Generic mission for {rules}')
    
    # Generate the mission tuple
    deploy = random.choice(deploy_types)
    return (deploy, rules, 2, description)

async def get_mission(rules: Optional[str]):
    mission = await sqllite_helper.get_mission(rules)
    
    if not mission:
        # Если миссия не найдена, генерируем новую
        mission = generate_new_one(rules)
        await sqllite_helper.save_mission(mission)

    if "rules" == "wh40k":
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

async def write_battle_result(battle_id, user_reply, scenario: Optional[str]):
    counts = user_reply.split(' ')
    rules = await sqllite_helper.get_rules_of_mission(battle_id)
    await sqllite_helper.add_battle_result(int(battle_id), counts[0], counts[1])

async def start_battle(mission_id, participants):
    battle_id = await sqllite_helper.add_battle(mission_id)
    for participant in participants:
        await sqllite_helper.add_battle_participant(battle_id[0], participant[0])
    return battle_id[0]
