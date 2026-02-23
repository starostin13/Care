"""
Migration 026: Add admin_users table for web admin authentication.

Creates admin_users table to store web passwords for admins.
The is_admin field in warmasters table (set via Telegram) determines admin status.
This table only stores password_hash for web authentication.
"""
from yoyo import step


def create_admin_users_table(conn):
    """Create the admin_users table for web authentication."""
    cursor = conn.cursor()
    
    # Check if admin_users table already exists
    cursor.execute("""
        SELECT name FROM sqlite_master 
        WHERE type='table' AND name='admin_users'
    """)
    table_exists = cursor.fetchone()
    
    if not table_exists:
        # Create admin_users table
        cursor.execute("""
            CREATE TABLE admin_users (
                warmaster_id INTEGER PRIMARY KEY,
                password_hash TEXT NOT NULL,
                created_at TEXT DEFAULT (datetime('now')),
                last_login TEXT,
                FOREIGN KEY (warmaster_id) REFERENCES warmasters(id) ON DELETE CASCADE
            )
        """)
        print("✅ Created admin_users table")
        print("   Note: is_admin status is determined by warmasters.is_admin field")
        print("   This table only stores web passwords for admin access")
    else:
        print("✅ admin_users table already exists")
    
    conn.commit()


steps = [
    step(create_admin_users_table)
]
