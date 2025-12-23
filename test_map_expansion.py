#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test for map expansion when a player is assigned to an alliance.
"""
import sys
import os

# Add CareBot directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'CareBot', 'CareBot'))

import asyncio
import sqlite3

import sqllite_helper


def create_test_db():
    """Create a test database with initial data."""
    db_path = '/tmp/test_map_expansion.db'
    
    # Remove existing database
    if os.path.exists(db_path):
        os.remove(db_path)
    
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    
    # Create tables
    cur.execute('''
        CREATE TABLE warmasters (
            id INTEGER PRIMARY KEY,
            telegram_id TEXT UNIQUE,
            alliance INTEGER DEFAULT 0,
            nickname TEXT
        )
    ''')
    
    cur.execute('''
        CREATE TABLE alliances (
            id INTEGER PRIMARY KEY,
            name TEXT,
            resources INTEGER DEFAULT 0
        )
    ''')
    
    cur.execute('''
        CREATE TABLE map (
            id INTEGER PRIMARY KEY,
            planet_id INTEGER,
            state TEXT,
            patron INTEGER,
            has_warehouse INTEGER DEFAULT 0
        )
    ''')
    
    cur.execute('''
        CREATE TABLE edges (
            id INTEGER PRIMARY KEY,
            left_hexagon INTEGER,
            right_hexagon INTEGER,
            state INTEGER
        )
    ''')
    
    # Insert test alliances
    cur.execute("INSERT INTO alliances (id, name, resources) VALUES (1, 'Alliance A', 100)")
    cur.execute("INSERT INTO alliances (id, name, resources) VALUES (2, 'Alliance B', 100)")
    
    # Insert initial warmasters (none in alliances yet)
    cur.execute("INSERT INTO warmasters (telegram_id, alliance, nickname) VALUES ('12345', 0, 'Player1')")
    cur.execute("INSERT INTO warmasters (telegram_id, alliance, nickname) VALUES ('67890', 0, 'Player2')")
    
    # Create initial map with just center hex (radius 0)
    cur.execute('''
        INSERT INTO map (id, planet_id, state, patron, has_warehouse)
        VALUES (1, 1, 'Леса', 1, 0)
    ''')
    
    conn.commit()
    conn.close()
    
    return db_path


async def test_map_expansion():
    """Test that map expands when player is assigned to an alliance."""
    print("\n=== Testing Map Expansion on Player Registration ===\n")
    
    # Create test database
    db_path = create_test_db()
    print(f"✓ Created test database: {db_path}")
    
    # Set database path for sqllite_helper
    sqllite_helper.DATABASE_PATH = db_path
    
    # Check initial state
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    
    cur.execute("SELECT COUNT(*) FROM map")
    initial_hex_count = cur.fetchone()[0]
    print(f"✓ Initial hex count: {initial_hex_count}")
    
    cur.execute("SELECT COUNT(*) FROM edges")
    initial_edge_count = cur.fetchone()[0]
    print(f"✓ Initial edge count: {initial_edge_count}")
    
    cur.execute("SELECT COUNT(*) FROM warmasters WHERE alliance != 0")
    initial_alliance_count = cur.fetchone()[0]
    print(f"✓ Initial warmasters with alliance: {initial_alliance_count}")
    
    conn.close()
    
    # Assign first player to alliance
    print("\n--- Assigning Player1 to Alliance 1 ---")
    await sqllite_helper.set_warmaster_alliance('12345', 1)
    
    # Check map expansion
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    
    cur.execute("SELECT COUNT(*) FROM map")
    hex_count_after_first = cur.fetchone()[0]
    print(f"✓ Hex count after first assignment: {hex_count_after_first}")
    
    cur.execute("SELECT COUNT(*) FROM edges")
    edge_count_after_first = cur.fetchone()[0]
    print(f"✓ Edge count after first assignment: {edge_count_after_first}")
    
    # Ring 0 = 1 hex, Ring 1 = 6 hexes, total = 7
    expected_hexes_after_first = 7
    if hex_count_after_first == expected_hexes_after_first:
        print(f"✓ Map expanded correctly: {initial_hex_count} → {hex_count_after_first} hexes")
    else:
        print(f"✗ Map expansion failed: expected {expected_hexes_after_first}, got {hex_count_after_first}")
        conn.close()
        return False
    
    conn.close()
    
    # Assign second player to alliance
    print("\n--- Assigning Player2 to Alliance 2 ---")
    await sqllite_helper.set_warmaster_alliance('67890', 2)
    
    # Check map expansion again
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    
    cur.execute("SELECT COUNT(*) FROM map")
    hex_count_after_second = cur.fetchone()[0]
    print(f"✓ Hex count after second assignment: {hex_count_after_second}")
    
    cur.execute("SELECT COUNT(*) FROM edges")
    edge_count_after_second = cur.fetchone()[0]
    print(f"✓ Edge count after second assignment: {edge_count_after_second}")
    
    # Ring 0 = 1, Ring 1 = 6, Ring 2 = 12, total = 19
    expected_hexes_after_second = 19
    if hex_count_after_second == expected_hexes_after_second:
        print(f"✓ Map expanded correctly: {hex_count_after_first} → {hex_count_after_second} hexes")
    else:
        print(f"✗ Map expansion failed: expected {expected_hexes_after_second}, got {hex_count_after_second}")
        conn.close()
        return False
    
    # Verify edges are created properly
    print("\n--- Verifying Edge Connectivity ---")
    cur.execute('''
        SELECT COUNT(DISTINCT e.id) 
        FROM edges e
        JOIN map m1 ON e.left_hexagon = m1.id
        JOIN map m2 ON e.right_hexagon = m2.id
    ''')
    valid_edges = cur.fetchone()[0]
    print(f"✓ Valid edges (connected to existing hexes): {valid_edges}")
    
    if valid_edges == edge_count_after_second:
        print("✓ All edges are properly connected")
    else:
        print(f"✗ Some edges are invalid: {edge_count_after_second - valid_edges} broken edges")
    
    conn.close()
    
    # Test that reassigning to same alliance doesn't expand
    print("\n--- Testing Reassignment to Same Alliance ---")
    await sqllite_helper.set_warmaster_alliance('12345', 1)
    
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    
    cur.execute("SELECT COUNT(*) FROM map")
    hex_count_after_reassign = cur.fetchone()[0]
    
    if hex_count_after_reassign == hex_count_after_second:
        print(f"✓ Map did not expand on reassignment: {hex_count_after_reassign} hexes")
    else:
        print(f"✗ Map incorrectly expanded on reassignment: {hex_count_after_second} → {hex_count_after_reassign}")
        conn.close()
        return False
    
    conn.close()
    
    # Test that assigning to alliance 0 (no alliance) doesn't expand
    print("\n--- Testing Assignment to No Alliance (0) ---")
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    cur.execute("INSERT INTO warmasters (telegram_id, alliance, nickname) VALUES ('99999', 0, 'Player3')")
    conn.commit()
    conn.close()
    
    await sqllite_helper.set_warmaster_alliance('99999', 0)
    
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    
    cur.execute("SELECT COUNT(*) FROM map")
    hex_count_after_no_alliance = cur.fetchone()[0]
    
    if hex_count_after_no_alliance == hex_count_after_second:
        print(f"✓ Map did not expand for alliance 0: {hex_count_after_no_alliance} hexes")
    else:
        print(f"✗ Map incorrectly expanded for alliance 0: {hex_count_after_second} → {hex_count_after_no_alliance}")
        conn.close()
        return False
    
    conn.close()
    
    print("\n=== All Tests Passed ✓ ===\n")
    return True


if __name__ == "__main__":
    try:
        result = asyncio.run(test_map_expansion())
        sys.exit(0 if result else 1)
    except Exception as e:
        print(f"\n✗ Error during testing: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
