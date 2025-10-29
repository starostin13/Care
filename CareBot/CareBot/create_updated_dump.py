"""
Create a new database dump after migration.
"""

import sqlite3
import os
from datetime import datetime

# Database path
DATABASE_PATH = (r"C:\Users\al-gerasimov\source\repos\Care\CareBot\CareBot"
                 r"\db\database")

def create_updated_dump():
    """Create a dump of the updated database."""
    
    if not os.path.exists(DATABASE_PATH):
        print(f"Error: Database file not found at {DATABASE_PATH}")
        return
    
    # Create output filename with timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    dump_filename = f"database_dump_migrated_{timestamp}.sql"
    dump_path = os.path.join(os.path.dirname(DATABASE_PATH), dump_filename)
    
    try:
        # Connect to the database
        conn = sqlite3.connect(DATABASE_PATH)
        
        # Create the dump
        with open(dump_path, 'w', encoding='utf-8') as f:
            # Write header
            f.write("-- SQLite Database Dump (After Migration)\n")
            f.write(f"-- Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write("-- Source: CareBot Database with language and notifications_enabled columns\n\n")
            
            # Write PRAGMA statements
            f.write("PRAGMA foreign_keys=OFF;\n")
            f.write("BEGIN TRANSACTION;\n\n")
            
            # Dump the database
            for line in conn.iterdump():
                f.write(f"{line}\n")
            
            # Write footer
            f.write("\nCOMMIT;\n")
            f.write("PRAGMA foreign_keys=ON;\n")
        
        conn.close()
        
        print(f"✅ Updated database dump created successfully!")
        print(f"Dump file: {dump_path}")
        print(f"File size: {os.path.getsize(dump_path)} bytes")
        
        return dump_path
        
    except Exception as e:
        print(f"Error creating dump: {e}")
        return None

if __name__ == "__main__":
    print("Creating updated database dump after migration...")
    print("=" * 50)
    create_updated_dump()