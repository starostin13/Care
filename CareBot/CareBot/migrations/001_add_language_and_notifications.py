"""
Migration 001: Add language and notifications_enabled columns to warmasters table

This migration adds:
- language column (TEXT, default 'ru')
- notifications_enabled column (INTEGER, default 1)
"""

from yoyo import step

def add_language_column_if_not_exists(conn):
    """Add language column if it doesn't exist."""
    cursor = conn.cursor()
    
    # Check if column exists
    cursor.execute("PRAGMA table_info(warmasters)")
    columns = [col[1] for col in cursor.fetchall()]
    
    if 'language' not in columns:
        cursor.execute("ALTER TABLE warmasters ADD COLUMN language TEXT DEFAULT 'ru'")

def add_notifications_column_if_not_exists(conn):
    """Add notifications_enabled column if it doesn't exist."""
    cursor = conn.cursor()
    
    # Check if column exists
    cursor.execute("PRAGMA table_info(warmasters)")
    columns = [col[1] for col in cursor.fetchall()]
    
    if 'notifications_enabled' not in columns:
        cursor.execute("ALTER TABLE warmasters ADD COLUMN notifications_enabled INTEGER DEFAULT 1")

def remove_language_column(conn):
    """Remove language column (rollback)."""
    # SQLite doesn't support DROP COLUMN before version 3.35.0
    # For compatibility, we'll leave the column but mark migration as rolled back
    pass

def remove_notifications_column(conn):
    """Remove notifications_enabled column (rollback)."""
    # SQLite doesn't support DROP COLUMN before version 3.35.0
    # For compatibility, we'll leave the column but mark migration as rolled back
    pass

steps = [
    step(add_language_column_if_not_exists, remove_language_column),
    step(add_notifications_column_if_not_exists, remove_notifications_column)
]