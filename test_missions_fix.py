"""
Test script to verify that the missions fix is working correctly.
"""

import sys
import os
import asyncio

# Add the project directory to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

async def test_sqllite_helper_import():
    """Test that sqllite_helper is imported in keyboard_constructor."""
    try:
        import keyboard_constructor
        # Check if sqllite_helper is imported
        if hasattr(keyboard_constructor, 'sqllite_helper'):
            print("✅ sqllite_helper is imported in keyboard_constructor")
            return True
        else:
            # Check in the module's globals
            import inspect
            source = inspect.getsource(keyboard_constructor)
            if 'import sqllite_helper' in source:
                print("✅ sqllite_helper is imported in keyboard_constructor")
                return True
            else:
                print("❌ sqllite_helper is NOT imported in keyboard_constructor")
                return False
    except Exception as e:
        print(f"❌ Error checking sqllite_helper import: {e}")
        return False

async def test_today_schedule_function():
    """Test that today_schedule function calls get_schedule_with_warmasters."""
    try:
        import keyboard_constructor
        import inspect
        
        # Get the source code of today_schedule
        source = inspect.getsource(keyboard_constructor.today_schedule)
        
        # Check if the function calls get_schedule_with_warmasters
        if 'get_schedule_with_warmasters' in source and '# ' not in source.split('get_schedule_with_warmasters')[0].split('\n')[-1]:
            print("✅ today_schedule calls get_schedule_with_warmasters (not commented)")
            return True
        else:
            print("❌ today_schedule does NOT call get_schedule_with_warmasters or it's commented")
            return False
    except Exception as e:
        print(f"❌ Error checking today_schedule function: {e}")
        return False

async def test_missions_title_exists():
    """Test that missions_title localization exists in migration."""
    try:
        import os
        migration_file = os.path.join(os.path.dirname(__file__), 'migrations', '007_add_missions_title_text.py')
        
        if os.path.exists(migration_file):
            with open(migration_file, 'r', encoding='utf-8') as f:
                content = f.read()
                if 'missions_title' in content and 'Выберите оппонента' in content:
                    print("✅ missions_title localization exists in migration 007")
                    return True
                else:
                    print("❌ missions_title localization is incomplete in migration 007")
                    return False
        else:
            print("❌ Migration 007 file does not exist")
            return False
    except Exception as e:
        print(f"❌ Error checking missions_title migration: {e}")
        return False

async def test_show_missions_handler():
    """Test that show_missions handler uses missions_title."""
    try:
        # Read the file directly instead of importing to avoid database issues
        import os
        handlers_file = os.path.join(os.path.dirname(__file__), 'handlers.py')
        
        with open(handlers_file, 'r', encoding='utf-8') as f:
            source = f.read()
        
        # Find the show_missions function
        if 'async def show_missions' in source:
            # Extract the function
            start = source.find('async def show_missions')
            end = source.find('\nasync def ', start + 1)
            if end == -1:
                end = len(source)
            function_source = source[start:end]
            
            # Check if it uses missions_title instead of appointments_title
            if 'missions_title' in function_source and 'appointments_title' not in function_source:
                print("✅ show_missions handler uses missions_title (not appointments_title)")
                return True
            elif 'appointments_title' in function_source:
                print("❌ show_missions handler still uses appointments_title")
                return False
            else:
                print("❌ show_missions handler doesn't use any title")
                return False
        else:
            print("❌ show_missions function not found")
            return False
    except Exception as e:
        print(f"❌ Error checking show_missions handler: {e}")
        return False

async def main():
    print("Testing missions fix...")
    print("=" * 60)
    
    tests = [
        ("sqllite_helper import", test_sqllite_helper_import),
        ("today_schedule function", test_today_schedule_function),
        ("missions_title localization", test_missions_title_exists),
        ("show_missions handler", test_show_missions_handler)
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
        print("\n🎉 All tests passed! The missions fix should work correctly.")
        print("\n📝 Changes made:")
        print("1. ✅ Added sqllite_helper import to keyboard_constructor.py")
        print("2. ✅ Uncommented get_schedule_with_warmasters call in today_schedule")
        print("3. ✅ Added missions_title localization in migration 007")
        print("4. ✅ Updated show_missions to use missions_title instead of appointments_title")
        print("\n🚀 When clicking 'Миссии' button, users should now see:")
        print("   - Title: 'Выберите оппонента для игры:' (in Russian)")
        print("   - List of available opponents from scheduled games")
    else:
        print("\n❌ Some tests failed. Please check the errors above.")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
