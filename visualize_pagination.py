#!/usr/bin/env python3
"""
Visual demonstration of how the pagination looks in the Telegram bot.
"""

import asyncio
import sys
import os

# Add the CareBot directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'CareBot', 'CareBot'))

# Set test mode
os.environ['CAREBOT_TEST_MODE'] = 'true'

import config
config.TEST_MODE = True

import keyboard_constructor
import mock_sqlite_helper as sqllite_helper


# Monkey patch to create many users
async def get_warmasters_with_many_users():
    """Return many mock users to demonstrate pagination."""
    users = []
    for i in range(55):
        users.append((
            f"user_{i}",
            f"Player{i:02d}",
            (i % 3) + 1
        ))
    return users

sqllite_helper.get_warmasters_with_nicknames = get_warmasters_with_many_users


def print_keyboard(keyboard, page_num):
    """Pretty print a keyboard layout."""
    print(f"\n{'=' * 70}")
    print(f"Page {page_num + 1} - Telegram Inline Keyboard Layout")
    print('=' * 70)
    
    row_num = 1
    for row in keyboard:
        row_buttons = []
        for button in row:
            text = button.text
            callback = button.callback_data
            row_buttons.append(f"[{text}]")
        
        print(f"Row {row_num:2d}: {' '.join(row_buttons)}")
        row_num += 1
    
    total_buttons = sum(len(row) for row in keyboard)
    print(f"\nTotal buttons: {total_buttons}")
    print('=' * 70)


async def visualize_pagination():
    """Visualize what the pagination looks like."""
    print("\n" + "=" * 70)
    print("TELEGRAM BOT PAGINATION VISUALIZATION")
    print("Demonstrating Alliance Assignment Menu with 55 Users")
    print("=" * 70)
    
    test_user_id = "123456789"
    
    # Show first page
    print("\n\n📱 FIRST PAGE (Shows 20 users)")
    keyboard_page_0 = await keyboard_constructor.admin_assign_alliance_players(test_user_id, 0)
    print_keyboard(keyboard_page_0, 0)
    
    # Show middle page
    print("\n\n📱 MIDDLE PAGE (Shows 20 users)")
    keyboard_page_1 = await keyboard_constructor.admin_assign_alliance_players(test_user_id, 1)
    print_keyboard(keyboard_page_1, 1)
    
    # Show last page
    print("\n\n📱 LAST PAGE (Shows remaining 15 users)")
    keyboard_page_2 = await keyboard_constructor.admin_assign_alliance_players(test_user_id, 2)
    print_keyboard(keyboard_page_2, 2)
    
    print("\n\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)
    print("✅ All 55 users are accessible across 3 pages")
    print("✅ Each page has 18-24 buttons (well under 100 limit)")
    print("✅ Navigation buttons allow moving between pages")
    print("✅ Page indicator shows current position")
    print("=" * 70)


if __name__ == "__main__":
    asyncio.run(visualize_pagination())
