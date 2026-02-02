"""
Migration 020: Add status column to mission_stack and create pending_results table
This enables the confirmation flow for game results.

Status values:
- 1: Active mission (can be played)
- 2: Pending confirmation (score submitted, awaiting confirmation)
- 3: Confirmed (score confirmed, results applied)
"""
from yoyo import step

def add_status_column_and_pending_results(conn):
    cursor = conn.cursor()
    
    # Check if status column exists
    cursor.execute("PRAGMA table_info(mission_stack)")
    columns = [col[1] for col in cursor.fetchall()]
    
    if 'status' not in columns:
        # Add status column with default value 1 (active)
        cursor.execute("ALTER TABLE mission_stack ADD COLUMN status INTEGER DEFAULT 1")
        print("✅ Added status column to mission_stack table")
        
        # Set status=1 for all existing missions
        cursor.execute("UPDATE mission_stack SET status = 1 WHERE status IS NULL")
        print("✅ Set status=1 for existing missions")
    else:
        print("✅ Status column already exists in mission_stack")
    
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

steps = [step(add_status_column_and_pending_results)]
