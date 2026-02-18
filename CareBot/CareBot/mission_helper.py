"""Helper functions for managing missions in the game."""

from typing import Optional, Tuple
import random
import logging
import config

# Автоматическое переключение на mock версию в тестовом режиме
if config.TEST_MODE:
    import mock_sqlite_helper as sqllite_helper
    print("🧪 Mission Helper using MOCK SQLite helper")
else:
    import sqllite_helper
    print("✅ Mission Helper using REAL SQLite helper")

import map_helper
import notification_service
from features import feature_registry
import register_features  # Ensure features are registered
from database.killzone_manager import get_killzone_for_mission
from models import Mission, MissionDetails

logger = logging.getLogger(__name__)

# Reinforcement restriction message
REINFORCEMENT_RESTRICTION_MESSAGE = (
    "⚠️ Атакующий игрок не может отправлять юнитов в резервы, "
    "за исключением тех кто имеет правило Deep Strike"
)

# Battlefleet Gothica celestial phenomena generators
BATTLEZONE_GENERATORS = {
    1: {  # Asteroid Field
        1: "Dense Asteroid Cluster - Ships moving through reduce speed by 2\"",
        2: "Asteroid Belt - Provides cover, enemies get -1 to hit",
        3: "Scattered Debris - No effect on movement",
        4: "Mining Operation - Abandoned structures provide partial cover",
        5: "Ice Field - Sensors reduced, -2\" to detection range",
        6: "Metallic Asteroids - Interferes with targeting systems"
    },
    2: {  # Nebula Zone
        1: "Gas Cloud - Reduces weapon range by 6\"",
        2: "Plasma Storm - Random energy discharges, roll for damage each turn",
        3: "Dust Cloud - All ships count as obscured",
        4: "Ion Nebula - Shields reduced by 1",
        5: "Radiation Field - Crew take 1 damage per turn inside",
        6: "Clear Zone - No effect"
    },
    3: {  # Gravity Wells
        1: "Massive Gravity Well - All movement reduced by 3\"",
        2: "Unstable Gravity - Random direction pull each turn",
        3: "Black Hole Proximity - Ships within 12\" pulled 2\" towards center",
        4: "Tidal Forces - Ships take 1 hull damage if moving at full speed",
        5: "Gravitational Anomaly - Unpredictable sensor readings",
        6: "Stable Orbit Zone - +1 to hit for ships not moving"
    },
    4: {  # Solar Phenomena
        1: "Solar Flare - All shields at -2 this turn",
        2: "Radiation Burst - Communications disrupted",
        3: "Electromagnetic Pulse - Ordnance weapons gain +1 strength",
        4: "Corona Discharge - Energy weapons reduced range by 6\"",
        5: "Stellar Wind - All ships pushed 3\" in random direction",
        6: "Magnetic Storm - Torpedoes may veer off course"
    },
    5: {  # Debris Field
        1: "Ship Wreckage - Provides full cover",
        2: "Battle Debris - Hazardous terrain, moving ships roll for damage",
        3: "Ancient Hulk - Can be used as cover or boarded",
        4: "Orbital Wreckage - Scattered debris, no effect",
        5: "Minefield Remnants - Roll D6 when entering, 5+ takes 1 damage",
        6: "Salvage Field - No combat effect"
    },
    6: {  # Planetary Bodies
        1: "Moon - Provides cover and gravity well",
        2: "Small Planet - Can use for slingshot maneuvers",
        3: "Gas Giant - Obscures sensors within 6\"",
        4: "Planetary Ring - Counts as asteroid field",
        5: "Barren Rock - Blocks line of sight",
        6: "Space Station - Neutral fortification"
    }
}


def _parse_reward_config(reward_config):
    """Return normalized reward entries from mission reward_config text."""
    rewards = {}
    if not reward_config:
        return rewards
    normalized = reward_config.replace("\n", ";")
    for part in normalized.split(";"):
        if ":" not in part:
            continue
        key, value = part.split(":", 1)
        key = key.strip().upper()
        try:
            amount = int(value.strip())
        except (TypeError, ValueError):
            continue
        rewards[key] = amount
    return rewards


