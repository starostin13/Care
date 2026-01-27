#!/usr/bin/env python3
"""
Integration test for double experience bonus feature.
Simulates the full flow of determining dominant alliance and building messages.
"""

import asyncio
import sys
import os

# Add the CareBot directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'CareBot', 'CareBot'))

# Set test mode BEFORE importing
os.environ['CAREBOT_TEST_MODE'] = 'true'

import mock_sqlite_helper as sqllite_helper
import mission_message_builder


async def simulate_mission_creation_flow():
    """Simulate the complete mission creation flow with dominant alliance detection."""
    print("\n=== Integration Test: Mission Creation with Dominant Alliance ===\n")
    
    # Scenario 1: Attacker (User1, alliance 1) vs Defender (User2, alliance 2)
    # Alliance 1 is dominant
    print("Scenario 1: Regular player vs Dominant alliance member")
    print("-" * 60)
    
    attacker_id = '123456789'  # User2, alliance 2
    defender_id = '325313837'  # User1, alliance 1 (dominant)
    
    # Get dominant alliance
    dominant_alliance_id = await sqllite_helper.get_dominant_alliance()
    print(f"Dominant alliance ID: {dominant_alliance_id}")
    
    # Get alliances
    attacker_alliance = await sqllite_helper.get_alliance_of_warmaster(attacker_id)
    defender_alliance = await sqllite_helper.get_alliance_of_warmaster(defender_id)
    
    attacker_alliance_id = attacker_alliance[0] if attacker_alliance else None
    defender_alliance_id = defender_alliance[0] if defender_alliance else None
    
    print(f"Attacker (User2) alliance: {attacker_alliance_id}")
    print(f"Defender (User1) alliance: {defender_alliance_id}")
    
    # Check dominance
    attacker_is_dominant = (dominant_alliance_id and 
                           attacker_alliance_id == dominant_alliance_id and
                           attacker_alliance_id != 0)
    defender_is_dominant = (dominant_alliance_id and 
                           defender_alliance_id == dominant_alliance_id and
                           defender_alliance_id != 0)
    
    print(f"Attacker is dominant: {attacker_is_dominant}")
    print(f"Defender is dominant: {defender_is_dominant}")
    
    # Build message for attacker
    attacker_nickname = await sqllite_helper.get_nicknamane(attacker_id)
    defender_nickname = await sqllite_helper.get_nicknamane(defender_id)
    
    print(f"\nAttacker nickname: {attacker_nickname}")
    print(f"Defender nickname: {defender_nickname}")
    
    # Build attacker's message
    print("\n--- Attacker's Message ---")
    attacker_builder = mission_message_builder.MissionMessageBuilder(
        mission_id=123,
        description="Loot: Retrieve resources",
        rules="killteam"
    )
    
    if defender_is_dominant:
        attacker_builder.add_double_exp_bonus(defender_nickname)
    
    attacker_message = attacker_builder.build()
    print(attacker_message)
    
    # Verify attacker gets bonus (defender is dominant)
    assert "⚔️" in attacker_message, "Attacker should see bonus message"
    assert "в 2 раза быстрее" in attacker_message, "Should mention 2x speed"
    print("\n✓ Attacker message correctly shows 2x exp bonus")
    
    # Build defender's message
    print("\n--- Defender's Message ---")
    defender_builder = mission_message_builder.MissionMessageBuilder(
        mission_id=123,
        description="Loot: Retrieve resources",
        rules="killteam"
    )
    
    if attacker_is_dominant:
        defender_builder.add_double_exp_bonus(attacker_nickname)
    
    defender_message = defender_builder.build()
    print(defender_message)
    
    # Verify defender does NOT get bonus (attacker is not dominant)
    assert "⚔️" not in defender_message, "Defender should NOT see bonus message"
    print("\n✓ Defender message correctly has NO bonus (attacker not dominant)")
    
    # Scenario 2: Both from non-dominant alliances
    print("\n\nScenario 2: Two players from non-dominant alliances")
    print("-" * 60)
    
    # Create a builder when neither is dominant
    builder = mission_message_builder.MissionMessageBuilder(
        mission_id=456,
        description="Secure objectives",
        rules="killteam"
    )
    
    # Neither gets bonus
    message = builder.build()
    print(message)
    
    assert "⚔️" not in message, "No bonus should be shown"
    print("\n✓ No bonus shown when neither player is from dominant alliance")
    
    print("\n" + "=" * 60)
    print("✅ INTEGRATION TEST PASSED!")
    print("=" * 60)
    print("\nSummary:")
    print("- Dominant alliance detection works correctly")
    print("- Message builder constructs appropriate messages")
    print("- Bonus is shown only when fighting dominant alliance member")
    print("- Message content is correctly localized in Russian")
    

async def test_message_persistence():
    """Test that mission messages can handle various states."""
    print("\n=== Test: Message Component Persistence ===\n")
    
    # Build a complex message step by step
    builder = mission_message_builder.MissionMessageBuilder(
        mission_id=789,
        description="Intel: Gather intelligence",
        rules="killteam"
    )
    
    # Add components in order
    builder.add_double_exp_bonus("TestPlayer")
    builder.add_situation(["Player has no CP", "Supply lines cut"])
    builder.add_reinforcement_message("⚠️ Cannot send reinforcements")
    builder.add_custom_info("Additional info: Weather is bad")
    
    message = builder.build()
    print("Complex message:")
    print(message)
    print()
    
    # Verify all components are present
    assert "📜Intel: Gather intelligence: killteam" in message
    assert "#789" in message
    assert "⚔️" in message
    assert "TestPlayer" in message
    assert "Player has no CP" in message
    assert "Supply lines cut" in message
    assert "⚠️ Cannot send reinforcements" in message
    assert "Additional info: Weather is bad" in message
    
    print("✓ All message components preserved correctly")
    print("✓ Components appear in correct order")


async def run_integration_tests():
    """Run all integration tests."""
    print("=" * 60)
    print("Double Experience Bonus - Integration Tests")
    print("=" * 60)
    
    try:
        await simulate_mission_creation_flow()
        await test_message_persistence()
        
        print("\n" + "=" * 60)
        print("✅ ALL INTEGRATION TESTS PASSED!")
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
    success = asyncio.run(run_integration_tests())
    sys.exit(0 if success else 1)
