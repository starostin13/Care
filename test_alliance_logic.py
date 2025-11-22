#!/usr/bin/env python3
"""
Unit test for alliance auto-deletion logic using mock data.
Tests the basic logic without requiring a real database.
"""

import asyncio
import sys
import os

# Set test mode environment variable BEFORE importing modules
os.environ['CAREBOT_TEST_MODE'] = 'true'

# Add the CareBot directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'CareBot', 'CareBot'))

import mock_sqlite_helper as sqllite_helper


async def test_redistribute_territories():
    """Test territory redistribution logic."""
    print("=" * 60)
    print("Test 1: Territory Redistribution")
    print("=" * 60)
    
    # This uses mock data, so it will return 0 (no territories tracked in mock)
    # but it tests that the function exists and can be called
    territories_moved = await sqllite_helper.redistribute_territories_from_alliance(1)
    print(f"✓ redistribute_territories_from_alliance() can be called")
    print(f"  Mock returned: {territories_moved} territories redistributed")
    return True


async def test_delete_alliance_with_territories():
    """Test that delete_alliance returns territory count."""
    print("\n" + "=" * 60)
    print("Test 2: Alliance Deletion with Territory Info")
    print("=" * 60)
    
    # Get initial state
    alliances = await sqllite_helper.get_all_alliances()
    print(f"\nInitial alliances: {len(alliances)}")
    for alliance_id, alliance_name in alliances:
        player_count = await sqllite_helper.get_alliance_player_count(alliance_id)
        print(f"  - {alliance_name} (ID: {alliance_id}): {player_count} players")
    
    # Create a test alliance
    test_alliance_id = await sqllite_helper.create_alliance("Test Alliance for Deletion")
    if not test_alliance_id:
        print("✗ Failed to create test alliance")
        return False
    
    print(f"\n✓ Created test alliance ID: {test_alliance_id}")
    
    # Delete it
    result = await sqllite_helper.delete_alliance(test_alliance_id)
    
    if not result['success']:
        print(f"✗ Failed to delete alliance: {result['message']}")
        return False
    
    print(f"\n✓ Alliance deleted successfully")
    print(f"  - Players redistributed: {result['players_redistributed']}")
    print(f"  - Territories redistributed: {result['territories_redistributed']}")
    
    # Check that result has all expected fields
    if 'territories_redistributed' not in result:
        print("✗ Result missing 'territories_redistributed' field")
        return False
    
    print("\n✓ Result contains all expected fields")
    return True


async def test_check_and_clean_empty_alliances():
    """Test automatic cleanup of empty alliances."""
    print("\n" + "=" * 60)
    print("Test 3: Automatic Empty Alliance Cleanup")
    print("=" * 60)
    
    # Create empty alliances
    test_alliance_ids = []
    for i in range(2):
        alliance_id = await sqllite_helper.create_alliance(f"Empty Alliance {i+1}")
        if alliance_id:
            test_alliance_ids.append(alliance_id)
            print(f"✓ Created empty alliance ID: {alliance_id}")
    
    if len(test_alliance_ids) != 2:
        print("✗ Failed to create test alliances")
        return False
    
    # Show state before cleanup
    print("\nBefore cleanup:")
    alliances = await sqllite_helper.get_all_alliances()
    for alliance_id, alliance_name in alliances:
        player_count = await sqllite_helper.get_alliance_player_count(alliance_id)
        print(f"  - {alliance_name} (ID: {alliance_id}): {player_count} players")
    
    # Run cleanup
    print("\nRunning auto-cleanup...")
    results = await sqllite_helper.check_and_clean_empty_alliances()
    
    if not results:
        print("✗ No alliances were cleaned up")
        return False
    
    print(f"\n✓ Cleaned up {len(results)} empty alliances")
    for result in results:
        print(f"  - Alliance ID {result['alliance_id']}: {result['alliance_name']}")
        print(f"    Success: {result['result']['success']}")
        if result['result']['success']:
            print(f"    Players: {result['result']['players_redistributed']}")
            print(f"    Territories: {result['result']['territories_redistributed']}")
    
    # Verify alliances were deleted
    print("\nAfter cleanup:")
    alliances_after = await sqllite_helper.get_all_alliances()
    for alliance_id, alliance_name in alliances_after:
        player_count = await sqllite_helper.get_alliance_player_count(alliance_id)
        print(f"  - {alliance_name} (ID: {alliance_id}): {player_count} players")
    
    # Check that empty alliances are gone
    remaining_empty = [aid for aid in test_alliance_ids if any(a[0] == aid for a in alliances_after)]
    if remaining_empty:
        print(f"\n✗ Some empty alliances still exist: {remaining_empty}")
        return False
    
    print("\n✓ All empty alliances were removed")
    return True


async def main():
    """Run all tests."""
    print("\n" + "=" * 60)
    print("Alliance Auto-Deletion Logic Tests (Mock Mode)")
    print("=" * 60)
    print("\nRunning tests using mock data (no database required)...\n")
    
    try:
        test1 = await test_redistribute_territories()
        test2 = await test_delete_alliance_with_territories()
        test3 = await test_check_and_clean_empty_alliances()
        
        print("\n" + "=" * 60)
        print("Test Summary")
        print("=" * 60)
        print(f"Test 1 (Territory Redistribution):     {'✓ PASSED' if test1 else '✗ FAILED'}")
        print(f"Test 2 (Alliance Deletion with Info):  {'✓ PASSED' if test2 else '✗ FAILED'}")
        print(f"Test 3 (Auto-Cleanup):                  {'✓ PASSED' if test3 else '✗ FAILED'}")
        print("=" * 60)
        
        if test1 and test2 and test3:
            print("\n✓ All tests passed!\n")
            return 0
        else:
            print("\n✗ Some tests failed\n")
            return 1
            
    except Exception as e:
        print(f"\n✗ Error during testing: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
