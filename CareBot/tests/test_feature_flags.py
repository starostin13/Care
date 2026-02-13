"""
Tests for feature flags functionality.

Tests the ability to toggle features on/off and verify that
feature flag checks work correctly.
"""
import os
import sys
import asyncio
import types

MODULE_DIR = os.path.join(os.path.dirname(__file__), '..', 'CareBot')
sys.path.insert(0, os.path.abspath(MODULE_DIR))

# Set test mode before importing modules
os.environ['CAREBOT_TEST_MODE'] = 'true'
sys.modules.setdefault("config", types.SimpleNamespace(TEST_MODE=True))

import feature_flags_helper  # noqa: E402


def test_feature_flag_enabled_by_default():
    """Test that common_resource flag is enabled by default."""
    async def run():
        enabled = await feature_flags_helper.is_feature_enabled('common_resource')
        return enabled
    
    result = asyncio.run(run())
    assert result is True, "common_resource should be enabled by default"


def test_toggle_feature_flag():
    """Test toggling a feature flag on and off."""
    async def run():
        # Get initial state
        initial_state = await feature_flags_helper.is_feature_enabled('common_resource')
        
        # Toggle the flag
        new_state = await feature_flags_helper.toggle_feature_flag('common_resource')
        
        # Verify it changed
        assert new_state != initial_state, "Flag should have changed state"
        
        # Verify the state is persisted
        current_state = await feature_flags_helper.is_feature_enabled('common_resource')
        assert current_state == new_state, "Flag state should be persisted"
        
        # Toggle back to original state
        final_state = await feature_flags_helper.toggle_feature_flag('common_resource')
        assert final_state == initial_state, "Flag should return to initial state"
        
        return True
    
    result = asyncio.run(run())
    assert result is True


def test_get_all_feature_flags():
    """Test retrieving all feature flags."""
    async def run():
        flags = await feature_flags_helper.get_all_feature_flags()
        
        # Should return a list
        assert isinstance(flags, list), "Should return a list"
        
        # Should contain common_resource flag
        flag_names = [flag[0] for flag in flags]
        assert 'common_resource' in flag_names, "Should contain common_resource flag"
        
        # Each flag should be a tuple with (name, enabled, description)
        for flag in flags:
            assert len(flag) == 3, "Each flag should have 3 elements"
            assert isinstance(flag[0], str), "Flag name should be a string"
            assert isinstance(flag[1], int), "Enabled should be an integer (0 or 1)"
            assert isinstance(flag[2], str), "Description should be a string"
        
        return True
    
    result = asyncio.run(run())
    assert result is True


def test_unknown_flag_returns_true():
    """Test that unknown flags return True by default (fail-safe)."""
    async def run():
        enabled = await feature_flags_helper.is_feature_enabled('nonexistent_flag')
        return enabled
    
    result = asyncio.run(run())
    assert result is True, "Unknown flags should be enabled by default (fail-safe)"


if __name__ == "__main__":
    print("Running feature flags tests...")
    
    print("✓ Testing feature enabled by default...")
    test_feature_flag_enabled_by_default()
    
    print("✓ Testing toggle feature flag...")
    test_toggle_feature_flag()
    
    print("✓ Testing get all feature flags...")
    test_get_all_feature_flags()
    
    print("✓ Testing unknown flag returns true...")
    test_unknown_flag_returns_true()
    
    print("\n✅ All feature flags tests passed!")