def generate_battlefleet_map():
    """Generate celestial phenomena map for Battlefleet Gothica missions.
    
    Based on Setting Up Celestial Phenomena: Method 2
    Divides table into 60cm square areas and generates phenomena.
    
    Returns:
        str: Formatted map description with celestial phenomena
    """
    # Standard table is typically 120cm x 180cm, giving us 2x3 = 6 areas of 60cm each
    # We'll use a simpler 2x3 grid (6 areas total)
    areas = []
    
    # First, determine which battlezone generator to use (D6 roll)
    generator_type = random.randint(1, 6)
    generator_name = {
        1: "Asteroid Field",
        2: "Nebula Zone", 
        3: "Gravity Wells",
        4: "Solar Phenomena",
        5: "Debris Field",
        6: "Planetary Bodies"
    }[generator_type]
    
    selected_generator = BATTLEZONE_GENERATORS[generator_type]
    
    # Check each area (6 total in 2x3 grid)
    area_labels = [
        "Top-Left", "Top-Center", "Top-Right",
        "Bottom-Left", "Bottom-Center", "Bottom-Right"
    ]
    
    for label in area_labels:
        # Roll D6 for each area - on 4+ it contains phenomena
        roll = random.randint(1, 6)
        if roll >= 4:
            # Generate phenomena from the selected generator
            phenomena_roll = random.randint(1, 6)
            phenomena = selected_generator[phenomena_roll]
            areas.append(f"  • {label}: {phenomena}")
        else:
            areas.append(f"  • {label}: Empty space")
    
    # Build the final map description
    map_desc = f"🗺️ BATTLEFLEET MAP - {generator_name.upper()}\n\n"
    map_desc += "Celestial Phenomena (60cm grid areas):\n"
    map_desc += "\n".join(areas)
    map_desc += "\n\n📋 Note: Position phenomena anywhere within each area, but don't overlap them."
    
    return map_desc



