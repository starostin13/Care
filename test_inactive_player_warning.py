#!/usr/bin/env python3
"""
Test script to verify inactive player warning functionality.
Tests that the system can find the least recently active player and send warnings.
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
import notification_service


async def test_get_least_active_player():
    """Test getting least recently active player."""
    print("=" * 60)
    print("Testing Get Least Recently Active Player")
    print("=" * 60)
    
    try:
        result = await sqllite_helper.get_least_recently_active_player()
        print(f"✅ get_least_recently_active_player() works, returned: {result}")
        return True
    except Exception as e:
        print(f"❌ get_least_recently_active_player() failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_get_all_admins():
    """Test getting all admins."""
    print("\n" + "=" * 60)
    print("Testing Get All Admins")
    print("=" * 60)
    
    try:
        result = await sqllite_helper.get_all_admins()
        print(f"✅ get_all_admins() works, returned: {result}")
        return True
    except Exception as e:
        print(f"❌ get_all_admins() failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_notification_function():
    """Test the notification function."""
    print("\n" + "=" * 60)
    print("Testing Notification Function")
    print("=" * 60)
    
    try:
        # Create a mock context
        class MockContext:
            class MockBot:
                async def send_message(self, chat_id, text):
                    print(f"  [Mock] Would send message to {chat_id}:")
                    print(f"    {text[:100]}...")
            bot = MockBot()
        
        context = MockContext()
        
        # Call the notification function
        await notification_service.notify_inactive_player_warning(
            context,
            player_telegram_id='123456789',
            player_name='Test Player',
            player_contact='+79123456789'
        )
        
        print("✅ notify_inactive_player_warning() works")
        return True
    except Exception as e:
        print(f"❌ notify_inactive_player_warning() failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """Run all tests."""
    print("\n🧪 Starting Inactive Player Warning Tests\n")
    
    tests = [
        ("Get Least Active Player", test_get_least_active_player),
        ("Get All Admins", test_get_all_admins),
        ("Notification Function", test_notification_function),
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
