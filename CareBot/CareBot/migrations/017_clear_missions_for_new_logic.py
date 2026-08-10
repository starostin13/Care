"""
Migration 017: Clear old missions and allow cell re-selection with new logic

This migration originally deleted all missions. That behavior can orphan
historical battles, so it now removes only missions that are not referenced
by any battle.

The new logic:
1. Finds all hexes adjacent to attacker's alliance hexes
2. Filters to only hexes belonging to defender's alliance
3. Randomly selects one of those adjacent hexes
"""

from yoyo import step


def clear_old_missions(conn):
    """Remove only unreferenced missions to avoid losing battle history."""
    cursor = conn.cursor()
    
    # Count current missions
    cursor.execute("SELECT COUNT(*) FROM mission_stack")
    initial_count = cursor.fetchone()[0]
    
    print(f"Initial mission count: {initial_count}")
    
    # Keep missions that are referenced by any battle to preserve history.
    cursor.execute("""
        DELETE FROM mission_stack
        WHERE id NOT IN (
            SELECT DISTINCT mission_id
            FROM battles
            WHERE mission_id IS NOT NULL
        )
    """)
    affected_rows = cursor.rowcount
    
    print(f"✅ Deleted {affected_rows} unreferenced missions")
    print(f"✅ Missions will be regenerated with new cell selection logic:")
    print(f"   - Find hexes adjacent to attacker's territory")
    print(f"   - Randomly select from defender's adjacent hexes")
    print(f"   - Falls back to random defender hex if no adjacent found")
    
    conn.commit()


steps = [step(clear_old_missions)]