def generate_new_one(rules):
    """Generates a new mission based on the provided ruleset."""
    # Base mission types and objectives for different rule sets
    if rules == "killteam":
        # 9 основных миссий Kill Team
        missions = [
            "Secure: Operatives must secure and hold key objectives",
            "Loot: Operatives must retrieve valuable resources",
            "Transmission: Operatives must transmit data",
            "Upload: Operatives must upload critical intelligence",
            "Intel: Operatives must gather intelligence from enemy positions",
            "Extraction: Operatives must extract valuable assets",
            "Sabotage: Operatives must sabotage",
            "Power Surge: Operatives must disrupt enemy power systems",
            "Coordinates: Operatives must destroy enemy warehouse"
        ]

        mission_name = random.choice(missions).split(":")[0]
        description = random.choice(missions)

        # cell should be None when generating, assigned later when mission is selected
        return (mission_name, rules, None, description, None, None)

    elif rules == "boarding_action":
        deploy_types = ["Breach Points", "Ship Interface", "Void Strike"]
        missions = [
            "Void Assault", "Engine Sabotage", "Bridge Takeover",
            "Datacore Theft", "Life Support Sabotage", "Vessel Capture"
        ]
        actions = ['secure critical ship systems', 'eliminate enemy crew',
                   'download ship schematics',
                   'establish control of key areas']
        description = (f"{random.choice(missions)}: Forces must "
                       f"{random.choice(actions)}")
        deploy = random.choice(deploy_types)
        # Return tuple with cell=None, no winner_bonus, no map_description for boarding_action
        return (deploy, rules, None, description, None, None)

    elif rules == "combat_patrol":
        deploy_types = ["Strategic Reserves",
                        "Tactical Deployment", "Flanking Maneuvers"]
        missions = [
            "Forward Assault", "Strategic Seizure", "Patrol Encounter",
            "Hold Ground", "Supply Line Disruption", "Priority Target"
        ]
        actions = ['secure and hold territory',
                   'eliminate enemy patrols',
                   'establish forward operating base',
                   'capture strategic assets'
                   ]
        description = (f"{random.choice(missions)}: Patrol forces must "
                       f"{random.choice(actions)}")
        deploy = random.choice(deploy_types)
        # Return tuple with cell=None, no winner_bonus, no map_description for consistency
        return (deploy, rules, None, description, None, None)

    elif rules == "wh40k":
        deploy_types = ["Total Domination", "Braze Bridge"]
        missions = [
            'Начиная со второго раунда битвы, в конце фазы командования каждого игрока, игрок, чей ход сейчас, получает ПО следующим образом: За каждый контролируемый ими маркер цели на нейтральной полосе они получают 5 ПО. Если они контролируют маркер цели в зоне развертывания противника, они получают 10 ПО. В пятом раунде битвы игрок, у которого второй ход, получает ПО, как описано выше, но делает это в конце хода, а не в конце своей фазы командования. Каждый игрок может получить максимум 90 ПО за выполнение этой цели миссии.',
            'Игрок получает 10 чоков в конце своего хода, если выполняется одно из двух условий: 1) Хотя бы один юнит игрока находится в Ничейной земле, в Ничейной земле нет юнитов оппонента; 2) Игрок имеет хотя бы один юнит в зоне Атакера, Ничейной земле и зоне Дефендера. В конце игры, Дефендер получает 20 очков если держит точку в своей деплойке. Атакер получает 40 очков если держит точку в деплойке оппонента. Если никто не держит точку в деплойке дефендера, то атакер получает 20 очков'
        ]
        winner_bonuses = [
            "Выбрать один юнит участвующий в битве. Этот юнит получает 3xp вместо 1xp за участие в битве.",
            "Победитель может выбрать юнит находящийся на точке вефендера и выдать ему любой доступный Battle Trait"
        ]
        description = random.choice(missions)
        deploy = random.choice(deploy_types)
        winner_bonus = random.choice(winner_bonuses)
        # Return tuple with cell=None, winner_bonus included, no map_description for wh40k
        return (deploy, rules, None, description, winner_bonus, None)

    elif rules == "battlefleet":
        deploy_types = ["Convoy Pattern", "Battle Line", "Orbital Superiority"]
        missions = [
            "Fleet Engagement", "Convoy Protection", "Planetary Bombardment",
            "Naval Blockade", "Ship Hunter", "Defense Platform Assault"
        ]
        actions = [
            'destroy enemy vessels',
            'protect supply ships',
            'establish orbital dominance',
            'disable enemy stations'
        ]
        description = (f"{random.choice(missions)}: Fleet must "
                       f"{random.choice(actions)}")
        deploy = random.choice(deploy_types)
        # Generate celestial phenomena map
        map_description = generate_battlefleet_map()
        # Return tuple with cell=None, no winner_bonus, but with map_description for battlefleet
        return (deploy, rules, None, description, None, map_description)

    else:
        # Default case if rules type is not recognized
        # Return tuple with cell=None, no winner_bonus, no map_description for consistency
        return ('Only War', rules, None, f'Generic mission for {rules}', None, None)


