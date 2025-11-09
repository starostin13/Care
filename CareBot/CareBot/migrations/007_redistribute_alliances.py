"""
Migration to redistribute alliances among warmasters.
Creates 5 alliances with specific warmaster assignments:
- Alliance 1: warmasters with id 1 and 12
- Alliance 2: warmasters with id 7 and 11 (smaller alliance)
- Alliance 3: warmasters with id 15 and 16
- Alliance 4: remaining warmasters distributed
- Alliance 5: remaining warmasters distributed
"""

from yoyo import step
import sqlite3

def redistribute_alliances(conn):
    """Redistribute warmasters among 5 alliances"""
    
    cursor = conn.cursor()
    
    # Clear existing alliances
    cursor.execute("DELETE FROM alliances")
    print("Cleared existing alliances")
    
    # Get all warmasters with nicknames
    cursor.execute("""
        SELECT id, nickname FROM warmasters 
        WHERE nickname IS NOT NULL AND nickname != '' 
        ORDER BY id
    """)
    
    warmasters = cursor.fetchall()
    print(f"Found {len(warmasters)} warmasters with nicknames:")
    for wm in warmasters:
        print(f"  ID: {wm[0]}, Nickname: {wm[1]}")
    
    # Create alliance names
    alliance_names = [
        "Crimson Legion",
        "Shadow Pact", 
        "Iron Brotherhood",
        "Storm Guard",
        "Void Seekers"
    ]
    
    # Define fixed assignments
    fixed_assignments = {
        1: 1,   # Alliance 1
        12: 1,  # Alliance 1
        7: 2,   # Alliance 2 (smaller)
        11: 2,  # Alliance 2 (smaller)
        15: 3,  # Alliance 3
        16: 3   # Alliance 3
    }
    
    # Track assignments
    assignments = {}
    unassigned = []
    
    # Process fixed assignments
    for warmaster_id, nickname in warmasters:
        if warmaster_id in fixed_assignments:
            alliance_id = fixed_assignments[warmaster_id]
            assignments[warmaster_id] = (alliance_id, alliance_names[alliance_id-1])
            print(f"Fixed assignment: Warmaster {warmaster_id} ({nickname}) -> Alliance {alliance_id} ({alliance_names[alliance_id-1]})")
        else:
            unassigned.append((warmaster_id, nickname))
    
    # Distribute remaining warmasters between alliances 4 and 5
    # Try to balance them, but alliance 2 should stay smaller
    alliance_4_count = len(unassigned) // 2
    alliance_5_count = len(unassigned) - alliance_4_count
    
    print(f"Distributing {len(unassigned)} unassigned warmasters:")
    print(f"  Alliance 4: {alliance_4_count} warmasters")
    print(f"  Alliance 5: {alliance_5_count} warmasters")
    
    # Assign to alliance 4
    for i in range(alliance_4_count):
        warmaster_id, nickname = unassigned[i]
        assignments[warmaster_id] = (4, alliance_names[3])
        print(f"  Warmaster {warmaster_id} ({nickname}) -> Alliance 4 ({alliance_names[3]})")
    
    # Assign to alliance 5
    for i in range(alliance_4_count, len(unassigned)):
        warmaster_id, nickname = unassigned[i]
        assignments[warmaster_id] = (5, alliance_names[4])
        print(f"  Warmaster {warmaster_id} ({nickname}) -> Alliance 5 ({alliance_names[4]})")
    
    # Insert alliance records
    for warmaster_id, (alliance_id, alliance_name) in assignments.items():
        cursor.execute("""
            INSERT OR REPLACE INTO alliances (id, warmaster_id, alliance_name)
            VALUES (?, ?, ?)
        """, (warmaster_id, warmaster_id, alliance_name))
    
    # Print final distribution
    print("\n=== Final Alliance Distribution ===")
    for alliance_id, alliance_name in enumerate(alliance_names, 1):
        members = [wm_id for wm_id, (a_id, _) in assignments.items() if a_id == alliance_id]
        print(f"Alliance {alliance_id} - {alliance_name}: {len(members)} members")
        for wm_id in members:
            wm_nickname = next(nickname for w_id, nickname in warmasters if w_id == wm_id)
            print(f"  - Warmaster {wm_id}: {wm_nickname}")
    
    conn.commit()
    print(f"Successfully redistributed {len(assignments)} warmasters among 5 alliances")

def rollback_alliances(conn):
    """Rollback function - clear alliances"""
    cursor = conn.cursor()
    cursor.execute("DELETE FROM alliances")
    conn.commit()
    print("Rolled back: cleared all alliance assignments")

# Define the migration steps
steps = [
    step(redistribute_alliances, rollback_alliances)
]