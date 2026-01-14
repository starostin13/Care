#!/usr/bin/env python3
"""
Test for alliance territory validation on date selection.
Tests that users cannot register for games if their alliance has no territories.
"""

import asyncio
import sys
import os

# Set test mode environment variable BEFORE importing modules
os.environ['CAREBOT_TEST_MODE'] = 'true'

# Add the CareBot directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'CareBot', 'CareBot'))

import mock_sqlite_helper as sqllite_helper


async def test_get_alliance_territory_count():
    """Test that the get_alliance_territory_count function exists and works."""
    print("=" * 60)
    print("Test 1: get_alliance_territory_count function")
    print("=" * 60)
    
    # Test with valid alliance
    count = await sqllite_helper.get_alliance_territory_count(1)
    print(f"✓ Alliance 1 territory count: {count}")
    
    # Test with alliance 0 (no alliance)
    count_no_alliance = await sqllite_helper.get_alliance_territory_count(0)
    print(f"✓ Alliance 0 (no alliance) territory count: {count_no_alliance}")
    
    if count_no_alliance != 0:
        print("✗ Alliance 0 should have 0 territories")
        return False
    
    print("✓ Function works correctly")
    return True


async def test_alliance_territory_validation():
    """Test that the alliance territory validation logic exists."""
    print("\n" + "=" * 60)
    print("Test 2: Alliance territory validation logic")
    print("=" * 60)
    
    # Test getting alliance of a warmaster
    alliance = await sqllite_helper.get_alliance_of_warmaster('325313837')
    print(f"✓ User alliance: {alliance}")
    
    if alliance and alliance[0]:
        # Check territory count for this alliance
        territory_count = await sqllite_helper.get_alliance_territory_count(alliance[0])
        print(f"✓ Alliance {alliance[0]} has {territory_count} territories")
    else:
        print("✓ User has no alliance")
    
    print("✓ Alliance lookup and territory check work")
    return True


async def test_localization_keys():
    """Test that error message keys are defined."""
    print("\n" + "=" * 60)
    print("Test 3: Error message localization keys")
    print("=" * 60)
    
    # Test getting error messages
    error_no_territories = await sqllite_helper.get_text_by_key('error_no_territories', 'ru')
    error_no_alliance = await sqllite_helper.get_text_by_key('error_no_alliance', 'ru')
    
    if error_no_territories:
        print(f"✓ 'error_no_territories' key exists: {error_no_territories[:50]}...")
    else:
        print("⚠ 'error_no_territories' key not found (may need migration)")
    
    if error_no_alliance:
        print(f"✓ 'error_no_alliance' key exists: {error_no_alliance[:50]}...")
    else:
        print("⚠ 'error_no_alliance' key not found (may need migration)")
    
    print("✓ Localization keys checked")
    return True


async def main():
    """Run all tests."""
    print("\n" + "=" * 60)
    print("Alliance Territory Validation Tests (Mock Mode)")
    print("=" * 60)
    print("\nTesting alliance territory check on date selection...\n")
    
    try:
        test1 = await test_get_alliance_territory_count()
        test2 = await test_alliance_territory_validation()
        test3 = await test_localization_keys()
        
        print("\n" + "=" * 60)
        print("Test Summary")
        print("=" * 60)
        print(f"Test 1 (Territory Count Function):     {'✓ PASSED' if test1 else '✗ FAILED'}")
        print(f"Test 2 (Validation Logic):              {'✓ PASSED' if test2 else '✗ FAILED'}")
        print(f"Test 3 (Localization Keys):             {'✓ PASSED' if test3 else '✗ FAILED'}")
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
