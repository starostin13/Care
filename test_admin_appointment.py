#!/usr/bin/env python3
"""
Test script to verify admin appointment functions.
This tests the new admin appointment feature.
"""

import asyncio
import sys
import os

# Add the CareBot directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'CareBot', 'CareBot'))

import sqllite_helper
import keyboard_constructor
import localization


async def test_admin_appointment_functions():
    """Test admin appointment functionality."""
    print("=" * 60)
    print("Testing Admin Appointment Functions")
    print("=" * 60)
    
    # Test 1: Find an admin user
    print("\n1. Setting up test environment...")
    try:
        warmasters = await sqllite_helper.get_warmasters_with_nicknames()
        admin_id = None
        for wm in warmasters:
            telegram_id, nickname, alliance = wm
            if await sqllite_helper.is_user_admin(telegram_id):
                admin_id = telegram_id
                print(f"   ✓ Found admin user: {nickname} (ID: {admin_id})")
                break
        
        if not admin_id:
            print("   ✗ No admin found in database")
            return
    except Exception as e:
        print(f"   ✗ Error: {e}")
        return
    
    # Test 2: Test is_user_admin function
    print("\n2. Testing is_user_admin()...")
    try:
        is_admin = await sqllite_helper.is_user_admin(admin_id)
        print(f"   ✓ User {admin_id} is admin: {is_admin}")
    except Exception as e:
        print(f"   ✗ Error: {e}")
    
    # Test 3: Test getting warmasters with nicknames
    print("\n3. Testing get_warmasters_with_nicknames()...")
    try:
        warmasters = await sqllite_helper.get_warmasters_with_nicknames()
        print(f"   ✓ Found {len(warmasters)} warmasters with nicknames:")
        for wm in warmasters:
            telegram_id, nickname, alliance = wm
            is_admin = await sqllite_helper.is_user_admin(telegram_id)
            admin_badge = " ⭐" if is_admin else ""
            print(f"      - {nickname}{admin_badge} (ID: {telegram_id})")
    except Exception as e:
        print(f"   ✗ Error: {e}")
    
    # Test 4: Test admin_appoint_admin_users keyboard
    print("\n4. Testing admin_appoint_admin_users() keyboard...")
    try:
        keyboard = await keyboard_constructor.admin_appoint_admin_users(admin_id)
        print(f"   ✓ Generated keyboard with {len(keyboard)} buttons")
        for button_row in keyboard:
            for button in button_row:
                print(f"      - {button.text} -> {button.callback_data}")
    except Exception as e:
        print(f"   ✗ Error: {e}")
    
    # Test 5: Test localization texts
    print("\n5. Testing localization texts...")
    try:
        texts = [
            'button_appoint_admin',
            'admin_appoint_title',
            'admin_appointed_success'
        ]
        for key in texts:
            text = await localization.get_text_for_user(admin_id, key)
            print(f"   ✓ {key}: {text}")
    except Exception as e:
        print(f"   ✗ Error: {e}")
    
    # Test 6: Test make_user_admin function (if we have another user)
    print("\n6. Testing make_user_admin() function...")
    try:
        warmasters = await sqllite_helper.get_warmasters_with_nicknames()
        # Find a non-admin user
        test_user_id = None
        test_user_nickname = None
        for wm in warmasters:
            telegram_id, nickname, alliance = wm
            if not await sqllite_helper.is_user_admin(telegram_id):
                test_user_id = telegram_id
                test_user_nickname = nickname
                break
        
        if test_user_id:
            # Check current admin status
            was_admin = await sqllite_helper.is_user_admin(test_user_id)
            print(f"   - User {test_user_nickname} (ID: {test_user_id})")
            print(f"   - Current admin status: {was_admin}")
            
            # Make them admin
            await sqllite_helper.make_user_admin(test_user_id)
            is_now_admin = await sqllite_helper.is_user_admin(test_user_id)
            print(f"   ✓ After make_user_admin: {is_now_admin}")
            
            if not was_admin and is_now_admin:
                print(f"   ✓ Successfully promoted {test_user_nickname} to admin!")
            else:
                print(f"   ⚠ User status unchanged")
        else:
            print("   - Skipped (all users are already admins)")
    except Exception as e:
        print(f"   ✗ Error: {e}")
    
    print("\n" + "=" * 60)
    print("Test Complete!")
    print("=" * 60)


if __name__ == "__main__":
    print("\nNote: Make sure DATABASE_PATH environment variable is set correctly")
    print("or the default path points to your database.\n")
    
    asyncio.run(test_admin_appointment_functions())
