"""
Migration 016: Fix incorrect mission_id values in battles table
and preserve historical battle records

Problem: Some battle records have mission_id set to invalid values:
- mission_id equal to battle_id (off-by-one errors)
- mission_id containing text descriptions instead of IDs
- mission_id pointing to non-existent missions

This migration now keeps corrupted battle records by setting invalid
mission_id values to NULL, instead of deleting battles.

Root cause: Bug in write_battle_result() which was passing battle_id
instead of mission_id to add_battle_result(). This has been fixed in
the code, but corrupted records need to be cleaned up.
"""

from yoyo import step


def clean_corrupted_battles(conn):
    """Set invalid mission_id values to NULL while preserving battles."""
    cursor = conn.cursor()
    
    # First, get all valid mission IDs
    cursor.execute("SELECT id FROM mission_stack")
    valid_mission_ids = set(row[0] for row in cursor.fetchall())
    
    print(f"Valid mission IDs: {sorted(valid_mission_ids)}")
    
    # Get all battles with invalid mission_id
    cursor.execute("SELECT id, mission_id FROM battles")
    corrupted_battles = []
    
    for battle_id, mission_id in cursor.fetchall():
        # Check if mission_id is valid
        if mission_id is None:
            # NULL mission_id is valid (initial state before result entered)
            continue
        
        if isinstance(mission_id, str):
            # Text in mission_id field is corrupted
            corrupted_battles.append(battle_id)
            print(f"❌ Battle {battle_id}: mission_id is text: {mission_id[:50]}...")
        elif mission_id not in valid_mission_ids:
            # mission_id doesn't reference existing mission
            corrupted_battles.append(battle_id)
            print(f"❌ Battle {battle_id}: mission_id={mission_id} (not found in mission_stack)")
        else:
            print(f"✅ Battle {battle_id}: mission_id={mission_id} (valid)")
    
    if corrupted_battles:
        print(f"\n🧹 Normalizing {len(corrupted_battles)} corrupted battle records...")

        for battle_id in corrupted_battles:
            cursor.execute("UPDATE battles SET mission_id = NULL WHERE id = ?", (battle_id,))
            print(f"   Updated battle {battle_id}: mission_id -> NULL")

        print(f"✅ Successfully normalized {len(corrupted_battles)} corrupted battles")
    else:
        print("✅ No corrupted battles found")
    
    conn.commit()


steps = [step(clean_corrupted_battles)]
