#!/usr/bin/env python3
"""
Test script to verify pagination logic works with many users.
"""

import asyncio
import sys
import os

# Add the CareBot directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'CareBot', 'CareBot'))

# Set test mode before importing modules that depend on config
os.environ['CAREBOT_TEST_MODE'] = 'true'
os.environ['TEST_MODE'] = '1'

import config
config.TEST_MODE = True

import keyboard_constructor
import mock_sqlite_helper as sqllite_helper


# Monkey patch the mock data to simulate many users
original_get_warmasters = sqllite_helper.get_warmasters_with_nicknames

async def get_warmasters_with_many_users():
    """Return many mock users to test pagination."""
    users = []
    for i in range(55):  # Create 55 users to test pagination (3 pages)
        users.append((
            f"user_{i}",  # telegram_id
            f"TestUser{i:02d}",  # nickname
            (i % 3) + 1  # alliance (cycling through 1, 2, 3)
        ))
    return users

# Apply monkey patch
sqllite_helper.get_warmasters_with_nicknames = get_warmasters_with_many_users


async def test_pagination_with_many_users():
    """Test pagination with many users."""
    print("=" * 60)
    print("Testing Pagination with Many Users (55 users)")
    print("=" * 60)
    
    test_user_id = "123456789"
    
    # Test 1: Verify we have many users
    print("\n1. Verifying mock data...")
    warmasters = await sqllite_helper.get_warmasters_with_nicknames()
    print(f"   ✓ Generated {len(warmasters)} mock users")
    
    # Test 2: Test each page
    print("\n2. Testing pagination across pages...")
    
    total_pages = (len(warmasters) + 19) // 20  # 20 items per page
    print(f"   Expected pages: {total_pages}")
    
    for page_num in range(total_pages):
        print(f"\n   Testing page {page_num}...")
        keyboard = await keyboard_constructor.admin_assign_alliance_players(test_user_id, page_num)
        
        # Count different button types
        player_buttons = 0
        pagination_row_found = False
        
        for row in keyboard:
            for button in row:
                callback_data = button.callback_data
                if callback_data.startswith("admin_player:"):
                    player_buttons += 1
                elif "📄" in button.text:
                    pagination_row_found = True
        
        print(f"      ✓ Player buttons on page {page_num}: {player_buttons}")
        print(f"      ✓ Pagination controls: {pagination_row_found}")
        
        # Verify button count
        total_buttons = sum(len(row) for row in keyboard)
        print(f"      ✓ Total buttons: {total_buttons}")
        
        if total_buttons >= 100:
            print(f"      ✗ ERROR: Page {page_num} exceeds 100 button limit!")
            return False
        
        # Verify page structure
        if page_num == 0:
            # First page should have 20 players + pagination + back = 22 rows
            expected_min_rows = 21  # 20 player rows + pagination row + back row
            if len(keyboard) < expected_min_rows:
                print(f"      ✗ ERROR: Expected at least {expected_min_rows} rows, got {len(keyboard)}")
        elif page_num == total_pages - 1:
            # Last page has remaining users
            remaining_users = len(warmasters) - (page_num * 20)
            print(f"      ✓ Last page has {remaining_users} users")
    
    # Test 3: Test navigation buttons
    print("\n3. Testing navigation button presence...")
    
    # First page should have only "Next" button
    keyboard_first = await keyboard_constructor.admin_assign_alliance_players(test_user_id, 0)
    has_prev = any("◀️" in str(row) for row in keyboard_first)
    has_next = any("▶️" in str(row) for row in keyboard_first)
    print(f"   First page - Previous button: {has_prev} (should be False)")
    print(f"   First page - Next button: {has_next} (should be True)")
    
    # Middle page should have both
    if total_pages > 2:
        keyboard_middle = await keyboard_constructor.admin_assign_alliance_players(test_user_id, 1)
        has_prev = any("◀️" in str(row) for row in keyboard_middle)
        has_next = any("▶️" in str(row) for row in keyboard_middle)
        print(f"   Middle page - Previous button: {has_prev} (should be True)")
        print(f"   Middle page - Next button: {has_next} (should be True)")
    
    # Last page should have only "Previous" button
    keyboard_last = await keyboard_constructor.admin_assign_alliance_players(test_user_id, total_pages - 1)
    has_prev = any("◀️" in str(row) for row in keyboard_last)
    has_next = any("▶️" in str(row) for row in keyboard_last)
    print(f"   Last page - Previous button: {has_prev} (should be True)")
    print(f"   Last page - Next button: {has_next} (should be False)")
    
    # Test 4: Verify all users are accessible
    print("\n4. Verifying all users are accessible...")
    all_user_ids = set()
    
    for page_num in range(total_pages):
        keyboard = await keyboard_constructor.admin_assign_alliance_players(test_user_id, page_num)
        
        for row in keyboard:
            for button in row:
                callback_data = button.callback_data
                if callback_data.startswith("admin_player:"):
                    user_id = callback_data.split(':')[1]
                    all_user_ids.add(user_id)
    
    print(f"   ✓ Total unique users accessible: {len(all_user_ids)}")
    print(f"   ✓ Expected users: {len(warmasters)}")
    
    if len(all_user_ids) == len(warmasters):
        print("   ✓ All users are accessible across pages!")
    else:
        print(f"   ✗ ERROR: Missing users! Expected {len(warmasters)}, got {len(all_user_ids)}")
        return False
    
    print("\n" + "=" * 60)
    print("✓ All Pagination Tests Passed!")
    print("=" * 60)
    return True


if __name__ == "__main__":
    success = asyncio.run(test_pagination_with_many_users())
    sys.exit(0 if success else 1)
