"""
Base Feature class and feature registry for toggleable game features.

Features can implement lifecycle methods that are called at specific points:
- on_create_mission(mission_data) - Called when a mission is created
- on_result_approved(battle_data) - Called when battle results are approved
- on_battle_start(battle_data) - Called when battle starts
- on_mission_complete(mission_data) - Called when mission completes

Each feature can be toggled on/off by administrators without code changes.
"""
import logging
from typing import Dict, Optional, Any
import config

# Автоматическое переключение на mock версию в тестовом режиме
if config.TEST_MODE:
    import mock_sqlite_helper as sqllite_helper
    print("🧪 Features using MOCK SQLite helper")
else:
    import sqllite_helper
    print("✅ Features using REAL SQLite helper")

logger = logging.getLogger(__name__)


class Feature:
    """
    Base class for all toggleable features.
    
    Subclasses should override lifecycle methods to implement feature-specific logic.
    """
    
    def __init__(self, flag_name: str, description: str):
        """
        Initialize feature.
        
        Args:
            flag_name: Unique identifier for this feature in database
            description: Human-readable description
        """
        self.flag_name = flag_name
        self.description = description
    
    async def is_enabled(self) -> bool:
        """Check if this feature is currently enabled."""
        return await sqllite_helper.is_feature_enabled(self.flag_name)
    
    async def on_create_mission(self, mission_data: Dict[str, Any]) -> None:
        """
        Called when a mission is created.
        
        Args:
            mission_data: Dictionary with mission information including:
                - rules: str - Game rules (killteam, wh40k, etc)
                - cell: Optional[int] - Map cell
                - attacker_id: str - Telegram ID
                - defender_id: str - Telegram ID
        """
        pass
    
    async def on_result_approved(self, battle_data: Dict[str, Any]) -> None:
        """
        Called when battle results are approved.
        
        Args:
            battle_data: Dictionary with battle information including:
                - battle_id: int
                - mission_id: int
                - user_score: int
                - opponent_score: int
                - user_alliance: Optional[int]
                - opponent_alliance: Optional[int]
                - winner_alliance_id: Optional[int]
                - loser_alliance_id: Optional[int]
                - mission_type: str
                - rules: str
        """
        pass
    
    async def on_battle_start(self, battle_data: Dict[str, Any]) -> None:
        """
        Called when a battle starts.
        
        Args:
            battle_data: Dictionary with battle information
        """
        pass
    
    async def on_mission_complete(self, mission_data: Dict[str, Any]) -> None:
        """
        Called when a mission is completed.
        
        Args:
            mission_data: Dictionary with mission information
        """
        pass


class FeatureRegistry:
    """
    Registry for all game features.
    
    Features register themselves and can be queried by flag name.
    Provides methods to call lifecycle hooks on all enabled features.
    """
    
    def __init__(self):
        self._features: Dict[str, Feature] = {}
    
    def register(self, feature: Feature) -> None:
        """Register a feature in the registry."""
        self._features[feature.flag_name] = feature
        logger.info(f"Registered feature: {feature.flag_name}")
    
    def get_feature(self, flag_name: str) -> Optional[Feature]:
        """Get a feature by its flag name."""
        return self._features.get(flag_name)
    
    def get_all_features(self) -> Dict[str, Feature]:
        """Get all registered features."""
        return self._features.copy()
    
    async def on_create_mission(self, mission_data: Dict[str, Any]) -> None:
        """Call on_create_mission on all enabled features."""
        for feature in self._features.values():
            if await feature.is_enabled():
                try:
                    await feature.on_create_mission(mission_data)
                except Exception as e:
                    logger.error(f"Error in {feature.flag_name}.on_create_mission: {e}", exc_info=True)
    
    async def on_result_approved(self, battle_data: Dict[str, Any]) -> None:
        """Call on_result_approved on all enabled features."""
        for feature in self._features.values():
            if await feature.is_enabled():
                try:
                    await feature.on_result_approved(battle_data)
                except Exception as e:
                    logger.error(f"Error in {feature.flag_name}.on_result_approved: {e}", exc_info=True)
    
    async def on_battle_start(self, battle_data: Dict[str, Any]) -> None:
        """Call on_battle_start on all enabled features."""
        for feature in self._features.values():
            if await feature.is_enabled():
                try:
                    await feature.on_battle_start(battle_data)
                except Exception as e:
                    logger.error(f"Error in {feature.flag_name}.on_battle_start: {e}", exc_info=True)
    
    async def on_mission_complete(self, mission_data: Dict[str, Any]) -> None:
        """Call on_mission_complete on all enabled features."""
        for feature in self._features.values():
            if await feature.is_enabled():
                try:
                    await feature.on_mission_complete(mission_data)
                except Exception as e:
                    logger.error(f"Error in {feature.flag_name}.on_mission_complete: {e}", exc_info=True)


# Global feature registry
feature_registry = FeatureRegistry()
