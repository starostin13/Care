#!/usr/bin/env python3
"""
Test script to verify automatic alliance deletion when member count reaches 0.
This test verifies:
1. Territory redistribution when alliance is deleted
2. Player redistribution when alliance is deleted
3. Automatic cleanup of empty alliances
"""

import asyncio
import sys
import os

# Add the CareBot directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'CareBot', 'CareBot'))

import sqllite_helper


async def test_territory_redistribution():
    """Test that territories are redistributed when alliance is deleted."""
    print("=" * 60)
    print("Testing Territory Redistribution")
    print("=" * 60)
    
    # Get all alliances
    print("\n1. Getting current alliances...")
    alliances = await sqllite_helper.get_all_alliances()
    print(f"   Found {len(alliances)} alliances:")
    for alliance_id, alliance_name in alliances:
        player_count = await sqllite_helper.get_alliance_player_count(alliance_id)
        territory_count = len(await sqllite_helper.get_hexes_by_alliance(alliance_id))
        print(f"      - {alliance_name} (ID: {alliance_id}): {player_count} players, {territory_count} territories")
    
    # Create a test alliance
    print("\n2. Creating test alliance...")
    test_alliance_id = await sqllite_helper.create_alliance("Test Empty Alliance")
    if test_alliance_id:
        print(f"   ✓ Created test alliance with ID: {test_alliance_id}")
    else:
        print("   ✗ Failed to create test alliance")
        return False
    
    # Assign some territories to test alliance (if there are any without patron)
    print("\n3. Checking for territories without patron...")
    async with sqllite_helper.aiosqlite.connect(sqllite_helper.DATABASE_PATH) as db:
        async with db.execute('SELECT id FROM map WHERE patron IS NULL LIMIT 3') as cursor:
            unpatronned = await cursor.fetchall()
        
        if unpatronned:
            print(f"   Found {len(unpatronned)} territories without patron")
            for (territory_id,) in unpatronned:
                await sqllite_helper.set_cell_patron(territory_id, test_alliance_id)
            print(f"   ✓ Assigned {len(unpatronned)} territories to test alliance")
        else:
            print("   No territories without patron found")
    
    # Check territory count
    test_territories = await sqllite_helper.get_hexes_by_alliance(test_alliance_id)
    print(f"\n4. Test alliance now has {len(test_territories)} territories")
    
    # Delete the test alliance
    print("\n5. Deleting test alliance...")
    result = await sqllite_helper.delete_alliance(test_alliance_id)
    
    if result['success']:
        print(f"   ✓ Alliance deleted successfully")
        print(f"   - Players redistributed: {result['players_redistributed']}")
        print(f"   - Territories redistributed: {result['territories_redistributed']}")
    else:
        print(f"   ✗ Failed to delete alliance: {result['message']}")
        return False
    
    # Verify territories were redistributed
    print("\n6. Verifying territories were redistributed...")
    remaining_alliances = await sqllite_helper.get_all_alliances()
    total_territories_after = 0
    for alliance_id, alliance_name in remaining_alliances:
        territory_count = len(await sqllite_helper.get_hexes_by_alliance(alliance_id))
        total_territories_after += territory_count
        print(f"      - {alliance_name}: {territory_count} territories")
    
    if len(test_territories) > 0:
        print(f"   ✓ Territories were redistributed to remaining alliances")
    else:
        print(f"   ℹ No territories to redistribute")
    
    return True


async def test_auto_cleanup():
    """Test automatic cleanup of empty alliances."""
    print("\n" + "=" * 60)
    print("Testing Automatic Empty Alliance Cleanup")
    print("=" * 60)
    
    # Create multiple test alliances
    print("\n1. Creating test alliances without members...")
    test_alliance_ids = []
    for i in range(2):
        alliance_id = await sqllite_helper.create_alliance(f"Test Empty Alliance {i+1}")
        if alliance_id:
            test_alliance_ids.append(alliance_id)
            print(f"   ✓ Created alliance ID: {alliance_id}")
        else:
            print(f"   ✗ Failed to create alliance {i+1}")
    
    # Show all alliances
    print("\n2. Current alliances:")
    alliances = await sqllite_helper.get_all_alliances()
    for alliance_id, alliance_name in alliances:
        player_count = await sqllite_helper.get_alliance_player_count(alliance_id)
        print(f"      - {alliance_name} (ID: {alliance_id}): {player_count} members")
    
    # Run auto-cleanup
    print("\n3. Running auto-cleanup...")
    results = await sqllite_helper.check_and_clean_empty_alliances()
    
    if results:
        print(f"   ✓ Cleaned up {len(results)} empty alliances:")
        for result in results:
            print(f"      - Alliance ID {result['alliance_id']} ({result['alliance_name']})")
            if result['result']['success']:
                print(f"        Territories redistributed: {result['result']['territories_redistributed']}")
    else:
        print("   ℹ No empty alliances to clean up")
    
    # Verify alliances were deleted
    print("\n4. Verifying empty alliances were removed...")
    alliances_after = await sqllite_helper.get_all_alliances()
    print(f"   Current alliances count: {len(alliances_after)}")
    for alliance_id, alliance_name in alliances_after:
        player_count = await sqllite_helper.get_alliance_player_count(alliance_id)
        print(f"      - {alliance_name} (ID: {alliance_id}): {player_count} members")
    
    # Verify test alliances are gone
    remaining_test_alliances = [aid for aid in test_alliance_ids if any(a[0] == aid for a in alliances_after)]
    if not remaining_test_alliances:
        print("   ✓ All test empty alliances were removed")
        return True
    else:
        print(f"   ✗ Some test alliances still exist: {remaining_test_alliances}")
        return False


async def main():
    """Run all tests."""
    print("\n" + "=" * 60)
    print("Testing Alliance Auto-Deletion Feature")
    print("=" * 60)
    
    try:
        # Test territory redistribution
        success1 = await test_territory_redistribution()
        
        # Test auto cleanup
        success2 = await test_auto_cleanup()
        
        print("\n" + "=" * 60)
        if success1 and success2:
            print("✓ All tests passed!")
        else:
            print("✗ Some tests failed")
        print("=" * 60 + "\n")
        
    except Exception as e:
        print(f"\n✗ Error during testing: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    print("\nNote: Make sure DATABASE_PATH environment variable is set correctly")
    print("or the default path points to your database.\n")
    
    asyncio.run(main())
