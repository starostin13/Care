"""
Migration 017: Clear old missions and allow cell re-selection with new logic

This migration clears all missions that were created before the cell selection
logic was updated to randomly select from defender's adjacent hexes.

The new logic:
1. Finds all hexes adjacent to attacker's alliance hexes
2. Filters to only hexes belonging to defender's alliance
3. Randomly selects one of those adjacent hexes

Old missions with cell=2 (hardcoded) or any specific cell assignment
should be cleared to be regenerated with the new logic.
"""

from yoyo import step


def clear_old_missions(conn):
    """Clear missions to allow regeneration with new logic."""
    cursor = conn.cursor()
    
    # Count current missions
    cursor.execute("SELECT COUNT(*) FROM mission_stack")
    initial_count = cursor.fetchone()[0]
    
    print(f"Initial mission count: {initial_count}")
    
    # Delete all missions to force regeneration with new logic
    cursor.execute("DELETE FROM mission_stack")
    affected_rows = cursor.rowcount
    
    print(f"✅ Deleted {affected_rows} missions")
    print(f"✅ Missions will be regenerated with new cell selection logic:")
    print(f"   - Find hexes adjacent to attacker's territory")
    print(f"   - Randomly select from defender's adjacent hexes")
    print(f"   - Falls back to random defender hex if no adjacent found")
    
    conn.commit()


steps = [step(clear_old_missions)]
