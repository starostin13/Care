"""
Migration 021: Fix NULL mission IDs in mission_stack

This migration ensures all missions have valid id values.
If a mission has NULL id, we generate a new one and update the database.
"""

from yoyo import step


def fix_null_mission_ids(conn):
    """Fix all missions with NULL id values."""
    cursor = conn.cursor()

    print("=" * 70)
    print("Migration 021: Fix NULL mission IDs in mission_stack")
    print("=" * 70)

    # Step 1: Check for missions with NULL id
    cursor.execute("""
        SELECT deploy, rules, cell, mission_description, winner_bonus, locked, created_date
        FROM mission_stack
        WHERE id IS NULL
    """)
    null_id_missions = cursor.fetchall()

    if not null_id_missions:
        print("\n✅ No missions with NULL id found!")
        print("=" * 70)
        return

    print(f"\n⚠️  Found {len(null_id_missions)} missions with NULL id")

    # Step 2: For each mission with NULL id, delete and re-insert to get auto-generated id
    fixed_count = 0
    for mission_data in null_id_missions:
        deploy, rules, cell, mission_description, winner_bonus, locked, created_date = mission_data

        # Delete the NULL id mission
        cursor.execute("""
            DELETE FROM mission_stack
            WHERE id IS NULL
            AND deploy = ?
            AND rules = ?
            AND ((cell IS NULL AND ? IS NULL) OR cell = ?)
            AND mission_description = ?
            LIMIT 1
        """, (deploy, rules, cell, cell, mission_description))

        # Re-insert to get auto-generated id
        cursor.execute("""
            INSERT INTO mission_stack (deploy, rules, cell, mission_description, winner_bonus, locked, created_date)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (deploy, rules, cell, mission_description, winner_bonus, locked, created_date))

        # Get the new id
        new_id = cursor.lastrowid
        fixed_count += 1

        print(f"   ✓ Fixed mission: {rules}/{deploy} -> new id={new_id}")

    print(f"\n✅ Successfully fixed {fixed_count} missions with NULL id")

    # Step 3: Verify no NULL ids remain
    cursor.execute("SELECT COUNT(*) FROM mission_stack WHERE id IS NULL")
    remaining_null = cursor.fetchone()[0]

    print(f"\n📋 Final verification:")
    print(f"   Remaining NULL id missions: {remaining_null}")

    if remaining_null > 0:
        print("   ⚠️  Warning: Some NULL id missions still exist!")
    else:
        print("   ✅ All missions now have valid id values!")

    conn.commit()
    print("\n" + "=" * 70)
    print("Migration 021 completed successfully")
    print("=" * 70)


steps = [step(fix_null_mission_ids)]
