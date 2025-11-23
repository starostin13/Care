#!/usr/bin/env python3
"""Test script to verify back button in day of week selection"""

import asyncio
import sys
import os

# Add the project directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'CareBot', 'CareBot'))

# Create minimal config for testing
config_content = """
TEST_MODE = True
crusade_care_bot_telegram_token = "test_token"
"""

# Write config file if it doesn't exist
config_path = os.path.join(os.path.dirname(__file__), 'CareBot', 'CareBot', 'config.py')
if not os.path.exists(config_path):
    with open(config_path, 'w') as f:
        f.write(config_content)

# Now import the modules
from keyboard_constructor import this_week

async def test_back_button_in_weekday_selection():
    """Test that back button appears in day of week selection keyboard"""
    
    print("=== Testing Back Button in Day of Week Selection ===\n")
    
    # Test with a sample rule
    test_rule = "rule:killteam"
    test_user_id = "test_user_123"
    
    print(f"Testing with rule: {test_rule}")
    print(f"Testing with user_id: {test_user_id}\n")
    
    try:
        # Get the week selection keyboard
        week_keyboard = await this_week(test_rule, test_user_id)
        
        print(f"Number of rows in keyboard: {len(week_keyboard)}")
        
        # Check each row
        for i, row in enumerate(week_keyboard):
            print(f"\nRow {i + 1}:")
            for button in row:
                print(f"  - Button text: '{button.text}'")
                print(f"    Callback data: '{button.callback_data}'")
        
        # Verify back button exists
        last_row = week_keyboard[-1]
        back_button_found = False
        
        for button in last_row:
            if 'back_to_games' in button.callback_data:
                back_button_found = True
                print(f"\n✅ SUCCESS: Back button found!")
                print(f"   Text: '{button.text}'")
                print(f"   Callback: '{button.callback_data}'")
                break
        
        if not back_button_found:
            print("\n❌ FAIL: Back button not found in the keyboard!")
            return False
        
        # Verify we have the expected number of rows (7 days + 1 back button row)
        if len(week_keyboard) == 4:  # 3 rows of dates + 1 row with back button
            print("\n✅ Keyboard structure is correct (4 rows)")
        else:
            print(f"\n⚠️  WARNING: Expected 4 rows, got {len(week_keyboard)}")
        
        return True
        
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(test_back_button_in_weekday_selection())
    sys.exit(0 if success else 1)
