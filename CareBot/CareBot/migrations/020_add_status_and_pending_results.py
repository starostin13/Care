"""
Migration 020: Rename locked column to status
This enables the confirmation flow for game results.

The locked column is renamed to status for clarity.
Status values:
- 0: Available mission (can be selected for play) - was "unlocked"
- 1: Active mission (being played) - was "locked" 
- 2: Pending confirmation (score submitted, awaiting confirmation) - NEW
- 3: Confirmed (score confirmed, results applied) - NEW

Note: The submitter of the result can be determined by checking who confirmed it
(the non-confirmer must be the submitter).
"""
from yoyo import step

def rename_locked_to_status(conn):
    cursor = conn.cursor()
    
    # Check current schema
    cursor.execute("PRAGMA table_info(mission_stack)")
    columns = {col[1]: col for col in cursor.fetchall()}
    
    # If we have 'locked' column but not 'status', rename it
    if 'locked' in columns and 'status' not in columns:
        # SQLite doesn't support RENAME COLUMN in older versions, so we need to recreate the table
        print("🔄 Renaming 'locked' column to 'status' in mission_stack...")
        
        # Create new table with status column
        cursor.execute("""
            CREATE TABLE mission_stack_new (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                deploy TEXT,
                rules TEXT,
                cell INTEGER,
                mission_description TEXT,
                winner_bonus TEXT,
                status INTEGER,
                created_date TEXT
            )
        """)
        
        # Copy data from old table to new table (locked -> status)
        cursor.execute("""
            INSERT INTO mission_stack_new (id, deploy, rules, cell, mission_description, winner_bonus, status, created_date)
            SELECT id, deploy, rules, cell, mission_description, winner_bonus, locked, created_date
            FROM mission_stack
        """)
        
        # Drop old table
        cursor.execute("DROP TABLE mission_stack")
        
        # Rename new table to original name
        cursor.execute("ALTER TABLE mission_stack_new RENAME TO mission_stack")
        
        print("✅ Successfully renamed 'locked' to 'status' in mission_stack")
        
    elif 'status' in columns and 'locked' not in columns:
        print("✅ 'status' column already exists (locked already renamed)")
    elif 'locked' in columns and 'status' in columns:
        print("⚠️  Both 'locked' and 'status' columns exist - manual intervention needed")
    else:
        # Neither exists, create status column
        cursor.execute("ALTER TABLE mission_stack ADD COLUMN status INTEGER DEFAULT 0")
        print("✅ Added 'status' column to mission_stack")
    
    conn.commit()

steps = [step(rename_locked_to_status)]
