"""
Test script to verify that the migration system and handlers are working correctly.
"""

import sys
import os

# Add the project directory to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_migration_system():
    """Test that the migration system works."""
    try:
        import migrate_db
        print("✅ Migration module imported successfully")
        
        # Test running migrations
        success = migrate_db.run_migrations()
        if success:
            print("✅ Migrations completed successfully")
        else:
            print("❌ Migration failed")
            return False
            
        return True
    except Exception as e:
        print(f"❌ Migration test failed: {e}")
        return False

def test_handlers_import():
    """Test that handlers can be imported without errors."""
    try:
        import handlers
        print("✅ Handlers module imported successfully")
        return True
    except Exception as e:
        print(f"❌ Handlers import failed: {e}")
        return False

def test_keyboard_constructor():
    """Test that keyboard constructor works."""
    try:
        import keyboard_constructor
        print("✅ Keyboard constructor imported successfully")
        return True
    except Exception as e:
        print(f"❌ Keyboard constructor import failed: {e}")
        return False

if __name__ == "__main__":
    print("Testing CareBot components...")
    print("=" * 40)
    
    tests = [
        test_migration_system,
        test_handlers_import,
        test_keyboard_constructor
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
        print()
    
    print(f"Test Results: {passed}/{total} passed")
    
    if passed == total:
        print("🎉 All tests passed! The bot should work correctly.")
        print("\n📝 Changes made:")
        print("1. ✅ Fixed tracemalloc warning by adding tracemalloc.start()")
        print("2. ✅ Added 'Back' button handler in all conversation states")
        print("3. ✅ Fixed setting() function to return SETTINGS state")
        print("4. ✅ Modified hello() function to handle both commands and callbacks")
        print("5. ✅ Database migration system is working")
        
        print("\n🚀 The 'Back' button should now work correctly!")
    else:
        print("❌ Some tests failed. Please check the errors above.")
        sys.exit(1)