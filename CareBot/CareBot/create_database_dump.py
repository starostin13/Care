"""
Script to create a SQL dump of the SQLite database for deployment on other devices.
This dump will include both the schema and the initial data.
"""

import sqlite3
import os
from datetime import datetime

# Database path from sqllite_helper.py
DATABASE_PATH = (r"C:\Users\al-gerasimov\source\repos\Care\CareBot\CareBot"
                 r"\db\database")

def create_database_dump():
    """Create a complete SQL dump of the database."""
    
    # Check if database exists
    if not os.path.exists(DATABASE_PATH):
        print(f"Error: Database file not found at {DATABASE_PATH}")
        return
    
    # Create output filename with timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    dump_filename = f"database_dump_{timestamp}.sql"
    dump_path = os.path.join(os.path.dirname(DATABASE_PATH), dump_filename)
    
    try:
        # Connect to the database
        conn = sqlite3.connect(DATABASE_PATH)
        
        # Create the dump
        with open(dump_path, 'w', encoding='utf-8') as f:
            # Write header
            f.write("-- SQLite Database Dump\n")
            f.write(f"-- Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write("-- Source: CareBot Database\n\n")
            
            # Write PRAGMA statements for better compatibility
            f.write("PRAGMA foreign_keys=OFF;\n")
            f.write("BEGIN TRANSACTION;\n\n")
            
            # Dump the database using iterdump
            for line in conn.iterdump():
                f.write(f"{line}\n")
            
            # Write footer
            f.write("\nCOMMIT;\n")
            f.write("PRAGMA foreign_keys=ON;\n")
        
        conn.close()
        
        print(f"Database dump created successfully!")
        print(f"Dump file: {dump_path}")
        print(f"File size: {os.path.getsize(dump_path)} bytes")
        
        return dump_path
        
    except sqlite3.Error as e:
        print(f"SQLite error: {e}")
        return None
    except Exception as e:
        print(f"Error creating dump: {e}")
        return None

def create_deployment_script(dump_path):
    """Create a deployment script to restore the database on another device."""
    
    if not dump_path or not os.path.exists(dump_path):
        print("No valid dump file to create deployment script for")
        return
    
    script_path = os.path.join(os.path.dirname(dump_path), "deploy_database.py")
    
    script_content = '''"""
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
    dump_file = "''' + os.path.basename(dump_path) + '''"
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
        print("\\nDeployment completed successfully!")
    else:
        print("\\nDeployment failed!")
        sys.exit(1)
'''
    
    try:
        with open(script_path, 'w', encoding='utf-8') as f:
            f.write(script_content)
        
        print(f"Deployment script created: {script_path}")
        return script_path
        
    except Exception as e:
        print(f"Error creating deployment script: {e}")
        return None

if __name__ == "__main__":
    print("CareBot Database Dump Creator")
    print("=" * 30)
    print()
    
    # Create the dump
    dump_path = create_database_dump()
    
    if dump_path:
        # Create deployment script
        create_deployment_script(dump_path)
        
        print("\nTo deploy on another device:")
        print("1. Copy the dump file and deploy_database.py to the target device")
        print("2. Ensure the target directory structure matches your project")
        print("3. Run: python deploy_database.py")
        print("\nNote: Modify the paths in deploy_database.py if your project structure differs")
    else:
        print("Failed to create database dump")