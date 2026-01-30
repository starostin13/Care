#!/usr/bin/env python3
"""
Test for double experience bonus feature.
Tests that players fighting against dominant alliance members get 2x exp bonus notification.
"""

import asyncio
import sys
import os

# Add the CareBot directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'CareBot', 'CareBot'))

# Set test mode BEFORE importing sqllite_helper
os.environ['CAREBOT_TEST_MODE'] = 'true'

import mock_sqlite_helper as sqllite_helper
import mission_message_builder


async def test_dominant_alliance_detection():
    """Test that get_dominant_alliance returns the alliance with most cells."""
    print("\n=== Test 1: Dominant Alliance Detection ===")
    
    dominant = await sqllite_helper.get_dominant_alliance()
    print(f"✓ Dominant alliance ID: {dominant}")
    
    # In mock, this should return 1 (Crimson Legion)
    assert dominant is not None, "Dominant alliance should not be None in test"
    print(f"✓ Test passed: Dominant alliance detected")


async def test_message_builder():
    """Test the MissionMessageBuilder class."""
    print("\n=== Test 2: Mission Message Builder ===")
    
    # Test basic message
    builder = mission_message_builder.MissionMessageBuilder(
        mission_id=123,
        description="Test Mission: Secure objectives",
        rules="killteam"
    )
    
    basic_message = builder.build()
    print(f"Basic message:\n{basic_message}\n")
    assert "📜Test Mission: Secure objectives: killteam" in basic_message
    assert "#123" in basic_message
    print("✓ Basic message construction works")
    
    # Test message with double exp bonus
    builder2 = mission_message_builder.MissionMessageBuilder(
        mission_id=456,
        description="Loot: Retrieve resources",
        rules="killteam"
    )
    builder2.add_double_exp_bonus("TestOpponent")
    message_with_bonus = builder2.build()
    print(f"Message with bonus:\n{message_with_bonus}\n")
    assert "⚔️" in message_with_bonus
    assert "доминирующего альянса" in message_with_bonus
    assert "в 2 раза быстрее" in message_with_bonus
    assert "TestOpponent" in message_with_bonus
    print("✓ Double exp bonus message works")
    
    # Test message with multiple components
    builder3 = mission_message_builder.MissionMessageBuilder(
        mission_id=789,
        description="Intel: Gather intelligence",
        rules="killteam"
    )
    builder3.add_double_exp_bonus("EnemyPlayer")
    builder3.add_situation(["Ситуация: У вас нет CP"])
    builder3.add_reinforcement_message("⚠️ Ограничение резервов")
    message_full = builder3.build()
    print(f"Full message:\n{message_full}\n")
    assert "⚔️" in message_full
    assert "Ситуация" in message_full
    assert "⚠️ Ограничение резервов" in message_full
    print("✓ Multiple components work correctly")


async def test_alliance_membership():
    """Test alliance membership detection."""
    print("\n=== Test 3: Alliance Membership Detection ===")
    
    # Get test users
    user1_alliance = await sqllite_helper.get_alliance_of_warmaster('325313837')
    user2_alliance = await sqllite_helper.get_alliance_of_warmaster('123456789')
    
    print(f"User1 alliance: {user1_alliance}")
    print(f"User2 alliance: {user2_alliance}")
    
    # Extract alliance IDs
    user1_id = user1_alliance[0] if user1_alliance else None
    user2_id = user2_alliance[0] if user2_alliance else None
    
    print(f"User1 alliance ID: {user1_id}")
    print(f"User2 alliance ID: {user2_id}")
    
    # Get dominant alliance
    dominant = await sqllite_helper.get_dominant_alliance()
    print(f"Dominant alliance ID: {dominant}")
    
    # Check if either is dominant
    user1_is_dominant = (user1_id == dominant and user1_id != 0)
    user2_is_dominant = (user2_id == dominant and user2_id != 0)
    
    print(f"User1 is dominant: {user1_is_dominant}")
    print(f"User2 is dominant: {user2_is_dominant}")
    
    # In mock setup, user1 is in alliance 1 which is dominant
    assert user1_is_dominant, "User1 should be in dominant alliance in test setup"
    print("✓ Alliance membership detection works")


async def test_message_builder_edge_cases():
    """Test edge cases for message builder."""
    print("\n=== Test 4: Message Builder Edge Cases ===")
    
    # Test with no opponent name
    builder = mission_message_builder.MissionMessageBuilder(
        mission_id=999,
        description="Test",
        rules="test"
    )
    builder.add_double_exp_bonus()  # No name provided
    message = builder.build()
    assert "оппонент является членом доминирующего альянса" in message
    print("✓ Double exp bonus without opponent name works")
    
    # Test with None/empty components
    builder2 = mission_message_builder.MissionMessageBuilder(
        mission_id=888,
        description="Test",
        rules="test"
    )
    builder2.add_situation(None)
    builder2.add_situation([])
    builder2.add_reinforcement_message(None)
    builder2.add_reinforcement_message("")
    message2 = builder2.build()
    # Should still be a valid message
    assert "#888" in message2
    print("✓ Handling of None/empty components works")


async def run_all_tests():
    """Run all tests."""
    print("=" * 60)
    print("Running Double Experience Bonus Tests")
    print("=" * 60)
    
    try:
        await test_dominant_alliance_detection()
        await test_message_builder()
        await test_alliance_membership()
        await test_message_builder_edge_cases()
        
        print("\n" + "=" * 60)
        print("✅ ALL TESTS PASSED!")
        print("=" * 60)
        return True
    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False
    except Exception as e:
        print(f"\n❌ UNEXPECTED ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == '__main__':
    success = asyncio.run(run_all_tests())
    sys.exit(0 if success else 1)