async def get_mission(rules: Optional[str], attacker_id: Optional[str] = None, defender_id: Optional[str] = None):
    """Fetches an existing mission or generates a new one if none exists.
    
    Args:
        rules: Mission ruleset (killteam, wh40k, etc.)
        attacker_id: Telegram ID of the attacker (who clicked the mission)
        defender_id: Telegram ID of the defender (opponent)
    
    Returns:
        Tuple with mission data for display (backwards compatible format)
    
    Battle cell is determined by finding hexes adjacent to attacker's territory 
    that belong to defender and randomly selecting one of them.
    """
    # Get mission from database (returns Mission object or None)
    mission = await sqllite_helper.get_mission(rules)
    
    if not mission:
        # Generate new mission (returns tuple)
        mission_tuple = generate_new_one(rules)
        await sqllite_helper.save_mission(mission_tuple)
        # Re-fetch from DB to get Mission object with ID
        mission = await sqllite_helper.get_mission(rules)
        
    if not mission:
        raise ValueError(f"Failed to get or create mission for rules: {rules}")
    
    # Determine cell_id based on participants
    cell_id = mission.cell
    
    if attacker_id and defender_id and cell_id is None:
        attacker_alliance = await sqllite_helper.get_alliance_of_warmaster(attacker_id)
        defender_alliance = await sqllite_helper.get_alliance_of_warmaster(defender_id)
        
        if attacker_alliance and defender_alliance:
            attacker_alliance_id = attacker_alliance[0]
            defender_alliance_id = defender_alliance[0]
            
            # Find hexes of defender that are adjacent to hexes of attacker
            adjacent_defender_hexes = await sqllite_helper.get_adjacent_hexes_between_alliances(
                attacker_alliance_id, defender_alliance_id
            )
            
            # Convert iterator to list if needed
            adjacent_hexes_list = list(adjacent_defender_hexes) if adjacent_defender_hexes else []
            if adjacent_hexes_list:
                # Randomly select one adjacent hex from defender's territory
                cell_id = random.choice(adjacent_hexes_list)[0]
                logger.info(
                    f"Battle cell determined: {cell_id} "
                    f"(random hex from defender's territory adjacent to attacker)"
                )
            else:
                # Fallback: no adjacent hexes, use random defender hex
                defender_hexes = await sqllite_helper.get_hexes_by_alliance(defender_alliance_id)
                defender_hexes_list = list(defender_hexes) if defender_hexes else []
                if defender_hexes_list:
                    cell_id = random.choice(defender_hexes_list)[0]
                    logger.info(
                        f"Battle cell determined: {cell_id} "
                        f"(random defender hex, no adjacent hexes found)"
                    )
                else:
                    logger.warning(
                        f"No hexes found for defender alliance {defender_alliance_id}"
                    )
        
        # Update mission with determined cell_id
        if cell_id is not None:
            await sqllite_helper.update_mission_cell(mission.id, cell_id)
            mission.cell = cell_id  # Update local object

    # Call feature hooks after cell is determined
    if cell_id is not None:
        mission_data = {
            'mission_id': mission.id,
            'rules': rules,
            'cell': cell_id,
            'description': mission.mission_description,
            'attacker_id': attacker_id,
            'defender_id': defender_id
        }
        await feature_registry.on_create_mission(mission_data)
        # Re-fetch mission to get updated description
        mission = await sqllite_helper.get_mission_details(mission.id)

    if rules == "killteam":
        if cell_id is not None:
            state = await sqllite_helper.get_state(cell_id)

            # Получаем killzone для данного state гекса (или None)
            hex_state = state[0] if state is not None else None
            killzone = get_killzone_for_mission(hex_state)

            # Build result tuple with extra info
            result = mission.to_tuple() + (f"Killzone: {killzone}",)

            if state is not None:
                result = result + (state[0],)

            history = await sqllite_helper.get_cell_history(cell_id)
            for point in history:
                result = result + tuple(point)  # Convert Row to tuple

            return result
        else:
            # For killteam without cell, return mission tuple
            return mission.to_tuple()

    elif rules == "wh40k":
        # Return mission info without locking
        if cell_id is not None:
            # If cell is assigned, add extra info
            number_of_safe_next_cells = await sqllite_helper.get_number_of_safe_next_cells(cell_id)
            result = mission.to_tuple() + (f"Бой на {(number_of_safe_next_cells + 1) * 500} pts",)
            history = await sqllite_helper.get_cell_history(cell_id)
            state = await sqllite_helper.get_state(cell_id)
            if state is not None:
                result = result + (state[0],)

            for point in history:
                result = result + tuple(point)  # Convert Row to tuple
            
            return result
        else:
            return mission.to_tuple()
    
    elif rules == "battlefleet":
        # Lock mission and include map description
        await sqllite_helper.lock_mission(mission.id)
        result = mission.to_tuple()
        # Add map description if available
        if mission.map_description:
            result = result + (mission.map_description,)
        return result

    return mission.to_tuple()

async def check_attacker_reinforcement_status(battle_id, attacker_id):
    """
    Checks if the attacker has adjacent cells to the mission cell.
    If not, returns a message about reinforcement restriction.
    
    Args:
        battle_id: Battle ID
        attacker_id: Telegram ID of the attacker
        
    Returns:
        str or None: Reinforcement restriction message if applicable, None otherwise
    """
    cell_id = await sqllite_helper.get_cell_id_by_battle_id(battle_id)
    
    # Get attacker's alliance
    attacker_alliance = await sqllite_helper.get_alliance_of_warmaster(attacker_id)
    if not attacker_alliance:
        return None
    
    attacker_alliance_id = attacker_alliance[0]
    
    if not cell_id:
        return REINFORCEMENT_RESTRICTION_MESSAGE
    
    # Check if attacker has any adjacent cell to the mission cell
    has_adjacent = await sqllite_helper.has_adjacent_cell_to_hex(
        attacker_alliance_id, cell_id
    )
    
    if not has_adjacent:
        return REINFORCEMENT_RESTRICTION_MESSAGE
    
    return None


