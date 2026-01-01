"""
Migration 015: Fix hardcoded cell=2 values in mission_stack

Issue: Historical test data had all missions set to cell=2, which violates the design
principle that cells should be dynamically assigned based on alliance hexes.

Fix: Set cell to NULL for all missions so they can be dynamically determined
when next used.

Created: 2026-01-01
"""
from yoyo import step

def fix_hardcoded_cells(conn):
    """Safely fix hardcoded cell=2 values"""
    cursor = conn.cursor()
    
    # Get current state
    cursor.execute("SELECT COUNT(*) FROM mission_stack WHERE cell=2")
    count_before = cursor.fetchone()[0]
    
    print(f"📊 Found {count_before} missions with hardcoded cell=2")
    
    if count_before > 0:
        # Clear the hardcoded values - set to NULL so they'll be dynamically assigned
        cursor.execute("UPDATE mission_stack SET cell=NULL WHERE cell=2")
        print(f"✅ Updated {count_before} missions: cell=2 -> cell=NULL")
        
        # Verify the update
        cursor.execute("SELECT COUNT(*) FROM mission_stack WHERE cell IS NULL")
        null_count = cursor.fetchone()[0]
        print(f"✅ Verified: {null_count} missions now have cell=NULL")
    else:
        print("✅ No hardcoded cell=2 values found - nothing to fix")

steps = [step(fix_hardcoded_cells)]
