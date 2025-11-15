#!/usr/bin/env python3
"""
Simple test script to verify admin alliance assignment functions.
This doesn't run the full bot, just tests the database functions.
"""

import asyncio
import sys
import os

# Add the CareBot directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'CareBot', 'CareBot'))

import sqllite_helper


async def test_admin_functions():
    """Test admin-related database functions."""
    print("=" * 60)
    print("Testing Admin Alliance Assignment Functions")
    print("=" * 60)
    
    # Test 1: Check if first user is admin (should auto-promote)
    print("\n1. Testing ensure_first_user_is_admin()...")
    try:
        admin_id = await sqllite_helper.ensure_first_user_is_admin()
        if admin_id:
            print(f"   ✓ Made user {admin_id} an admin")
        else:
            print("   ✓ Admin already exists")
    except Exception as e:
        print(f"   ✗ Error: {e}")
    
    # Test 2: Get warmasters with nicknames
    print("\n2. Testing get_warmasters_with_nicknames()...")
    try:
        warmasters = await sqllite_helper.get_warmasters_with_nicknames()
        print(f"   ✓ Found {len(warmasters)} warmasters with nicknames:")
        for wm in warmasters:
            telegram_id, nickname, alliance = wm
            print(f"      - {nickname} (ID: {telegram_id}, Alliance: {alliance})")
    except Exception as e:
        print(f"   ✗ Error: {e}")
    
    # Test 3: Get all alliances
    print("\n3. Testing get_all_alliances()...")
    try:
        alliances = await sqllite_helper.get_all_alliances()
        print(f"   ✓ Found {len(alliances)} alliances:")
        for alliance in alliances:
            alliance_id, alliance_name = alliance
            print(f"      - {alliance_name} (ID: {alliance_id})")
    except Exception as e:
        print(f"   ✗ Error: {e}")
    
    # Test 4: Get alliance player counts
    print("\n4. Testing get_alliance_player_count()...")
    try:
        alliances = await sqllite_helper.get_all_alliances()
        for alliance_id, alliance_name in alliances:
            count = await sqllite_helper.get_alliance_player_count(alliance_id)
            print(f"   ✓ {alliance_name}: {count} players")
    except Exception as e:
        print(f"   ✗ Error: {e}")
    
    # Test 5: Check admin status
    print("\n5. Testing is_user_admin()...")
    try:
        if admin_id:
            is_admin = await sqllite_helper.is_user_admin(admin_id)
            print(f"   ✓ User {admin_id} admin status: {is_admin}")
        else:
            print("   - Skipped (no admin ID available)")
    except Exception as e:
        print(f"   ✗ Error: {e}")
    
    print("\n" + "=" * 60)
    print("Test Complete!")
    print("=" * 60)


if __name__ == "__main__":
    print("\nNote: Make sure DATABASE_PATH environment variable is set correctly")
    print("or the default path points to your database.\n")
    
    asyncio.run(test_admin_functions())