async def get_situation(battle_id, telegram_ids):
    """
    Checks if participants have a route to a warehouse and their situation.
    """
    cell_id = await sqllite_helper.get_cell_id_by_battle_id(battle_id)
    result = []

    for particpant_telegram in telegram_ids:
        # Extract telegram_id from tuple (telegram_ids is list of tuples like [('123456',), ('789012',)])
        telegram_id = particpant_telegram[0] if isinstance(particpant_telegram, tuple) else particpant_telegram
        has_route_to_warehouse = await map_helper.has_route_to_warehouse(
            cell_id, telegram_id)
        if has_route_to_warehouse is False:
            nickname = await sqllite_helper.get_nicknamane(telegram_id)
            display_name = nickname or str(telegram_id)
            result.append(
                f"{display_name} не получает CP. Вместо этого "
                f"использует колоду со страгеммами.")

    return result


async def write_battle_result(battle_id, user_reply):
    """Writes the battle result to the database."""
    counts = user_reply.split(' ')
    # Get the mission_id from the battle record
    mission_id = await sqllite_helper.get_mission_id_for_battle(battle_id)
    if not mission_id:
        logger.error(f"Could not find mission_id for battle {battle_id}")
        raise ValueError(f"Battle {battle_id} not found or has no mission_id")
    
    await sqllite_helper.get_rules_of_mission(mission_id)
    await sqllite_helper.add_battle_result(
        mission_id, counts[0], counts[1])


