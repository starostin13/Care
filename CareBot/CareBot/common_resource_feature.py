"""
Common Resource Feature - Alliance resource management mechanics.

This feature controls whether alliances gain and lose resources based on
battle outcomes and mission types.
"""
import logging
from typing import Dict, Any, Optional
from features import Feature
import config

# Автоматическое переключение на mock версию в тестовом режиме
if config.TEST_MODE:
    import mock_sqlite_helper as sqllite_helper
    print("🧪 Common Resource Feature using MOCK SQLite helper")
else:
    import sqllite_helper
    print("✅ Common Resource Feature using REAL SQLite helper")

logger = logging.getLogger(__name__)


class CommonResourceFeature(Feature):
    """
    Alliance common resource mechanics.
    
    When enabled:
    - Alliances receive resources for participation
    - Different mission types award/deduct resources based on outcomes
    - Mission bonuses apply resource rewards
    """
    
    def __init__(self):
        super().__init__(
            flag_name='common_resource',
            description='Alliance resource mechanics'
        )
    
    async def on_result_approved(self, battle_data: Dict[str, Any]) -> None:
        """
        Award or deduct resources when battle results are approved.
        
        This implements all the resource logic that was previously scattered
        throughout mission_helper.py.
        """
        user_alliance = battle_data.get('user_alliance')
        opponent_alliance = battle_data.get('opponent_alliance')
        winner_alliance_id = battle_data.get('winner_alliance_id')
        loser_alliance_id = battle_data.get('loser_alliance_id')
        winner_score = battle_data.get('winner_score', 0)
        loser_score = battle_data.get('loser_score', 0)
        mission_type = battle_data.get('mission_type', '').lower()
        rules = battle_data.get('rules', '')
        reward_config = battle_data.get('reward_config')
        
        # Award participation resources
        participant_alliances = []
        if user_alliance not in (None, 0):
            participant_alliances.append(user_alliance)
        if opponent_alliance not in (None, 0):
            participant_alliances.append(opponent_alliance)
        
        for alliance_id in set(participant_alliances):
            await sqllite_helper.increase_common_resource(alliance_id, 1)
            logger.info("Alliance %s received 1 common resource for participation", alliance_id)
        
        # Process mission type specific rewards
        await self._process_mission_type_rewards(
            mission_type=mission_type,
            rules=rules,
            winner_alliance_id=winner_alliance_id,
            loser_alliance_id=loser_alliance_id,
            winner_score=winner_score,
            loser_score=loser_score,
            user_alliance=user_alliance,
            opponent_alliance=opponent_alliance
        )
        
        # Apply mission-specific rewards from reward_config
        if reward_config:
            await self._apply_reward_config(reward_config, winner_alliance_id)
    
    async def _process_mission_type_rewards(
        self,
        mission_type: str,
        rules: str,
        winner_alliance_id: Optional[int],
        loser_alliance_id: Optional[int],
        winner_score: int,
        loser_score: int,
        user_alliance: int,
        opponent_alliance: int
    ) -> None:
        """Process rewards based on mission type and rules."""
        
        if rules == "killteam":
            await self._process_killteam_mission(
                mission_type, winner_alliance_id, loser_alliance_id,
                winner_score, loser_score, user_alliance, opponent_alliance
            )
    
    async def _process_killteam_mission(
        self,
        mission_type: str,
        winner_alliance_id: Optional[int],
        loser_alliance_id: Optional[int],
        winner_score: int,
        loser_score: int,
        user_alliance: int,
        opponent_alliance: int
    ) -> None:
        """Process Kill Team mission rewards."""
        
        if mission_type == "loot":
            # Both players get 1 resource (already awarded as participation)
            # Winner gets additional resources based on score ratio
            if winner_alliance_id:
                if loser_score == 0:
                    additional_resources = 3
                else:
                    score_ratio = winner_score / loser_score
                    additional_resources = max(1, int(score_ratio))
                
                await sqllite_helper.increase_common_resource(
                    winner_alliance_id, additional_resources)
                logger.info(
                    "Loot mission: Winner %s received %s additional resources",
                    winner_alliance_id, additional_resources)
        
        elif mission_type == "transmission":
            # Winner gets resources equal to opponent's resources but limited by own
            if winner_alliance_id and loser_alliance_id:
                winner_resources = await sqllite_helper.get_alliance_resources(winner_alliance_id)
                loser_resources = await sqllite_helper.get_alliance_resources(loser_alliance_id)
                transfer_amount = min(loser_resources, winner_resources)
                
                if transfer_amount > 0:
                    await sqllite_helper.increase_common_resource(
                        winner_alliance_id, transfer_amount)
                    logger.info(
                        "Transmission mission: Winner %s received %s resources",
                        winner_alliance_id, transfer_amount)
        
        elif mission_type == "secure":
            # Winner gets 2 resources
            if winner_alliance_id:
                await sqllite_helper.increase_common_resource(winner_alliance_id, 2)
                logger.info("Secure mission: Winner %s received 2 resources", winner_alliance_id)
        
        elif mission_type == "resource collection":
            # Winner gets 1 resource
            if winner_alliance_id:
                await sqllite_helper.increase_common_resource(winner_alliance_id, 1)
                logger.info(
                    "Resource Collection mission: Winner %s gained 1 resource",
                    winner_alliance_id)
        
        elif mission_type == "extraction":
            # Winner gets 1 resource, loser loses 1 resource
            if winner_alliance_id and loser_alliance_id:
                await sqllite_helper.increase_common_resource(winner_alliance_id, 1)
                await sqllite_helper.decrease_common_resource(loser_alliance_id, 1)
                logger.info(
                    "Extraction mission: Winner %s gained 1, loser %s lost 1 resource",
                    winner_alliance_id, loser_alliance_id)
        
        elif mission_type == "power surge":
            # Loser loses resources equal to number of warehouses
            if winner_alliance_id and loser_alliance_id:
                warehouse_count = await sqllite_helper.get_warehouse_count_by_alliance(
                    loser_alliance_id)
                resource_loss = max(1, warehouse_count)
                
                await sqllite_helper.decrease_common_resource(loser_alliance_id, resource_loss)
                logger.info(
                    "Power Surge mission: Loser %s lost %s resources",
                    loser_alliance_id, resource_loss)
        
        elif mission_type == "coordinates":
            # Loser loses resources and one warehouse
            if winner_alliance_id and loser_alliance_id:
                warehouse_count = await sqllite_helper.get_warehouse_count_by_alliance(
                    loser_alliance_id)
                resource_loss = max(1, warehouse_count)
                
                await sqllite_helper.decrease_common_resource(loser_alliance_id, resource_loss)
                await sqllite_helper.destroy_warehouse_by_alliance(loser_alliance_id)
                
                logger.info(
                    "Coordinates mission: Loser %s lost %s resources and one warehouse",
                    loser_alliance_id, resource_loss)
    
    async def _apply_reward_config(
        self,
        reward_config: str,
        winner_alliance_id: Optional[int]
    ) -> None:
        """Apply mission-specific resource bonus from reward_config."""
        # Parse reward_config to extract COMMON_RESOURCE value
        from mission_helper import _parse_reward_config
        rewards = _parse_reward_config(reward_config)
        resource_bonus_value = rewards.get("COMMON_RESOURCE", 0)
        
        if resource_bonus_value and winner_alliance_id:
            await sqllite_helper.increase_common_resource(
                winner_alliance_id, resource_bonus_value)
            logger.info(
                "Applied mission resource bonus: +%s to alliance %s",
                resource_bonus_value, winner_alliance_id)


# Create and export the common resource feature instance
common_resource_feature = CommonResourceFeature()
