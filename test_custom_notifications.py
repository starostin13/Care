#!/usr/bin/env python3
"""
Test script to verify custom notification functions work correctly.
This tests the database and helper functions without running the full bot.
"""

import asyncio
import sys
import os

# Add the CareBot directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'CareBot', 'CareBot'))

import sqllite_helper
import localization


async def test_custom_notifications():
    """Test custom notification-related functions."""
    print("=" * 60)
    print("Testing Custom Notification Functions")
    print("=" * 60)
    
    # Test 1: Check if localization texts exist
    print("\n1. Testing localization texts...")
    try:
        test_keys = [
            "button_admin_custom_notification",
            "custom_notification_select_recipient_type",
            "button_notify_warmaster",
            "button_notify_alliance",
            "custom_notification_select_warmaster",
            "custom_notification_select_alliance",
            "custom_notification_send_message",
            "custom_notification_sent",
            "no_warmasters_found",
            "no_alliances_found",
        ]
        
        for key in test_keys:
            text_ru = await sqllite_helper.get_text_by_key(key, 'ru')
            text_en = await sqllite_helper.get_text_by_key(key, 'en')
            if text_ru and text_en:
                print(f"   ✓ {key}: RU='{text_ru[:30]}...' EN='{text_en[:30]}...'")
            else:
                print(f"   ✗ {key}: Missing (RU={bool(text_ru)}, EN={bool(text_en)})")
    except Exception as e:
        print(f"   ✗ Error: {e}")
    
    # Test 2: Get warmasters with nicknames
    print("\n2. Testing get_warmasters_with_nicknames()...")
    try:
        warmasters = await sqllite_helper.get_warmasters_with_nicknames()
        print(f"   ✓ Found {len(warmasters)} warmasters with nicknames:")
        for wm in warmasters[:5]:  # Show first 5
            telegram_id, nickname, alliance = wm
            print(f"      - {nickname} (ID: {telegram_id}, Alliance: {alliance})")
        if len(warmasters) > 5:
            print(f"      ... and {len(warmasters) - 5} more")
    except Exception as e:
        print(f"   ✗ Error: {e}")
    
    # Test 3: Get all alliances
    print("\n3. Testing get_all_alliances()...")
    try:
        alliances = await sqllite_helper.get_all_alliances()
        print(f"   ✓ Found {len(alliances)} alliances:")
        for alliance in alliances:
            alliance_id, alliance_name = alliance[:2]
            print(f"      - {alliance_name} (ID: {alliance_id})")
    except Exception as e:
        print(f"   ✗ Error: {e}")
    
    # Test 4: Get players by alliance
    print("\n4. Testing get_players_by_alliance()...")
    try:
        alliances = await sqllite_helper.get_all_alliances()
        if alliances:
            test_alliance_id = alliances[0][0]
            players = await sqllite_helper.get_players_by_alliance(test_alliance_id)
            print(f"   ✓ Alliance {alliances[0][1]} has {len(players)} players:")
            for player in players[:3]:  # Show first 3
                telegram_id, nickname, alliance = player
                print(f"      - {nickname} (ID: {telegram_id})")
            if len(players) > 3:
                print(f"      ... and {len(players) - 3} more")
        else:
            print("   - No alliances found to test")
    except Exception as e:
        print(f"   ✗ Error: {e}")
    
    # Test 5: Check admin status
    print("\n5. Testing is_user_admin()...")
    try:
        warmasters = await sqllite_helper.get_warmasters_with_nicknames()
        if warmasters:
            test_user_id = warmasters[0][0]
            is_admin = await sqllite_helper.is_user_admin(test_user_id)
            print(f"   ✓ User {warmasters[0][1]} (ID: {test_user_id}) admin status: {is_admin}")
        else:
            print("   - No users found to test")
    except Exception as e:
        print(f"   ✗ Error: {e}")
    
    # Test 6: Test localization.get_text_for_user
    print("\n6. Testing localization.get_text_for_user()...")
    try:
        warmasters = await sqllite_helper.get_warmasters_with_nicknames()
        if warmasters:
            test_user_id = warmasters[0][0]
            text = await localization.get_text_for_user(
                test_user_id,
                "button_admin_custom_notification"
            )
            print(f"   ✓ Got text for user {warmasters[0][1]}: '{text}'")
        else:
            print("   - No users found to test")
    except Exception as e:
        print(f"   ✗ Error: {e}")
    
    print("\n" + "=" * 60)
    print("Test Complete!")
    print("=" * 60)


if __name__ == "__main__":
    print("\nNote: Make sure DATABASE_PATH environment variable is set correctly")
    print("or the default path points to your database.\n")
    
    asyncio.run(test_custom_notifications())
