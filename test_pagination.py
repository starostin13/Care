#!/usr/bin/env python3
"""
Test script to verify pagination logic for admin menus.
This tests the keyboard construction functions without running the full bot.
"""

import asyncio
import sys
import os

# Add the CareBot directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'CareBot', 'CareBot'))

# Set test mode before importing modules that depend on config
os.environ['TEST_MODE'] = '1'

import config
config.TEST_MODE = True

import keyboard_constructor
import mock_sqlite_helper as sqllite_helper


async def test_pagination():
    """Test pagination functionality."""
    print("=" * 60)
    print("Testing Pagination for Admin Menus")
    print("=" * 60)
    
    # Test 1: Get warmasters with nicknames
    print("\n1. Testing get_warmasters_with_nicknames()...")
    try:
        warmasters = await sqllite_helper.get_warmasters_with_nicknames()
        print(f"   ✓ Found {len(warmasters)} warmasters with nicknames")
        for wm in warmasters[:5]:  # Show first 5
            telegram_id, nickname, alliance = wm
            print(f"      - {nickname} (ID: {telegram_id}, Alliance: {alliance})")
        if len(warmasters) > 5:
            print(f"      ... and {len(warmasters) - 5} more")
    except Exception as e:
        print(f"   ✗ Error: {e}")
        import traceback
        traceback.print_exc()
    
    # Test 2: Test keyboard construction with pagination
    print("\n2. Testing admin_assign_alliance_players() with pagination...")
    test_user_id = "123456789"
    
    try:
        # Page 0
        print("\n   Testing page 0...")
        keyboard_page_0 = await keyboard_constructor.admin_assign_alliance_players(test_user_id, 0)
        print(f"   ✓ Page 0 has {len(keyboard_page_0)} button rows")
        
        # Check if pagination buttons exist
        has_pagination = any("📄" in str(row) for row in keyboard_page_0)
        print(f"   ✓ Pagination controls present: {has_pagination}")
        
        # If we have enough users, test page 1
        if len(warmasters) > 20:
            print("\n   Testing page 1...")
            keyboard_page_1 = await keyboard_constructor.admin_assign_alliance_players(test_user_id, 1)
            print(f"   ✓ Page 1 has {len(keyboard_page_1)} button rows")
        
        # Test boundary conditions
        print("\n   Testing boundary conditions...")
        keyboard_high_page = await keyboard_constructor.admin_assign_alliance_players(test_user_id, 999)
        print(f"   ✓ High page number handled gracefully: {len(keyboard_high_page)} rows")
        
        keyboard_negative = await keyboard_constructor.admin_assign_alliance_players(test_user_id, -1)
        print(f"   ✓ Negative page number handled gracefully: {len(keyboard_negative)} rows")
        
    except Exception as e:
        print(f"   ✗ Error: {e}")
        import traceback
        traceback.print_exc()
    
    # Test 3: Test admin appoint pagination
    print("\n3. Testing admin_appoint_admin_users() with pagination...")
    try:
        keyboard = await keyboard_constructor.admin_appoint_admin_users(test_user_id, 0)
        print(f"   ✓ Admin appoint page 0 has {len(keyboard)} button rows")
        
        has_pagination = any("📄" in str(row) for row in keyboard)
        print(f"   ✓ Pagination controls present: {has_pagination}")
        
    except Exception as e:
        print(f"   ✗ Error: {e}")
        import traceback
        traceback.print_exc()
    
    # Test 4: Verify button structure
    print("\n4. Verifying button structure...")
    try:
        keyboard = await keyboard_constructor.admin_assign_alliance_players(test_user_id, 0)
        
        # Count different button types
        player_buttons = 0
        pagination_buttons = 0
        back_buttons = 0
        
        for row in keyboard:
            for button in row:
                callback_data = button.callback_data
                if callback_data.startswith("admin_player:"):
                    player_buttons += 1
                elif callback_data.startswith("admin_players_page:"):
                    pagination_buttons += 1
                elif callback_data == "back_to_main":
                    back_buttons += 1
        
        print(f"   ✓ Player buttons: {player_buttons}")
        print(f"   ✓ Pagination buttons: {pagination_buttons}")
        print(f"   ✓ Back buttons: {back_buttons}")
        
        # Verify we don't exceed limits
        total_buttons = sum(len(row) for row in keyboard)
        print(f"   ✓ Total buttons: {total_buttons} (should be < 100)")
        
        if total_buttons < 100:
            print("   ✓ Within Telegram's button limit!")
        else:
            print("   ✗ WARNING: Exceeds Telegram's 100 button limit!")
        
    except Exception as e:
        print(f"   ✗ Error: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n" + "=" * 60)
    print("Pagination Tests Complete!")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(test_pagination())