async def apply_mission_rewards(battle_id, user_reply, user_telegram_id):
    """
    Apply rewards or penalties based on mission type and battle results.

    Args:
        battle_id: The ID of the battle
        user_reply: The battle result string like "15 10" 
            (user_score opponent_score)
        user_telegram_id: Telegram ID of the user who submitted the result
    """
    logger.info(
        "=== START apply_mission_rewards: battle_id=%s, user=%s, "
        "scores=%s ===",
        battle_id, user_telegram_id, user_reply)
    
    counts = user_reply.split(' ')
    user_score = int(counts[0])
    opponent_score = int(counts[1])
    logger.info("Parsed scores: user=%s, opponent=%s", user_score, opponent_score)

    # Get opponent's telegram ID
    opponent_telegram_id = await sqllite_helper.get_opponent_telegram_id(
        battle_id, user_telegram_id)
    logger.info(
        "get_opponent_telegram_id returned: %s (type: %s)",
        opponent_telegram_id, type(opponent_telegram_id))
    
    if isinstance(opponent_telegram_id, tuple):
        opponent_telegram_id = opponent_telegram_id[0]
        logger.info("Extracted opponent_telegram_id from tuple: %s",
                    opponent_telegram_id)
    
    # Ensure IDs are strings for database consistency
    user_telegram_id = str(user_telegram_id)
    opponent_telegram_id = str(opponent_telegram_id)

    # Get the mission details
    mission_id = await sqllite_helper.get_mission_id_by_battle_id(battle_id)
    logger.info("mission_id for battle: %s", mission_id)
    
    mission_details = await sqllite_helper.get_mission_details(mission_id)
    logger.info("mission_details: %s", mission_details)

    if not mission_details:
        logger.error("Could not find mission details for battle %s", battle_id)
        return

    # Extract mission type and rules from Mission object
    mission_type = mission_details.deploy  # Mission name/type
    rules = mission_details.rules
    logger.info("Mission type: %s, rules: %s", mission_type, rules)

    # Get alliance IDs for both players 
    # (IDs are already converted to strings above)
    # Get alliance IDs for both players
    logger.info("Fetching alliance for user: %s", user_telegram_id)
    user_alliance_id = await sqllite_helper.get_alliance_of_warmaster(
        user_telegram_id)
    logger.info(
        "get_alliance_of_warmaster(user) returned: %s (type: %s)",
        user_alliance_id, type(user_alliance_id))
    
    logger.info("Fetching alliance for opponent: %s", opponent_telegram_id)
    opponent_alliance_id = await sqllite_helper.get_alliance_of_warmaster(
        opponent_telegram_id)
    logger.info(
        "get_alliance_of_warmaster(opponent) returned: %s (type: %s)",
        opponent_alliance_id, type(opponent_alliance_id))

    # Validate alliance data
    if not user_alliance_id:
        logger.error(
            "Could not find alliance for user %s in battle %s",
            user_telegram_id, battle_id)
        return
    
    if not opponent_alliance_id:
        logger.error(
            "Could not find alliance for opponent %s in battle %s",
            opponent_telegram_id, battle_id)
        return

    # Extract alliance IDs from tuples
    user_alliance = user_alliance_id[0]
    opponent_alliance = opponent_alliance_id[0]
    logger.info(
        "Extracted alliances: user=%s, opponent=%s",
        user_alliance, opponent_alliance)

    # Check if players have valid alliances (not 0)
    if user_alliance == 0:
        logger.warning(
            "User %s has no alliance (alliance=0) in battle %s",
            user_telegram_id, battle_id)
    
    if opponent_alliance == 0:
        logger.warning(
            "Opponent %s has no alliance (alliance=0) in battle %s",
            opponent_telegram_id, battle_id)

    # Base resource gain for participating alliances
    participant_alliances = []
    if user_alliance not in (None, 0):
        participant_alliances.append(user_alliance)
    if opponent_alliance not in (None, 0):
        participant_alliances.append(opponent_alliance)

    # Determine winner
    logger.info("Determining winner...")
    if user_score > opponent_score:
        winner_alliance_id = (user_alliance
                              if user_alliance != 0 else None)
        loser_alliance_id = (opponent_alliance
                             if opponent_alliance != 0 else None)
        winner_score = user_score
        loser_score = opponent_score
        logger.info(
            "User won: winner_alliance=%s, loser_alliance=%s",
            winner_alliance_id, loser_alliance_id)
    elif opponent_score > user_score:
        winner_alliance_id = (opponent_alliance
                              if opponent_alliance != 0 else None)
        loser_alliance_id = (user_alliance
                             if user_alliance != 0 else None)
        winner_score = opponent_score
        loser_score = user_score
        logger.info(
            "Opponent won: winner_alliance=%s, loser_alliance=%s",
            winner_alliance_id, loser_alliance_id)
    else:
        # Draw - no clear winner
        winner_alliance_id = None
        loser_alliance_id = None
        winner_score = user_score
        loser_score = opponent_score
        logger.info("Draw - no winner")

    # Prepare battle data for features
    battle_data = {
        'battle_id': battle_id,
        'mission_id': mission_id,
        'user_score': user_score,
        'opponent_score': opponent_score,
        'user_alliance': user_alliance,
        'opponent_alliance': opponent_alliance,
        'winner_alliance_id': winner_alliance_id,
        'loser_alliance_id': loser_alliance_id,
        'winner_score': winner_score,
        'loser_score': loser_score,
        'mission_type': mission_type,
        'rules': rules,
        'reward_config': getattr(mission_details, "reward_config", None)
    }
    
    # Call feature lifecycle method for all enabled features
    await feature_registry.on_result_approved(battle_data)
    
    # Process non-resource mission-specific logic
    if rules == "killteam":
        if mission_type.lower() == "intel":
            # Creates warehouse in the hex where the mission took place
            if winner_alliance_id:
                cell_id = await sqllite_helper.get_cell_id_by_battle_id(battle_id)
                await sqllite_helper.create_warehouse(cell_id)
                logger.info("Intel mission: Warehouse created in hex %s", cell_id)
        
        elif mission_type.lower() == "sabotage":
            # No resource changes for sabotage missions
            logger.info("Sabotage mission: No resource changes")

    # Check if loser alliance has any hexes remaining after battle
    logger.info("Checking for alliance elimination...")
    if loser_alliance_id:
        logger.info(
            "Checking hexes for loser alliance: %s", loser_alliance_id)
        remaining_hexes = await sqllite_helper.get_hexes_by_alliance(
            loser_alliance_id)
        # Convert iterator to list to get length
        remaining_hexes_list = list(remaining_hexes) if remaining_hexes else []
        logger.info(
            "Alliance %s has %s hexes remaining",
            loser_alliance_id, len(remaining_hexes_list))
        if len(remaining_hexes_list) == 0:
            logger.info(
                "Alliance %s eliminated - no hexes remaining",
                loser_alliance_id)
            await handle_alliance_elimination(loser_alliance_id)
    else:
        logger.info("No loser alliance to check (draw or alliance=0)")

    if rules == "wh40k":
        # Process 40k missions - apply winner bonuses from database
        if winner_alliance_id:
            # Get winner bonus from database (secret until now)
            winner_bonus = await sqllite_helper.get_winner_bonus(mission_id)
            
            # Возвращаем информацию о бонусе победителя для сообщения
            return {
                "battle_id": battle_id,
                "mission_type": mission_type,
                "rules": rules,
                "winner_alliance_id": winner_alliance_id,
                "winner_bonus": winner_bonus,
                "rewards_applied": True
            }

    # Return the summary of rewards for potential messaging to users
    logger.info(
        "=== END apply_mission_rewards: battle_id=%s, "
        "winner=%s ===", battle_id, winner_alliance_id)
    return {
        "battle_id": battle_id,
        "mission_type": mission_type,
        "rules": rules,
        "winner_alliance_id": winner_alliance_id,
        "rewards_applied": True
    }


