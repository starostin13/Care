#!/usr/bin/env python3
"""Test script to verify back button handler exists and is registered in code"""

import sys
import os
import re

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

# Set environment variable before importing modules
os.environ['CAREBOT_TEST_MODE'] = 'true'

def test_back_button_handler():
    """Test that the back_to_games handler exists and is registered."""
    
    print("=== Testing Back Button Handler Registration ===\n")
    
    # Read handlers.py file
    handlers_path = os.path.join(os.path.dirname(__file__), 'CareBot', 'CareBot', 'handlers.py')
    with open(handlers_path, 'r') as f:
        handlers_content = f.read()
    
    # Check if back_to_games function exists
    if re.search(r'async def back_to_games\(', handlers_content):
        print("✅ back_to_games function definition found")
    else:
        print("❌ FAIL: back_to_games function not found")
        return False
    
    # Check if the function returns GAMES
    if re.search(r'return GAMES', handlers_content[handlers_content.find('async def back_to_games'):]):
        print("✅ back_to_games returns GAMES state")
    else:
        print("⚠️  WARNING: Could not verify return value")
    
    # Check if handler is registered in SCHEDULE state
    if re.search(r'CallbackQueryHandler\(back_to_games.*pattern.*back_to_games', handlers_content):
        print("✅ back_to_games handler registered in conversation handler")
    else:
        print("❌ FAIL: back_to_games handler not registered")
        return False
    
    # Check if it's in SCHEDULE state section
    schedule_section_match = re.search(r'SCHEDULE:\s*\[(.*?)\]', handlers_content, re.DOTALL)
    if schedule_section_match:
        schedule_section = schedule_section_match.group(1)
        if 'back_to_games' in schedule_section:
            print("✅ back_to_games handler is in SCHEDULE state")
        else:
            print("❌ FAIL: back_to_games handler not in SCHEDULE state")
            return False
    
    # Try to import the function
    try:
        from handlers import back_to_games, SCHEDULE, GAMES
        print(f"\n✅ Successfully imported back_to_games function")
        print(f"   SCHEDULE state value: {SCHEDULE}")
        print(f"   GAMES state value: {GAMES}")
        
        # Check function signature
        import inspect
        sig = inspect.signature(back_to_games)
        print(f"   Function signature: {sig}")
        
    except ImportError as e:
        print(f"\n❌ FAIL: Cannot import back_to_games function: {e}")
        return False
    
    print("\n✅ SUCCESS: All checks passed!")
    return True

if __name__ == "__main__":
    success = test_back_button_handler()
    sys.exit(0 if success else 1)
