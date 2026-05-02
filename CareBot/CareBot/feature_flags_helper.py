"""
Feature flags helper module.

This module provides utilities for checking and managing feature flags.
Feature flags allow administrators to enable/disable specific features
without code changes.
"""
import config

# Автоматическое переключение на mock версию в тестовом режиме
if config.TEST_MODE:
    import mock_sqlite_helper as sqllite_helper
    print("🧪 Feature Flags Helper using MOCK SQLite helper")
else:
    import sqllite_helper
    print("✅ Feature Flags Helper using REAL SQLite helper")


async def is_feature_enabled(flag_name: str) -> bool:
    """
    Check if a feature flag is enabled.
    
    Args:
        flag_name: Name of the feature flag to check
        
    Returns:
        True if feature is enabled, False otherwise.
        Returns True by default if flag doesn't exist (fail-safe).
    """
    return await sqllite_helper.is_feature_enabled(flag_name)


async def toggle_feature_flag(flag_name: str) -> bool:
    """
    Toggle a feature flag between enabled and disabled.
    
    Args:
        flag_name: Name of the feature flag to toggle
        
    Returns:
        New state of the flag (True=enabled, False=disabled)
    """
    return await sqllite_helper.toggle_feature_flag(flag_name)


async def get_all_feature_flags() -> list:
    """
    Get all feature flags with their current status.
    
    Returns:
        List of tuples: [(flag_name, enabled, description), ...]
    """
    return await sqllite_helper.get_all_feature_flags()
