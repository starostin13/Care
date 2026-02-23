"""
Database deployment script for CareBot.
This script will restore the database from the SQL dump.
"""

import sqlite3
import os
import sys

def deploy_database(dump_file_path, target_db_path):
    """Deploy the database from a SQL dump file."""
    
    # Check if dump file exists
    if not os.path.exists(dump_file_path):
        print(f"Error: Dump file not found at {dump_file_path}")
        return False
    
    # Create target directory if it doesn't exist
    target_dir = os.path.dirname(target_db_path)
    if not os.path.exists(target_dir):
        os.makedirs(target_dir)
        print(f"Created directory: {target_dir}")
    
    # Remove existing database if it exists
    if os.path.exists(target_db_path):
        backup_path = f"{target_db_path}.backup"
        os.rename(target_db_path, backup_path)
        print(f"Existing database backed up to: {backup_path}")
    
    try:
        # Create new database
        conn = sqlite3.connect(target_db_path)
        
        # Read and execute the dump file
        with open(dump_file_path, 'r', encoding='utf-8') as f:
            sql_script = f.read()
        
        conn.executescript(sql_script)
        conn.close()
        
        print(f"Database deployed successfully to: {target_db_path}")
        return True
        
    except sqlite3.Error as e:
        print(f"SQLite error during deployment: {e}")
        return False
    except Exception as e:
        print(f"Error during deployment: {e}")
        return False

if __name__ == "__main__":
    # Default paths - modify as needed for your deployment
    dump_file = "database_dump_20251027_131158.sql"
    target_database = "db/database"  # Relative to script location
    
    # Get script directory
    script_dir = os.path.dirname(os.path.abspath(__file__))
    dump_file_path = os.path.join(script_dir, dump_file)
    target_db_path = os.path.join(script_dir, target_database)
    
    print("CareBot Database Deployment")
    print("=" * 30)
    print(f"Dump file: {dump_file_path}")
    print(f"Target database: {target_db_path}")
    print()
    
    if deploy_database(dump_file_path, target_db_path):
        print("\nDeployment completed successfully!")
    else:
        print("\nDeployment failed!")
        sys.exit(1)
