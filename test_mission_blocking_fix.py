#!/usr/bin/env python3
"""
Integration test to verify the mission blocking fix.

This test simulates the scenario described in the issue:
- Two pairs of players start 10 minutes apart
- They should NOT get the same mission number
- The first pair gets a mission, it gets locked
- The second pair gets a different mission

Test validates:
1. New missions are saved with locked=0
2. get_mission finds unlocked missions
3. lock_mission properly locks missions
4. Locked missions are not returned by get_mission
"""

import sys
import os

# Add the project directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'CareBot', 'CareBot'))

# Set test mode BEFORE importing
os.environ['CAREBOT_TEST_MODE'] = 'true'

import asyncio
import mock_sqlite_helper as db


async def test_mission_blocking_scenario():
    """
    Simulate the exact scenario from the issue:
    Two pairs of players starting 10 minutes apart.
    """
    print("\n" + "=" * 70)
    print("SCENARIO: Two pairs of players start 10 minutes apart")
    print("=" * 70)
    
    # Reset mock data
    db.MOCK_MISSIONS.clear()
    
    # === PAIR 1: First pair of players (Time: T) ===
    print("\n[TIME T] Pair 1 starts playing...")
    
    # Pair 1 requests a killteam mission
    mission_pair1 = await db.get_mission("killteam")
    
    if mission_pair1:
        print("  ❌ ERROR: Found existing mission (should be none)")
        return False
    else:
        print("  ✓ No existing missions found (correct)")
    
    # Generate new mission for Pair 1
    print("  → Generating new mission for Pair 1...")
    mission_data = ("Secure", "killteam", None, "Secure objectives", None)
    mission_id_1 = await db.save_mission(mission_data)
    print(f"  ✓ Created mission ID: {mission_id_1}")
    
    # Verify mission is saved as unlocked
    saved_mission = db.MOCK_MISSIONS.get(mission_id_1)
    if saved_mission['locked'] != 0:
        print(f"  ❌ ERROR: Mission saved with locked={saved_mission['locked']} (should be 0)")
        return False
    print("  ✓ Mission saved with locked=0")
    
    # Pair 1 gets the mission
    mission_pair1 = await db.get_mission("killteam")
    if not mission_pair1:
        print("  ❌ ERROR: Cannot find the mission we just created")
        return False
    print(f"  ✓ Pair 1 retrieved mission ID: {mission_pair1.get('id', 'N/A')}")
    
    # Lock the mission (assigned to Pair 1)
    await db.lock_mission(mission_id_1)
    print(f"  ✓ Mission {mission_id_1} locked for Pair 1")
    
    # Verify mission is now locked
    locked_mission = db.MOCK_MISSIONS.get(mission_id_1)
    if locked_mission['locked'] != 1:
        print(f"  ❌ ERROR: Mission not locked (locked={locked_mission['locked']})")
        return False
    print("  ✓ Mission now has locked=1")
    
    # === PAIR 2: Second pair starts 10 minutes later (Time: T+10min) ===
    print("\n[TIME T+10min] Pair 2 starts playing...")
    
    # Pair 2 requests a killteam mission
    mission_pair2 = await db.get_mission("killteam")
    
    if mission_pair2:
        # This is the BUG! They got the same mission as Pair 1
        if mission_pair2.get('id') == mission_id_1:
            print(f"  ❌ BUG DETECTED: Pair 2 got same mission as Pair 1 (ID: {mission_id_1})")
            print("  This is the bug described in the issue!")
            return False
        else:
            print(f"  ⚠️  Pair 2 found a different unlocked mission (ID: {mission_pair2.get('id')})")
    else:
        print("  ✓ No unlocked missions found for Pair 2 (correct - Pair 1's mission is locked)")
    
    # Generate new mission for Pair 2
    print("  → Generating new mission for Pair 2...")
    mission_data_2 = ("Loot", "killteam", None, "Collect resources", None)
    mission_id_2 = await db.save_mission(mission_data_2)
    print(f"  ✓ Created mission ID: {mission_id_2}")
    
    # Verify it's a different mission
    if mission_id_2 == mission_id_1:
        print("  ❌ ERROR: Same mission ID as Pair 1!")
        return False
    print(f"  ✓ Different mission ID (Pair 1: {mission_id_1}, Pair 2: {mission_id_2})")
    
    print("\n" + "=" * 70)
    print("✅ TEST PASSED: Mission blocking is working correctly!")
    print("=" * 70)
    print("\nSummary:")
    print(f"  • Pair 1 got mission {mission_id_1} (locked)")
    print(f"  • Pair 2 got mission {mission_id_2} (new mission)")
    print("  • No duplicate missions assigned ✓")
    
    return True


async def test_mission_unlocking_flow():
    """
    Test that missions are saved unlocked and can be locked later.
    """
    print("\n" + "=" * 70)
    print("TEST: Mission locking/unlocking flow")
    print("=" * 70)
    
    # Reset mock data
    db.MOCK_MISSIONS.clear()
    
    # Create a mission
    mission_data = ("Test", "wh40k", None, "Test mission", "Test bonus")
    mission_id = await db.save_mission(mission_data)
    
    # Check it's unlocked
    mission = db.MOCK_MISSIONS.get(mission_id)
    assert mission['locked'] == 0, "Mission should be saved as unlocked"
    print(f"✓ Mission {mission_id} saved with locked=0")
    
    # Verify we can find it
    found = await db.get_mission("wh40k")
    assert found is not None, "Should find unlocked mission"
    print(f"✓ Found unlocked mission")
    
    # Lock it
    await db.lock_mission(mission_id)
    mission = db.MOCK_MISSIONS.get(mission_id)
    assert mission['locked'] == 1, "Mission should be locked"
    print(f"✓ Mission {mission_id} locked")
    
    # Verify we can't find it anymore
    found = await db.get_mission("wh40k")
    assert found is None, "Should not find locked mission"
    print(f"✓ Locked mission not returned by get_mission")
    
    print("\n✅ Mission locking flow works correctly!")
    return True


async def main():
    """Run all integration tests."""
    print("\n" + "=" * 70)
    print("Mission Blocking Fix - Integration Tests")
    print("=" * 70)
    print("\nThis tests the fix for the issue:")
    print("  'блокировние миссий' - Mission blocking issue")
    print("\nProblem: Two pairs starting 10 minutes apart got same mission")
    print("Fix: Save missions with locked=0, lock them when assigned")
    
    tests = [
        ("Mission blocking scenario", test_mission_blocking_scenario),
        ("Mission locking flow", test_mission_unlocking_flow),
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = await test_func()
            results.append(result)
        except AssertionError as e:
            print(f"\n❌ TEST FAILED: {test_name}")
            print(f"   Assertion: {e}")
            results.append(False)
        except Exception as e:
            print(f"\n❌ TEST ERROR: {test_name}")
            print(f"   Error: {e}")
            import traceback
            traceback.print_exc()
            results.append(False)
    
    print("\n" + "=" * 70)
    passed = sum(results)
    total = len(results)
    
    if passed == total:
        print(f"✅ ALL TESTS PASSED ({passed}/{total})")
        print("\n🎉 The mission blocking issue is FIXED!")
        print("\nWhat the fix does:")
        print("  1. New missions are saved with locked=0 (unlocked)")
        print("  2. get_mission finds only unlocked missions")
        print("  3. Missions are locked when assigned to players")
        print("  4. Locked missions won't be reused by other players")
        print("\nThis prevents the bug where two pairs got the same mission.")
        return 0
    else:
        print(f"❌ TESTS FAILED ({total-passed}/{total} failures)")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
