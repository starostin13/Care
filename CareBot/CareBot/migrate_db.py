"""
Database migration system using yoyo-migrations.
This script checks for pending migrations and applies them automatically.
"""

import os
import sys
from yoyo import get_backend, read_migrations

# Database path from sqllite_helper.py
DATABASE_PATH = (r"C:\Users\al-gerasimov\source\repos\Care\CareBot\CareBot"
                 r"\db\database")

MIGRATIONS_DIR = "migrations"


def ensure_database_exists():
    """Ensure the database file and directory exist."""
    db_dir = os.path.dirname(DATABASE_PATH)
    if not os.path.exists(db_dir):
        os.makedirs(db_dir)
        print(f"Created database directory: {db_dir}")
    
    if not os.path.exists(DATABASE_PATH):
        # Create empty database file
        open(DATABASE_PATH, 'a').close()
        print(f"Created database file: {DATABASE_PATH}")


def run_migrations():
    """Run pending database migrations."""
    
    # Ensure database exists
    ensure_database_exists()
    
    # Get the directory of this script
    script_dir = os.path.dirname(os.path.abspath(__file__))
    migrations_path = os.path.join(script_dir, MIGRATIONS_DIR)
    
    if not os.path.exists(migrations_path):
        print(f"No migrations directory found at {migrations_path}")
        return True
    
    try:
        # Create database backend
        backend = get_backend(f"sqlite:///{DATABASE_PATH}")
        
        # Read migrations
        migrations = read_migrations(migrations_path)
        
        if not migrations:
            print("No migrations found.")
            return True
        
        # Get pending migrations
        pending = backend.to_apply(migrations)
        
        if not pending:
            print("✅ Database is up to date. No migrations to apply.")
            return True
        
        print(f"Found {len(pending)} pending migration(s):")
        for migration in pending:
            print(f"  - {migration.id}")
        
        # Apply migrations
        print("\nApplying migrations...")
        with backend.lock():
            backend.apply_migrations(backend.to_apply(migrations))
        
        print("✅ All migrations applied successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Database error during migration: {e}")
        return False
    except Exception as e:
        print(f"❌ Error during migration: {e}")
        return False


def check_migration_status():
    """Check which migrations have been applied."""
    
    if not os.path.exists(DATABASE_PATH):
        print("Database does not exist yet.")
        return
    
    try:
        # Get the directory of this script
        script_dir = os.path.dirname(os.path.abspath(__file__))
        migrations_path = os.path.join(script_dir, MIGRATIONS_DIR)
        
        # Create database backend
        backend = get_backend(f"sqlite:///{DATABASE_PATH}")
        
        # Read migrations
        migrations = read_migrations(migrations_path)
        
        # Get applied migrations
        applied = backend.to_rollback(migrations)
        pending = backend.to_apply(migrations)
        
        print("Migration Status:")
        print("=" * 50)
        
        if applied:
            print("✅ Applied migrations:")
            for migration in applied:
                print(f"  - {migration.id}")
        
        if pending:
            print("\n⏳ Pending migrations:")
            for migration in pending:
                print(f"  - {migration.id}")
        
        if not applied and not pending:
            print("No migrations found.")
            
    except Exception as e:
        print(f"Error checking migration status: {e}")


if __name__ == "__main__":
    print("CareBot Database Migration System")
    print("=" * 40)
    
    if len(sys.argv) > 1 and sys.argv[1] == "--status":
        check_migration_status()
    else:
        success = run_migrations()
        if not success:
            sys.exit(1)