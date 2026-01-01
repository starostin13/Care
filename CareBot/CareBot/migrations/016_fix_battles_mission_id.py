"""
Migration 016: Fix incorrect mission_id values in battles table
and remove test/corrupted battle records

Problem: Some battle records have mission_id set to invalid values:
- mission_id equal to battle_id (off-by-one errors)
- mission_id containing text descriptions instead of IDs
- mission_id pointing to non-existent missions

This migration removes all corrupted battle records where mission_id
is not NULL and does not reference an existing mission in mission_stack.

Root cause: Bug in write_battle_result() which was passing battle_id
instead of mission_id to add_battle_result(). This has been fixed in
the code, but corrupted records need to be cleaned up.
"""

from yoyo import step


def clean_corrupted_battles(conn):
    """Remove all battle records with invalid mission_id values."""
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
        print(f"\n🧹 Removing {len(corrupted_battles)} corrupted battle records...")
        
        # Remove corrupted battles and their participants
        for battle_id in corrupted_battles:
            # Remove battle_attenders records
            cursor.execute("DELETE FROM battle_attenders WHERE battle_id = ?", (battle_id,))
            # Remove battle record
            cursor.execute("DELETE FROM battles WHERE id = ?", (battle_id,))
            print(f"   Removed battle {battle_id}")
        
        print(f"✅ Successfully removed {len(corrupted_battles)} corrupted battles")
    else:
        print("✅ No corrupted battles found")
    
    conn.commit()


steps = [step(clean_corrupted_battles)]
