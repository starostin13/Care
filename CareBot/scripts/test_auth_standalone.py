#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Test admin authentication - standalone version"""

import sys
import hashlib
import sqlite3

def test_auth(db_path: str, warmaster_id: int, password: str):
    """Test the authentication logic"""
    print(f"\n=== Testing Authentication for Warmaster ID: {warmaster_id} ===\n")
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Step 1: Check is_admin status
        print(f"Step 1: Checking is_admin status...")
        cursor.execute("SELECT is_admin, nickname, telegram_id, alliance FROM warmasters WHERE id = ?", (warmaster_id,))
        warmaster = cursor.fetchone()
        
        if not warmaster:
            print(f"  ❌ Warmaster ID {warmaster_id} not found!")
            return False
        
        is_admin, nickname, telegram_id, alliance = warmaster
        print(f"  Nickname: {nickname}")
        print(f"  Telegram ID: {telegram_id}")
        print(f"  Alliance: {alliance}")
        print(f"  is_admin: {is_admin}")
        
        if is_admin != 1:
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
        cursor.execute(
            "SELECT password_hash, created_at FROM admin_users WHERE warmaster_id = ?",
            (warmaster_id,)
        )
        admin_record = cursor.fetchone()
        
        if not admin_record:
            print(f"  ❌ No admin_users record found for warmaster_id {warmaster_id}")
            return False
        
        db_password_hash, created_at = admin_record
        print(f"  DB password_hash: {db_password_hash}")
        print(f"  Created at: {created_at}")
        
        if db_password_hash != password_hash:
            print(f"  ❌ Password hashes don't match!")
            print(f"     Expected: {password_hash}")
            print(f"     Got:      {db_password_hash}")
            return False
        else:
            print("  ✅ Password is correct")
        
        print("\n=== ✅ Authentication would succeed ===\n")
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        conn.close()

if __name__ == "__main__":
    if len(sys.argv) != 4:
        print("Usage: python test_auth_standalone.py <db_path> <warmaster_id> <password>")
        print("Example: python test_auth_standalone.py /app/data/game_database.db 1 sibbeer6")
        sys.exit(1)
    
    db_path = sys.argv[1]
    warmaster_id = int(sys.argv[2])
    password = sys.argv[3]
    
    result = test_auth(db_path, warmaster_id, password)
    sys.exit(0 if result else 1)
