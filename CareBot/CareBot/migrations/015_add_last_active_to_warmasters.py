"""
Migration 015: Add last_active column to warmasters table for tracking player activity
"""
from yoyo import step
import datetime

def add_last_active_column(conn):
    """Add last_active timestamp column to warmasters table."""
    cursor = conn.cursor()
    
    # Add last_active column with default value as current timestamp
    cursor.execute('''
        ALTER TABLE warmasters ADD COLUMN last_active TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    ''')
    
    # Initialize existing players with current timestamp
    cursor.execute('''
        UPDATE warmasters SET last_active = CURRENT_TIMESTAMP WHERE last_active IS NULL
    ''')
    
    print("✅ Added last_active column to warmasters table")

steps = [step(add_last_active_column)]
