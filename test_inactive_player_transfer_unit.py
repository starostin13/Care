#!/usr/bin/env python3
"""
Simple unit test for inactive player transfer feature.
Tests the code structure without requiring a database.
"""

import asyncio
import sys
import os

# Add the CareBot directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'CareBot', 'CareBot'))

# Set test mode to use mock helpers
os.environ['CAREBOT_TEST_MODE'] = 'true'
import config
config.TEST_MODE = True

import mock_sqlite_helper as sqllite_helper
import warmaster_helper


async def test_mock_functions_exist():
    """Test that all new mock functions exist and can be called."""
    print("=" * 60)
    print("Testing Mock Functions")
    print("=" * 60)
    
    tests_passed = 0
    tests_total = 0
    
    # Test update_last_active
    tests_total += 1
    try:
        await sqllite_helper.update_last_active('123456789')
        print("✅ update_last_active() works")
        tests_passed += 1
    except Exception as e:
        print(f"❌ update_last_active() failed: {e}")
    
    # Test get_alliance_average_inactivity_days
    tests_total += 1
    try:
        result = await sqllite_helper.get_alliance_average_inactivity_days(1)
        print(f"✅ get_alliance_average_inactivity_days() works, returned: {result}")
        tests_passed += 1
    except Exception as e:
        print(f"❌ get_alliance_average_inactivity_days() failed: {e}")
    
    # Test get_inactive_players_in_alliance
    tests_total += 1
    try:
        result = await sqllite_helper.get_inactive_players_in_alliance(1, 2.0)
        print(f"✅ get_inactive_players_in_alliance() works, returned: {result}")
        tests_passed += 1
    except Exception as e:
        print(f"❌ get_inactive_players_in_alliance() failed: {e}")
    
    # Test get_all_admins
    tests_total += 1
    try:
        result = await sqllite_helper.get_all_admins()
        print(f"✅ get_all_admins() works, returned: {result}")
        tests_passed += 1
    except Exception as e:
        print(f"❌ get_all_admins() failed: {e}")
    
    # Test get_player_last_active
    tests_total += 1
    try:
        result = await sqllite_helper.get_player_last_active('123456789')
        print(f"✅ get_player_last_active() works, returned: {result}")
        tests_passed += 1
    except Exception as e:
        print(f"❌ get_player_last_active() failed: {e}")
    
    # Test transfer_inactive_player
    tests_total += 1
    try:
        result = await sqllite_helper.transfer_inactive_player('123456789', 1, 2)
        print(f"✅ transfer_inactive_player() works, returned: {result}")
        tests_passed += 1
    except Exception as e:
        print(f"❌ transfer_inactive_player() failed: {e}")
    
    # Test get_target_alliance_for_inactive_player
    tests_total += 1
    try:
        result = await sqllite_helper.get_target_alliance_for_inactive_player(1)
        print(f"✅ get_target_alliance_for_inactive_player() works, returned: {result}")
        tests_passed += 1
    except Exception as e:
        print(f"❌ get_target_alliance_for_inactive_player() failed: {e}")
    
    print(f"\nPassed: {tests_passed}/{tests_total}")
    return tests_passed == tests_total


async def test_warmaster_helper_function():
    """Test that the warmaster helper function exists."""
    print("\n" + "=" * 60)
    print("Testing Warmaster Helper Function")
    print("=" * 60)
    
    try:
        # Create a mock context
        class MockContext:
            class MockBot:
                async def send_message(self, chat_id, text):
                    print(f"  [Mock] Would send message to {chat_id}: {text[:50]}...")
            bot = MockBot()
        
        context = MockContext()
        
        # Call the function
        result = await warmaster_helper.check_and_transfer_inactive_players(context, 2.0)
        
        print(f"✅ check_and_transfer_inactive_players() works")
        print(f"   Result: {result}")
        return True
    except Exception as e:
        print(f"❌ check_and_transfer_inactive_players() failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_code_structure():
    """Verify the code structure is correct."""
    print("\n" + "=" * 60)
    print("Testing Code Structure")
    print("=" * 60)
    
    # Import notification_service
    import notification_service
    
    # Check that the notification function exists
    if hasattr(notification_service, 'notify_inactive_player_transfer'):
        print("✅ notify_inactive_player_transfer() function exists in notification_service")
    else:
        print("❌ notify_inactive_player_transfer() function not found in notification_service")
        return False
    
    # Check that mission_helper has been updated (indirectly through import)
    import mission_helper
    print("✅ mission_helper imports successfully")
    
    return True


async def main():
    """Run all tests."""
    print("\n🧪 Starting Inactive Player Transfer Feature Unit Tests\n")
    
    tests = [
        ("Mock Functions", test_mock_functions_exist),
        ("Warmaster Helper Function", test_warmaster_helper_function),
        ("Code Structure", test_code_structure),
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            result = await test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"\n❌ Error in {test_name}: {e}")
            import traceback
            traceback.print_exc()
            results.append((test_name, False))
    
    # Summary
    print("\n" + "=" * 60)
    print("Test Summary")
    print("=" * 60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status}: {test_name}")
    
    print(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 All tests passed!")
        return 0
    else:
        print(f"\n⚠️  {total - passed} test(s) failed")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
