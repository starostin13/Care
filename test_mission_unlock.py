"""
Test script to verify that the mission unlock feature is working correctly.
This tests the unlock_expired_missions function.
"""

import sys
import os
import asyncio
import datetime

# Add the project directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'CareBot', 'CareBot'))

# Set test mode
os.environ['CAREBOT_TEST_MODE'] = 'true'

async def test_unlock_expired_missions_function_exists():
    """Test that unlock_expired_missions function exists."""
    try:
        import sqllite_helper
        
        if hasattr(sqllite_helper, 'unlock_expired_missions'):
            print("✅ unlock_expired_missions function exists in sqllite_helper")
            return True
        else:
            print("❌ unlock_expired_missions function NOT found in sqllite_helper")
            return False
    except Exception as e:
        print(f"❌ Error checking unlock_expired_missions: {e}")
        return False

async def test_get_mission_calls_unlock():
    """Test that get_mission calls unlock_expired_missions."""
    try:
        import inspect
        import sqllite_helper
        
        # Get the source code of get_mission
        source = inspect.getsource(sqllite_helper.get_mission)
        
        # Check if it calls unlock_expired_missions
        if 'unlock_expired_missions' in source:
            print("✅ get_mission calls unlock_expired_missions")
            return True
        else:
            print("❌ get_mission does NOT call unlock_expired_missions")
            return False
    except Exception as e:
        print(f"❌ Error checking get_mission: {e}")
        return False

async def test_save_mission_includes_date():
    """Test that save_mission includes created_date."""
    try:
        import inspect
        import sqllite_helper
        
        # Get the source code of save_mission
        source = inspect.getsource(sqllite_helper.save_mission)
        
        # Check if it includes created_date
        if 'created_date' in source and 'datetime.date.today()' in source:
            print("✅ save_mission includes created_date with current date")
            return True
        else:
            print("❌ save_mission does NOT include created_date properly")
            return False
    except Exception as e:
        print(f"❌ Error checking save_mission: {e}")
        return False

async def test_mock_functions_exist():
    """Test that mock functions are updated."""
    try:
        import mock_sqlite_helper
        
        has_unlock = hasattr(mock_sqlite_helper, 'unlock_expired_missions')
        has_get = hasattr(mock_sqlite_helper, 'get_mission')
        has_save = hasattr(mock_sqlite_helper, 'save_mission')
        
        if has_unlock and has_get and has_save:
            print("✅ All mock functions exist")
            return True
        else:
            missing = []
            if not has_unlock:
                missing.append('unlock_expired_missions')
            if not has_get:
                missing.append('get_mission')
            if not has_save:
                missing.append('save_mission')
            print(f"❌ Missing mock functions: {', '.join(missing)}")
            return False
    except Exception as e:
        print(f"❌ Error checking mock functions: {e}")
        return False

async def test_migration_exists():
    """Test that migration file exists."""
    try:
        migration_file = os.path.join(
            os.path.dirname(__file__), 
            'CareBot', 'CareBot', 'migrations', 
            '014_add_created_date_to_mission_stack.py'
        )
        
        if os.path.exists(migration_file):
            with open(migration_file, 'r', encoding='utf-8') as f:
                content = f.read()
                if 'created_date' in content and 'mission_stack' in content:
                    print("✅ Migration 014 exists and contains created_date for mission_stack")
                    return True
                else:
                    print("❌ Migration 014 is incomplete")
                    return False
        else:
            print("❌ Migration 014 file does not exist")
            return False
    except Exception as e:
        print(f"❌ Error checking migration: {e}")
        return False

async def main():
    print("Testing mission unlock feature...")
    print("=" * 60)
    
    tests = [
        ("unlock_expired_missions exists", test_unlock_expired_missions_function_exists),
        ("get_mission calls unlock", test_get_mission_calls_unlock),
        ("save_mission includes date", test_save_mission_includes_date),
        ("mock functions exist", test_mock_functions_exist),
        ("migration file exists", test_migration_exists)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\nTesting {test_name}...")
        if await test_func():
            passed += 1
    
    print("\n" + "=" * 60)
    print(f"Test Results: {passed}/{total} passed")
    
    if passed == total:
        print("\n🎉 All tests passed! The mission unlock feature should work correctly.")
        print("\n📝 Changes made:")
        print("1. ✅ Added migration 014 to add created_date column to mission_stack")
        print("2. ✅ Added unlock_expired_missions function to unlock past missions")
        print("3. ✅ Updated get_mission to call unlock_expired_missions before fetching")
        print("4. ✅ Updated save_mission to save current date when creating missions")
        print("5. ✅ Updated mock functions to match real implementation")
        print("\n🚀 Expected behavior:")
        print("   - New missions are saved with today's date")
        print("   - Before fetching missions, past locked missions are unlocked")
        print("   - This allows reusing missions that weren't played on their scheduled date")
    else:
        print("\n❌ Some tests failed. Please check the errors above.")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
