"""Helper functions for managing missions in the game."""

from typing import Optional
import random
import logging
import sqllite_helper
import map_helper
import notification_service
from database.killzone_manager import get_killzone_for_mission

logger = logging.getLogger(__name__)


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

        return (mission_name, rules, 2, description, None)

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
        return (deploy, rules, 2, description)

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
        return (deploy, rules, 2, description, None)

    elif rules == "wh40k":
        deploy_types = ["Total Domination"]
        missions = [
            'Начиная со второго раунда битвы, в конце фазы командования каждого игрока, игрок, чей ход сейчас, получает ПО следующим образом: За каждый контролируемый ими маркер цели на нейтральной полосе они получают 5 ПО. Если они контролируют маркер цели в зоне развертывания противника, они получают 10 ПО. В пятом раунде битвы игрок, у которого второй ход, получает ПО, как описано выше, но делает это в конце хода, а не в конце своей фазы командования. Каждый игрок может получить максимум 90 ПО за выполнение этой цели миссии.'
        ]
        winner_bonuses = [
            "Выбрать один юнит участвующий в битве. Этот юнит получает 3xp вместо 1xp за участие в битве.",
        ]
        description = random.choice(missions)
        deploy = random.choice(deploy_types)
        winner_bonus = random.choice(winner_bonuses)
        return (deploy, rules, 2, description, winner_bonus)

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
        return (deploy, rules, 2, description)

    else:
        # Default case if rules type is not recognized
        return ('Only War', rules, 2, f'Generic mission for {rules}', None)


async def get_mission(rules: Optional[str]):
    """Fetches an existing mission or generates a new one if none exists."""
    mission = await sqllite_helper.get_mission(rules)

    if not mission:
        # Если миссия не найдена, генерируем новую
        mission = generate_new_one(rules)
        await sqllite_helper.save_mission(mission)

    if rules == "killteam":
        cell_id = mission[2]
        await sqllite_helper.lock_mission(cell_id)
        state = await sqllite_helper.get_state(cell_id)

        # Получаем killzone для данного state гекса (или None)
        hex_state = state[0] if state is not None else None
        killzone = get_killzone_for_mission(hex_state)
        mission = mission + (f"Killzone: {killzone}",)

        if state is not None:
            mission = mission + (state[0],)

        history = await sqllite_helper.get_cell_history(cell_id)
        for point in history:
            mission = mission + point

    elif rules == "wh40k":
        cell_id = mission[2]
        await sqllite_helper.lock_mission(cell_id)
        number_of_safe_next_cells = await sqllite_helper.get_number_of_safe_next_cells(cell_id)
        mission = mission + (f"Бой на {(number_of_safe_next_cells + 1) * 500} pts",)
        history = await sqllite_helper.get_cell_history(cell_id)
        state = await sqllite_helper.get_state(cell_id)
        if state is not None:
            mission = mission + (state[0],)

        for point in history:
            mission = mission + point

    return mission


async def get_situation(battle_id, telegram_ids):
    """
    Checks if participants have a route to a warehouse and their situation.
    """
    cell_id = await sqllite_helper.get_cell_id_by_battle_id(battle_id)
    result = []

    for particpant_telegram in telegram_ids:
        has_route_to_warehouse = await map_helper.has_route_to_warehouse(
            cell_id, particpant_telegram)
        if has_route_to_warehouse is False:
            result.append(
                f"{particpant_telegram} не получает CP. Вместо этого "
                f"использует колоду со страгеммами.")

    return result


async def write_battle_result(battle_id, user_reply):
    """Writes the battle result to the database."""
    counts = user_reply.split(' ')
    await sqllite_helper.get_rules_of_mission(battle_id)
    await sqllite_helper.add_battle_result(
        int(battle_id), counts[0], counts[1])


