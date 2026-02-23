#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Test admin authentication logic"""

import sys
import hashlib
import asyncio
import os

# Set test database path
os.environ['DATABASE_PATH'] = '/app/data/game_database.db'

# Import auth components
sys.path.insert(0, '/app')
from CareBot import sqllite_helper

async def test_auth(warmaster_id: int, password: str):
    """Test the authentication logic"""
    print(f"\n=== Testing Authentication for Warmaster ID: {warmaster_id} ===\n")
    
    # Step 1: Check is_admin status
    print(f"Step 1: Checking is_admin status...")
    is_admin = await sqllite_helper.is_warmaster_admin(warmaster_id)
    print(f"  is_warmaster_admin({warmaster_id}) = {is_admin}")
    
    if not is_admin:
        print("  ❌ User is not admin!")
        return False
    else:
        print("  ✅ User is admin")
    
    # Step 2: Hash password
    print(f"\nStep 2: Hashing password...")
    password_hash = hashlib.sha256(password.encode()).hexdigest()
    print(f"  Password: '{password}'")
    print(f"  Hash: {password_hash}")
    
    # Step 3: Check password in database
    print(f"\nStep 3: Checking password in admin_users table...")
    is_valid = await sqllite_helper.verify_admin_web_credentials(warmaster_id, password_hash)
    print(f"  verify_admin_web_credentials({warmaster_id}, hash) = {is_valid}")
    
    if not is_valid:
        print("  ❌ Password verification failed!")
        
        # Debug: Check what's in the database
        print("\n  Debug: Checking database records...")
        import aiosqlite
        async with aiosqlite.connect('/app/data/game_database.db') as db:
            # Check admin_users record
            async with db.execute(
                "SELECT warmaster_id, password_hash FROM admin_users WHERE warmaster_id = ?",
                (warmaster_id,)
            ) as cursor:
                record = await cursor.fetchone()
                if record:
                    print(f"    DB warmaster_id: {record[0]}")
                    print(f"    DB password_hash: {record[1]}")
                    print(f"    Hashes match: {record[1] == password_hash}")
                else:
                    print(f"    ❌ No record found in admin_users for warmaster_id {warmaster_id}")
        
        return False
    else:
        print("  ✅ Password is correct")
    
    # Step 4: Get warmaster info
    print(f"\nStep 4: Loading warmaster info...")
    info = await sqllite_helper.get_warmaster_info_by_id(warmaster_id)
    if info:
        print(f"  Nickname: {info[0]}")
        print(f"  Registered as: {info[1]}")
        print(f"  Telegram ID: {info[4]}")
        print(f"  Alliance: {info[5]}")
        print("  ✅ User loaded successfully")
    else:
        print("  ❌ Failed to load user info")
        return False
    
    print("\n=== ✅ Authentication would succeed ===\n")
    return True

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python test_admin_auth.py <warmaster_id> <password>")
        print("Example: python test_admin_auth.py 1 sibbeer6")
        sys.exit(1)
    
    warmaster_id = int(sys.argv[1])
    password = sys.argv[2]
    
    result = asyncio.run(test_auth(warmaster_id, password))
    sys.exit(0 if result else 1)
