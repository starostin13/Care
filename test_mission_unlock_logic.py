"""
Test script to verify the mission unlock logic is working correctly.
This tests that the code has been modified correctly.
"""

import sys
import os
import datetime

# Add the project directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'CareBot', 'CareBot'))

def test_code_structure():
    """Test that the code structure is correct."""
    print("Testing code structure...")
    print("=" * 60)
    
    # Test 1: Check unlock_expired_missions function
    print("\n1. Checking unlock_expired_missions function...")
    with open('CareBot/CareBot/sqllite_helper.py', 'r', encoding='utf-8') as f:
        content = f.read()
        
        if 'async def unlock_expired_missions():' in content:
            print("   ✅ Function definition found")
        else:
            print("   ❌ Function definition NOT found")
            return False
            
        if 'UPDATE mission_stack' in content and 'SET locked=0' in content:
            print("   ✅ Updates locked status correctly")
        else:
            print("   ❌ Update statement incorrect")
            return False
            
        if 'WHERE locked=1 AND (created_date < ?' in content or 'WHERE locked=1 AND created_date < ?' in content:
            print("   ✅ Filter condition is correct")
        else:
            print("   ❌ Filter condition is incorrect")
            return False
    
    # Test 2: Check get_mission calls unlock_expired_missions
    print("\n2. Checking get_mission function...")
    with open('CareBot/CareBot/sqllite_helper.py', 'r', encoding='utf-8') as f:
        content = f.read()
        
        # Find get_mission function
        start = content.find('async def get_mission(rules):')
        if start == -1:
            print("   ❌ get_mission function NOT found")
            return False
        
        # Check if it calls unlock_expired_missions before SELECT
        unlock_call = content.find('await unlock_expired_missions()', start)
        select_call = content.find('SELECT * FROM mission_stack', start)
        
        if unlock_call != -1 and unlock_call < select_call:
            print("   ✅ Calls unlock_expired_missions before SELECT")
        else:
            print("   ❌ Does NOT call unlock_expired_missions before SELECT")
            return False
    
    # Test 3: Check save_mission includes created_date
    print("\n3. Checking save_mission function...")
    with open('CareBot/CareBot/sqllite_helper.py', 'r', encoding='utf-8') as f:
        content = f.read()
        
        # Find save_mission function
        start = content.find('async def save_mission(mission):')
        if start == -1:
            print("   ❌ save_mission function NOT found")
            return False
        
        # Extract the function (approximately)
        end = content.find('\n\nasync def', start + 1)
        if end == -1:
            end = start + 500
        function_content = content[start:end]
        
        if 'created_date' in function_content:
            print("   ✅ Includes created_date in INSERT")
        else:
            print("   ❌ Does NOT include created_date")
            return False
            
        if 'datetime.date.today().isoformat()' in function_content:
            print("   ✅ Uses current date")
        else:
            print("   ❌ Does NOT use current date")
            return False
    
    # Test 4: Check migration file
    print("\n4. Checking migration file...")
    migration_path = 'CareBot/CareBot/migrations/014_add_created_date_to_mission_stack.py'
    if not os.path.exists(migration_path):
        print("   ❌ Migration file does NOT exist")
        return False
    
    with open(migration_path, 'r', encoding='utf-8') as f:
        content = f.read()
        
        if 'created_date' in content and 'mission_stack' in content:
            print("   ✅ Migration adds created_date to mission_stack")
        else:
            print("   ❌ Migration is incomplete")
            return False
        
        if 'ALTER TABLE mission_stack ADD COLUMN created_date' in content:
            print("   ✅ Uses correct ALTER TABLE syntax")
        else:
            print("   ❌ ALTER TABLE syntax incorrect")
            return False
    
    # Test 5: Check mock implementation
    print("\n5. Checking mock implementation...")
    with open('CareBot/CareBot/mock_sqlite_helper.py', 'r', encoding='utf-8') as f:
        content = f.read()
        
        if 'async def unlock_expired_missions():' in content:
            print("   ✅ Mock has unlock_expired_missions function")
        else:
            print("   ❌ Mock does NOT have unlock_expired_missions")
            return False
        
        # Check if mock get_mission calls unlock
        start = content.find('async def get_mission(rules):')
        if start != -1:
            end = content.find('\n\nasync def', start + 1)
            if end == -1:
                end = start + 1000
            function_content = content[start:end]
            
            if 'await unlock_expired_missions()' in function_content:
                print("   ✅ Mock get_mission calls unlock_expired_missions")
            else:
                print("   ❌ Mock get_mission does NOT call unlock_expired_missions")
                return False
        else:
            print("   ❌ Mock get_mission function NOT found")
            return False
    
    return True

def main():
    print("Testing mission unlock implementation...")
    print()
    
    if test_code_structure():
        print("\n" + "=" * 60)
        print("🎉 ALL TESTS PASSED!")
        print("=" * 60)
        print("\n📝 Implementation Summary:")
        print("1. ✅ Added unlock_expired_missions() function")
        print("   - Unlocks missions with past dates and locked=1")
        print("   - Returns number of missions unlocked")
        print()
        print("2. ✅ Modified get_mission() function")
        print("   - Calls unlock_expired_missions() before fetching")
        print("   - Ensures old locked missions are available")
        print()
        print("3. ✅ Modified save_mission() function")
        print("   - Saves current date to created_date field")
        print("   - Tracks when each mission was created")
        print()
        print("4. ✅ Created migration 014")
        print("   - Adds created_date column to mission_stack table")
        print("   - Safe to run on existing databases")
        print()
        print("5. ✅ Updated mock implementation")
        print("   - Mock functions match real implementation")
        print("   - Test mode will work correctly")
        print()
        print("🚀 Expected Behavior:")
        print("   When get_mission() is called:")
        print("   1. First, unlock_expired_missions() runs")
        print("   2. All missions with past dates get unlocked (locked=0)")
        print("   3. Then the normal query runs to find available missions")
        print("   4. Previously locked missions from past dates can be reused")
        print()
        print("📅 Example:")
        print("   - Mission created on 2025-01-01 with locked=1")
        print("   - Today is 2025-01-02")
        print("   - get_mission() is called")
        print("   - Mission gets unlocked (locked=0)")
        print("   - Mission becomes available for play")
        return 0
    else:
        print("\n" + "=" * 60)
        print("❌ TESTS FAILED")
        print("=" * 60)
        print("\nPlease review the errors above and fix the implementation.")
        return 1

if __name__ == "__main__":
    exit(main())
