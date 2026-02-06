"""
Migration 020: Rename locked column to status and create pending_results table
This enables the confirmation flow for game results.

The locked column is renamed to status for clarity.
Status values:
- 0: Available mission (can be selected for play) - was "unlocked"
- 1: Active mission (being played) - was "locked" 
- 2: Pending confirmation (score submitted, awaiting confirmation) - NEW
- 3: Confirmed (score confirmed, results applied) - NEW

The pending_results table stores submitted scores awaiting confirmation.
"""
from yoyo import step

def rename_locked_to_status_and_create_pending_results(conn):
    cursor = conn.cursor()

    # Preserve trigger definitions that depend on mission_stack.
    cursor.execute("""
        SELECT sql FROM sqlite_master
        WHERE type='trigger' AND name='validate_battle_mission_id'
    """)
    trigger_row = cursor.fetchone()
    trigger_sql = trigger_row[0] if trigger_row else None
    
    # Check current schema
    cursor.execute("PRAGMA table_info(mission_stack)")
    columns = {col[1]: col for col in cursor.fetchall()}
    
    # If we have 'locked' column but not 'status', rename it
    if 'locked' in columns and 'status' not in columns:
        # SQLite doesn't support RENAME COLUMN in older versions, so we need to recreate the table
        print("🔄 Renaming 'locked' column to 'status' in mission_stack...")

        if trigger_sql:
            cursor.execute("DROP TRIGGER IF EXISTS validate_battle_mission_id")
        
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

        if trigger_sql:
            cursor.execute(trigger_sql)
        
        print("✅ Successfully renamed 'locked' to 'status' in mission_stack")
        
    elif 'status' in columns and 'locked' not in columns:
        print("✅ 'status' column already exists (locked already renamed)")
    elif 'locked' in columns and 'status' in columns:
        print("⚠️  Both 'locked' and 'status' columns exist - manual intervention needed")
    else:
        # Neither exists, create status column
        cursor.execute("ALTER TABLE mission_stack ADD COLUMN status INTEGER DEFAULT 0")
        print("✅ Added 'status' column to mission_stack")
    
    # Check if pending_results table exists
    cursor.execute("""
        SELECT name FROM sqlite_master 
        WHERE type='table' AND name='pending_results'
    """)
    table_exists = cursor.fetchone()
    
    if not table_exists:
        # Create pending_results table
        cursor.execute("""
            CREATE TABLE pending_results (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                battle_id INTEGER NOT NULL,
                submitter_id TEXT NOT NULL,
                fstplayer_score INTEGER NOT NULL,
                sndplayer_score INTEGER NOT NULL,
                created_at TEXT NOT NULL,
                FOREIGN KEY (battle_id) REFERENCES battles(id)
            )
        """)
        print("✅ Created pending_results table")
    else:
        print("✅ pending_results table already exists")
    
    conn.commit()

steps = [step(rename_locked_to_status_and_create_pending_results)]
