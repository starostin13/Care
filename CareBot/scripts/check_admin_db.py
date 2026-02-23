#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Check admin database records"""

import sqlite3
import sys

db_path = sys.argv[1] if len(sys.argv) > 1 else '/app/data/game_database.db'
warmaster_id = int(sys.argv[2]) if len(sys.argv) > 2 else 1

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Check warmaster
cursor.execute("SELECT id, telegram_id, nickname, is_admin FROM warmasters WHERE id = ?", (warmaster_id,))
warmaster = cursor.fetchone()
print(f"Warmaster record: {warmaster}")

if warmaster:
    print(f"  ID: {warmaster[0]}")
    print(f"  Telegram ID: {warmaster[1]}")
    print(f"  Nickname: {warmaster[2]}")
    print(f"  is_admin: {warmaster[3]}")

# Check admin_users
cursor.execute("SELECT warmaster_id, password_hash, created_at, last_login FROM admin_users WHERE warmaster_id = ?", (warmaster_id,))
admin_user = cursor.fetchone()
print(f"\nAdmin user record: {admin_user}")

if admin_user:
    print(f"  Warmaster ID: {admin_user[0]}")
    print(f"  Password hash: {admin_user[1][:50]}...")
    print(f"  Created at: {admin_user[2]}")
    print(f"  Last login: {admin_user[3]}")

conn.close()
