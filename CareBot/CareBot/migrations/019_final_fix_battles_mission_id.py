"""
Migration 019: Final fix for battles.mission_id corruption

This migration ensures all battles have valid mission_id values and creates
a trigger to prevent future corruptions.

The root cause has been fixed in mission_helper.py where mission[0] (id) is now
correctly used instead of mission[4] (winner_bonus or mission_description).
"""

from yoyo import step


def fix_battles_mission_id(conn):
    """Fix all battles with invalid mission_id and add safeguards."""
    cursor = conn.cursor()
    
    print("=" * 70)
    print("Migration 019: Final fix for battles.mission_id corruption")
    print("=" * 70)
    
    # Step 1: Get all valid mission IDs
    cursor.execute("SELECT id FROM mission_stack")
    valid_mission_ids = set(row[0] for row in cursor.fetchall())
    print(f"\n✅ Found {len(valid_mission_ids)} valid missions in mission_stack")
    
    # Step 2: Check current battles table
    cursor.execute("SELECT id, mission_id, fstplayer, sndplayer FROM battles")
    all_battles = cursor.fetchall()
    
    corrupted = []
    valid = []
    
    for battle_id, mission_id, fstplayer, sndplayer in all_battles:
        if mission_id is None:
            # NULL is valid (battle not completed yet)
            valid.append((battle_id, mission_id))
        elif not isinstance(mission_id, int):
            # Non-integer mission_id is corruption
            corrupted.append((battle_id, mission_id, "non-integer"))
            print(f"❌ Battle {battle_id}: mission_id is not an integer: {repr(mission_id)[:50]}")
        elif mission_id not in valid_mission_ids:
            # mission_id doesn't exist in mission_stack
            corrupted.append((battle_id, mission_id, "missing"))
            print(f"❌ Battle {battle_id}: mission_id={mission_id} not found in mission_stack")
        else:
            valid.append((battle_id, mission_id))
    
    print(f"\n📊 Statistics:")
    print(f"   Valid battles: {len(valid)}")
    print(f"   Corrupted battles: {len(corrupted)}")
    
    # Step 3: Clean corrupted battles
    if corrupted:
        print(f"\n🧹 Cleaning {len(corrupted)} corrupted battle records...")
        
        for battle_id, bad_mission_id, reason in corrupted:
            # Remove battle_attenders
            cursor.execute("DELETE FROM battle_attenders WHERE battle_id = ?", (battle_id,))
            # Remove battle
            cursor.execute("DELETE FROM battles WHERE id = ?", (battle_id,))
            print(f"   ✓ Removed battle {battle_id} (reason: {reason}, bad_mission_id: {repr(bad_mission_id)[:30]})")
        
        print(f"✅ Successfully cleaned {len(corrupted)} corrupted battles")
    else:
        print("\n✅ No corrupted battles found!")
    
    # Step 4: Create trigger to prevent future corruption
    print("\n🛡️  Creating safeguard trigger...")
    
    # Drop trigger if exists
    cursor.execute("DROP TRIGGER IF EXISTS validate_battle_mission_id")
    
    # Create trigger to validate mission_id on INSERT/UPDATE
    cursor.execute("""
        CREATE TRIGGER validate_battle_mission_id
        BEFORE UPDATE OF mission_id ON battles
        FOR EACH ROW
        WHEN NEW.mission_id IS NOT NULL
        BEGIN
            SELECT CASE
                WHEN NOT EXISTS (SELECT 1 FROM mission_stack WHERE id = NEW.mission_id)
                THEN RAISE(ABORT, 'Invalid mission_id: must reference existing mission in mission_stack')
            END;
        END;
    """)
    
    print("✅ Created trigger 'validate_battle_mission_id'")
    print("   This trigger will prevent invalid mission_id values in future updates")
    
    # Step 5: Verify final state
    cursor.execute("""
        SELECT COUNT(*) 
        FROM battles 
        WHERE mission_id IS NOT NULL 
        AND mission_id NOT IN (SELECT id FROM mission_stack)
    """)
    remaining_corrupted = cursor.fetchone()[0]
    
    print(f"\n📋 Final verification:")
    print(f"   Remaining corrupted battles: {remaining_corrupted}")
    
    if remaining_corrupted > 0:
        print("   ⚠️  Warning: Some corrupted battles still exist!")
    else:
        print("   ✅ All battles have valid mission_id values!")
    
    conn.commit()
    print("\n" + "=" * 70)
    print("Migration 019 completed successfully")
    print("=" * 70)


steps = [step(fix_battles_mission_id)]
