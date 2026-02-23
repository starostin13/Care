#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Standalone script to set admin web password
Does NOT import any CareBot modules - direct SQLite access
"""

import sys
import hashlib
import sqlite3
from datetime import datetime

def set_password(db_path: str, warmaster_id: int, password: str):
    """Set web password for admin using direct SQLite access"""
    
    # Hash password with SHA256 (same as in sqllite_helper)
    password_hash = hashlib.sha256(password.encode()).hexdigest()
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Check if warmaster exists and is admin
        cursor.execute("SELECT is_admin, nickname FROM warmasters WHERE id = ?", (warmaster_id,))
        result = cursor.fetchone()
        
        if not result:
            print(f"❌ Warmaster ID {warmaster_id} not found")
            return False
            
        is_admin, nickname = result
        if is_admin != 1:
            print(f"❌ Warmaster {nickname} (ID {warmaster_id}) is not an admin")
            return False
        
        # Insert or update password
        cursor.execute("""
            INSERT INTO admin_users (warmaster_id, password_hash, created_at, last_login)
            VALUES (?, ?, ?, NULL)
            ON CONFLICT(warmaster_id) DO UPDATE SET
                password_hash = excluded.password_hash
        """, (warmaster_id, password_hash, datetime.now().isoformat()))
        
        conn.commit()
        print(f"✅ Web password set for warmaster: {nickname} (ID {warmaster_id})")
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False
    finally:
        conn.close()

if __name__ == "__main__":
    if len(sys.argv) != 4:
        print("Usage: python set_password_standalone.py <db_path> <warmaster_id> <password>")
        print("Example: python set_password_standalone.py /app/data/game_database.db 1 mypassword")
        sys.exit(1)
    
    db_path = sys.argv[1]
    warmaster_id = int(sys.argv[2])
    password = sys.argv[3]
    
    success = set_password(db_path, warmaster_id, password)
    sys.exit(0 if success else 1)