async def apply_mission_rewards(battle_id, user_reply, user_telegram_id):
    """
    Apply rewards or penalties based on mission type and battle results.

    Args:
        battle_id: The ID of the battle
        user_reply: The battle result string like "15 10" 
            (user_score opponent_score)
        user_telegram_id: Telegram ID of the user who submitted the result
    """
    counts = user_reply.split(' ')
    user_score = int(counts[0])
    opponent_score = int(counts[1])

    # Get opponent's telegram ID
    opponent_telegram_id = await sqllite_helper.get_opponent_telegram_id(
        battle_id, user_telegram_id)
    if isinstance(opponent_telegram_id, tuple):
        opponent_telegram_id = opponent_telegram_id[0]

    # Get the mission details
    mission_id = await sqllite_helper.get_mission_id_by_battle_id(battle_id)
    mission_details = await sqllite_helper.get_mission_details(mission_id)

    if not mission_details:
        logger.error("Could not find mission details for battle %s", battle_id)
        return

    # Extract mission type (the first part of the mission tuple is the
    # mission name/type)
    mission_type = mission_details[0]
    rules = mission_details[1]

    # Get alliance IDs for both players
    user_alliance_id = await sqllite_helper.get_alliance_of_warmaster(
        user_telegram_id)
    opponent_alliance_id = await sqllite_helper.get_alliance_of_warmaster(
        opponent_telegram_id)

    # Determine winner
    if user_score > opponent_score:
        winner_alliance_id = user_alliance_id[0]
        loser_alliance_id = opponent_alliance_id[0]
        winner_score = user_score
        loser_score = opponent_score
    elif opponent_score > user_score:
        winner_alliance_id = opponent_alliance_id[0]
        loser_alliance_id = user_alliance_id[0]
        winner_score = opponent_score
        loser_score = user_score
    else:
        # Draw - no clear winner
        winner_alliance_id = None
        loser_alliance_id = None
        winner_score = user_score
        loser_score = opponent_score

    # Apply rewards based on mission type and rules
    if rules == "killteam":
        # Process Kill Team missions
        if mission_type.lower() == "loot":
            # Both players get 1 resource
            await sqllite_helper.increase_common_resource(
                user_alliance_id[0], 1)
            await sqllite_helper.increase_common_resource(
                opponent_alliance_id[0], 1)

            # Winner gets additional resources based on score ratio
            if winner_alliance_id:
                # Calculate additional resources (minimum 1)
                if loser_score == 0:
                    additional_resources = 3  # To avoid division by zero
                else:
                    score_ratio = winner_score / loser_score
                    additional_resources = max(1, int(score_ratio))

                await sqllite_helper.increase_common_resource(
                    winner_alliance_id, additional_resources)

                logger.info(
                    "Loot mission: Winner %s received %s resources total",
                    winner_alliance_id, additional_resources + 1)
                logger.info(
                    "Loot mission: Loser %s received 1 resource",
                    loser_alliance_id)

        elif mission_type.lower() == "transmission":
            # Winner gets resources equal to opponent's resources but
            # limited by own resources
            if winner_alliance_id and loser_alliance_id:
                # Get current resource amounts
                winner_resources = await sqllite_helper.get_alliance_resources(
                    winner_alliance_id)
                loser_resources = await sqllite_helper.get_alliance_resources(
                    loser_alliance_id)

                # Calculate transfer amount (minimum of loser's and winner's
                # resources)
                transfer_amount = min(loser_resources, winner_resources)

                if transfer_amount > 0:
                    await sqllite_helper.increase_common_resource(
                        winner_alliance_id, transfer_amount)
                    logger.info(
                        "Transmission mission: Winner %s received %s "
                        "resources",
                        winner_alliance_id, transfer_amount)
                else:
                    logger.info(
                        "Transmission mission: No resources transferred "
                        "(either winner or loser has 0 resources)")

        elif mission_type.lower() == "secure":
            # Winner gets resources, may create warehouse
            if winner_alliance_id:
                await sqllite_helper.increase_common_resource(
                    winner_alliance_id, 2)
                logger.info(
                    "Secure mission: Winner %s received 2 resources",
                    winner_alliance_id)

        elif mission_type.lower() == "intel":
            # Creates warehouse in the hex where the mission took place
            if winner_alliance_id:
                cell_id = await sqllite_helper.get_cell_id_by_battle_id(
                    battle_id)
                await sqllite_helper.create_warehouse(cell_id)
                logger.info(
                    "Intel mission: Warehouse created in hex %s",
                    cell_id)

        elif mission_type.lower() == "sabotage":
            # No resource changes for sabotage missions
            logger.info("Sabotage mission: No resource changes")
            
        elif mission_type.lower() == "resource collection":
            # Winner gets 1 resource from eliminated alliance reserves
            if winner_alliance_id:
                await sqllite_helper.increase_common_resource(
                    winner_alliance_id, 1)
                logger.info(
                    f"Resource Collection mission: Winner "
                    f"{winner_alliance_id} gained 1 resource")

        elif mission_type.lower() == "extraction":
            # Winner gets 1 resource, loser loses 1 resource
            if winner_alliance_id and loser_alliance_id:
                await sqllite_helper.increase_common_resource(
                    winner_alliance_id, 1)
                await sqllite_helper.decrease_common_resource(
                    loser_alliance_id, 1)
                logger.info(
                    "Extraction mission: Winner %s gained 1 resource, "
                    "loser %s lost 1 resource",
                    winner_alliance_id, loser_alliance_id)

        elif mission_type.lower() == "power surge":
            # Loser loses resources equal to number of warehouses (minimum 1)
            if winner_alliance_id and loser_alliance_id:
                warehouse_count = await (
                    sqllite_helper.get_warehouse_count_by_alliance(loser_alliance_id)
                )
                resource_loss = max(1, warehouse_count)
                
                await sqllite_helper.decrease_common_resource(
                    loser_alliance_id, resource_loss)
                logger.info(
                    "Power Surge mission: Loser %s lost %s resources "
                    "(based on %s warehouses)",
                    loser_alliance_id, resource_loss, warehouse_count)

        elif mission_type.lower() == "coordinates":
            # Loser loses resources equal to number of warehouses (minimum 1)
            # Winner destroys enemy warehouse
            if winner_alliance_id and loser_alliance_id:
                warehouse_count = await (
                    sqllite_helper.get_warehouse_count_by_alliance(loser_alliance_id)
                )
                resource_loss = max(1, warehouse_count)
                
                await sqllite_helper.decrease_common_resource(
                    loser_alliance_id, resource_loss)
                
                # Destroy one enemy warehouse if exists
                await sqllite_helper.destroy_warehouse_by_alliance(loser_alliance_id)
                
                logger.info(
                    "Coordinates mission: Loser %s lost %s resources and one warehouse",
                    loser_alliance_id, resource_loss)

        # Add more mission types as needed

    # Check if loser alliance has any hexes remaining after battle
    if loser_alliance_id:
        remaining_hexes = await sqllite_helper.get_hexes_by_alliance(
            loser_alliance_id)
        if len(remaining_hexes) == 0:
            logger.info(
                "Alliance %s eliminated - no hexes remaining",
                loser_alliance_id)
            await handle_alliance_elimination(loser_alliance_id)

    elif rules == "wh40k":
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


async def start_battle(mission_id, participants):
    """Starts a new battle for the given mission and participants."""
    battle_id = await sqllite_helper.add_battle(mission_id)
    for participant in participants:
        await sqllite_helper.add_battle_participant(
            battle_id[0],
            participant[0]
        )
    return battle_id[0]
