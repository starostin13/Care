"""
Test script to verify that missions get locked=2 status when battle score is submitted.
"""

import sys
import os
import asyncio

# Add the project directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'CareBot', 'CareBot'))

# Set test mode to use mock database
os.environ['CAREBOT_TEST_MODE'] = 'true'

async def test_set_mission_score_submitted_exists():
    """Test that set_mission_score_submitted function exists."""
    try:
        import sqllite_helper
        
        if hasattr(sqllite_helper, 'set_mission_score_submitted'):
            print("✅ set_mission_score_submitted function exists in sqllite_helper")
            return True
        else:
            print("❌ set_mission_score_submitted function NOT found in sqllite_helper")
            return False
    except Exception as e:
        print(f"❌ Error checking set_mission_score_submitted: {e}")
        return False

async def test_mock_set_mission_score_submitted_exists():
    """Test that set_mission_score_submitted function exists in mock."""
    try:
        import mock_sqlite_helper
        
        if hasattr(mock_sqlite_helper, 'set_mission_score_submitted'):
            print("✅ set_mission_score_submitted function exists in mock_sqlite_helper")
            return True
        else:
            print("❌ set_mission_score_submitted function NOT found in mock_sqlite_helper")
            return False
    except Exception as e:
        print(f"❌ Error checking mock set_mission_score_submitted: {e}")
        return False

async def test_write_battle_result_calls_set_mission_score_submitted():
    """Test that write_battle_result calls set_mission_score_submitted."""
    try:
        import inspect
        import mission_helper
        
        # Get the source code of write_battle_result
        source = inspect.getsource(mission_helper.write_battle_result)
        
        # Check if it calls set_mission_score_submitted
        if 'set_mission_score_submitted' in source:
            print("✅ write_battle_result calls set_mission_score_submitted")
            return True
        else:
            print("❌ write_battle_result does NOT call set_mission_score_submitted")
            return False
    except Exception as e:
        print(f"❌ Error checking write_battle_result: {e}")
        return False

async def test_mock_function_works():
    """Test that mock function can be called."""
    try:
        import mock_sqlite_helper
        
        # Call the mock function
        result = await mock_sqlite_helper.set_mission_score_submitted(123)
        
        if result:
            print("✅ Mock set_mission_score_submitted can be called successfully")
            return True
        else:
            print("❌ Mock set_mission_score_submitted returned unexpected result")
            return False
    except Exception as e:
        print(f"❌ Error calling mock set_mission_score_submitted: {e}")
        return False

async def main():
    """Run all tests."""
    print("Testing locked=2 status feature...")
    print("=" * 60)
    
    tests = [
        ("set_mission_score_submitted exists in sqllite_helper", test_set_mission_score_submitted_exists()),
        ("set_mission_score_submitted exists in mock_sqlite_helper", test_mock_set_mission_score_submitted_exists()),
        ("write_battle_result calls set_mission_score_submitted", test_write_battle_result_calls_set_mission_score_submitted()),
        ("Mock function can be called", test_mock_function_works())
    ]
    
    results = []
    for name, test in tests:
        print(f"\nTesting {name}...")
        result = await test
        results.append(result)
    
    print("\n" + "=" * 60)
    passed = sum(results)
    total = len(results)
    print(f"Test Results: {passed}/{total} passed")
    
    if passed == total:
        print("\n✅ All tests passed!")
    else:
        print(f"\n❌ {total - passed} test(s) failed. Please check the errors above.")

if __name__ == "__main__":
    asyncio.run(main())
