"""
Script to check database schema and add missing columns if needed.
"""

import sqlite3
import os

# Database path from sqllite_helper.py
DATABASE_PATH = (r"C:\Users\al-gerasimov\source\repos\Care\CareBot\CareBot"
                 r"\db\database")

def check_table_schema():
    """Check the current schema of warmasters table."""
    
    if not os.path.exists(DATABASE_PATH):
        print(f"Error: Database file not found at {DATABASE_PATH}")
        return
    
    try:
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        
        # Get table schema
        cursor.execute("PRAGMA table_info(warmasters)")
        columns = cursor.fetchall()
        
        print("Current warmasters table schema:")
        print("=" * 50)
        for column in columns:
            print(f"Column: {column[1]}, Type: {column[2]}, NotNull: {column[3]}, Default: {column[4]}")
        
        # Check if language column exists
        column_names = [column[1] for column in columns]
        
        if 'language' not in column_names:
            print("\n❌ Missing 'language' column!")
            add_missing_columns(conn)
        else:
            print("\n✅ 'language' column exists")
            
        if 'notifications_enabled' not in column_names:
            print("❌ Missing 'notifications_enabled' column!")
            add_missing_columns(conn)
        else:
            print("✅ 'notifications_enabled' column exists")
        
        conn.close()
        
    except sqlite3.Error as e:
        print(f"SQLite error: {e}")
    except Exception as e:
        print(f"Error: {e}")

def add_missing_columns(conn):
    """Add missing columns to warmasters table."""
    
    try:
        cursor = conn.cursor()
        
        # Check if language column exists and add it if missing
        cursor.execute("PRAGMA table_info(warmasters)")
        columns = cursor.fetchall()
        column_names = [column[1] for column in columns]
        
        if 'language' not in column_names:
            print("Adding 'language' column...")
            cursor.execute("ALTER TABLE warmasters ADD COLUMN language TEXT DEFAULT 'ru'")
            print("✅ Added 'language' column with default 'ru'")
        
        if 'notifications_enabled' not in column_names:
            print("Adding 'notifications_enabled' column...")
            cursor.execute("ALTER TABLE warmasters ADD COLUMN notifications_enabled INTEGER DEFAULT 1")
            print("✅ Added 'notifications_enabled' column with default 1")
        
        conn.commit()
        print("\n🎉 Migration completed successfully!")
        
    except sqlite3.Error as e:
        print(f"Error adding columns: {e}")
        conn.rollback()

def show_all_tables():
    """Show all tables in the database."""
    
    try:
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cursor.fetchall()
        
        print("\nAll tables in database:")
        print("=" * 30)
        for table in tables:
            print(f"- {table[0]}")
        
        conn.close()
        
    except sqlite3.Error as e:
        print(f"SQLite error: {e}")

if __name__ == "__main__":
    print("CareBot Database Schema Checker & Migrator")
    print("=" * 45)
    
    show_all_tables()
    print()
    check_table_schema()