async def handle_alliance_elimination(eliminated_alliance_id, context=None):
    """Handle alliance elimination by redistributing resources as missions."""
    logger.info("Processing elimination of alliance %s", eliminated_alliance_id)
    
    # Get eliminated alliance resources
    alliance_resources = await sqllite_helper.get_alliance_resources(
        eliminated_alliance_id)
    
    # Get count of remaining active alliances (excluding the eliminated one)
    active_alliances_count = await sqllite_helper.get_active_alliances_count()
    remaining_alliances = active_alliances_count - 1
    
    total_missions = 0
    if remaining_alliances > 0 and alliance_resources > 0:
        # Calculate missions to create (integer division, remainder ignored)
        missions_per_alliance = alliance_resources // remaining_alliances
        total_missions = missions_per_alliance * remaining_alliances
        
        logger.info(
            "Creating %s resource collection missions "
            "from %s resources", total_missions, alliance_resources)
        
        # Create resource collection missions
        for i in range(total_missions):
            mission_data = (
                "Resource Collection",  # deploy
                "resource_collection",  # rules
                None,  # cell (NULL)
                "Collect resources from eliminated alliance reserves.",
                None,  # winner_bonus
                None,  # map_description
            )
            await sqllite_helper.save_mission(mission_data)
    
    # Send notifications if context is provided
    if context:
        await notification_service.notify_alliance_elimination(
            context, eliminated_alliance_id)
    
    # Clear alliance members and delete alliance
    await sqllite_helper.clear_alliance_members(eliminated_alliance_id)
    await sqllite_helper.delete_alliance(eliminated_alliance_id)
    
    logger.info("Alliance %s eliminated and cleaned up", eliminated_alliance_id)


async def start_battle(mission_id, player1_id, player2_id):
    """Starts a new battle for the given mission with exactly 2 players.
    
    Args:
        mission_id: The mission ID
        player1_id: First player telegram ID (will be fstplayer)
        player2_id: Second player telegram ID (will be sndplayer)
    
    Returns:
        int: Battle ID
    
    Raises:
        ValueError: If player IDs are missing or invalid
    """
    if not player1_id or not player2_id:
        raise ValueError(
            f"start_battle requires exactly 2 players. "
            f"Got player1={player1_id}, player2={player2_id}"
        )
    
    # Create battle without scores
    battle_id_result = await sqllite_helper.add_battle(mission_id)
    
    if not battle_id_result:
        raise RuntimeError(f"Failed to create battle for mission {mission_id}")
    
    battle_id = battle_id_result[0]
    
    # Add exactly 2 players in order: first player is fstplayer, second is sndplayer
    await sqllite_helper.add_battle_participant(
        battle_id,
        player1_id
    )
    await sqllite_helper.add_battle_participant(
        battle_id,
        player2_id
    )
    
    logger.info(
        f"Battle {battle_id} created for mission {mission_id} with "
        f"fstplayer={player1_id}, sndplayer={player2_id}"
    )
    
    return battle_id
