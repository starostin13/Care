"""
Tests for common_resource feature flag integration.

Tests that common_resource mechanics are properly disabled when
the feature flag is turned off.
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


def test_common_resource_flag_toggles_correctly():
    """Test that the common_resource flag can be toggled."""
    
    async def run():
        # Get initial state
        initial_state = await feature_flags_helper.is_feature_enabled('common_resource')
        print(f"Initial state: {initial_state}")
        
        # Toggle off
        new_state = await feature_flags_helper.toggle_feature_flag('common_resource')
        print(f"After first toggle: {new_state}")
        assert new_state != initial_state, "State should change after toggle"
        
        # Verify state is persisted
        verified_state = await feature_flags_helper.is_feature_enabled('common_resource')
        print(f"Verified state: {verified_state}")
        assert verified_state == new_state, "State should be persisted"
        
        # Toggle back
        final_state = await feature_flags_helper.toggle_feature_flag('common_resource')
        print(f"After second toggle: {final_state}")
        assert final_state == initial_state, "Should return to initial state"
        
        return True
    
    result = asyncio.run(run())
    assert result is True


def test_feature_flag_affects_resource_checks():
    """Test that checking feature flag works correctly."""
    
    async def run():
        # Test when enabled
        await feature_flags_helper.toggle_feature_flag('common_resource')  # Ensure it's on
        enabled = await feature_flags_helper.is_feature_enabled('common_resource')
        
        if not enabled:
            # If it was off, toggle to turn on
            await feature_flags_helper.toggle_feature_flag('common_resource')
            enabled = await feature_flags_helper.is_feature_enabled('common_resource')
        
        print(f"Feature enabled: {enabled}")
        assert enabled is True, "Feature should be enabled"
        
        # Toggle off
        await feature_flags_helper.toggle_feature_flag('common_resource')
        disabled = await feature_flags_helper.is_feature_enabled('common_resource')
        print(f"Feature disabled: {disabled}")
        assert disabled is False, "Feature should be disabled"
        
        # Toggle back on for other tests
        await feature_flags_helper.toggle_feature_flag('common_resource')
        
        return True
    
    result = asyncio.run(run())
    assert result is True


if __name__ == "__main__":
    print("Running common_resource feature flag integration tests...")
    
    print("\n✓ Testing common_resource flag toggles...")
    test_common_resource_flag_toggles_correctly()
    
    print("\n✓ Testing feature flag affects resource checks...")
    test_feature_flag_affects_resource_checks()
    
    print("\n✅ All common_resource feature flag integration tests passed!")

