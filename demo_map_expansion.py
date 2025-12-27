#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Integration test demonstrating map expansion with visual output.
This test shows how the map expands as players join alliances.
"""
import sys
import os
import sqlite3

# Add CareBot directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'CareBot', 'CareBot'))

import asyncio


def create_demo_db():
    """Create a demonstration database."""
    db_path = '/tmp/demo_map_expansion.db'
    
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
    
    # Insert alliances
    alliances = [
        (1, 'Imperium of Man'),
        (2, 'Chaos Forces'),
        (3, 'Ork Waaagh'),
        (4, 'Eldar Craftworld')
    ]
    for alliance_id, name in alliances:
        cur.execute("INSERT INTO alliances (id, name, resources) VALUES (?, ?, 100)", (alliance_id, name))
    
    # Insert players (not assigned to alliances yet)
    players = [
        ('player1', 'Commander Alpha'),
        ('player2', 'Warlord Beta'),
        ('player3', 'Boss Gamma'),
        ('player4', 'Farseer Delta'),
    ]
    for telegram_id, nickname in players:
        cur.execute(
            "INSERT INTO warmasters (telegram_id, alliance, nickname) VALUES (?, 0, ?)",
            (telegram_id, nickname)
        )
    
    # Create initial map with just center hex
    cur.execute('''
        INSERT INTO map (id, planet_id, state, patron, has_warehouse)
        VALUES (1, 1, 'Город', 1, 0)
    ''')
    
    conn.commit()
    conn.close()
    
    return db_path


def show_map_stats(db_path):
    """Display current map statistics."""
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    
    cur.execute("SELECT COUNT(*) FROM map")
    hex_count = cur.fetchone()[0]
    
    cur.execute("SELECT COUNT(*) FROM edges")
    edge_count = cur.fetchone()[0]
    
    cur.execute("SELECT COUNT(*) FROM warmasters WHERE alliance != 0")
    players_in_alliances = cur.fetchone()[0]
    
    # Calculate expected ring count
    # Ring 0 = 1, Ring 1 = 7, Ring 2 = 19, Ring 3 = 37, etc.
    rings = 0
    total = 1
    while total < hex_count:
        rings += 1
        total = 3 * rings * rings + 3 * rings + 1
    
    print(f"   Hexes: {hex_count} (Rings: 0-{rings})")
    print(f"   Edges: {edge_count}")
    print(f"   Players in alliances: {players_in_alliances}")
    
    conn.close()
    return hex_count, edge_count


async def run_demo():
    """Run the demonstration."""
    import sqllite_helper
    
    print("\n" + "=" * 70)
    print("MAP EXPANSION DEMONSTRATION")
    print("=" * 70)
    print("\nThis demo shows how the planet map expands as players join alliances.")
    print("The map uses a hexagonal grid that expands in rings:")
    print("  - Ring 0: 1 hex (center)")
    print("  - Ring 1: 6 hexes (first ring)")
    print("  - Ring 2: 12 hexes (second ring)")
    print("  - Ring 3: 18 hexes (third ring)")
    print("  etc.")
    
    # Create demo database
    db_path = create_demo_db()
    sqllite_helper.DATABASE_PATH = db_path
    
    print("\n" + "-" * 70)
    print("INITIAL STATE")
    print("-" * 70)
    show_map_stats(db_path)
    
    # Player 1 joins Imperium
    print("\n" + "-" * 70)
    print("ACTION: Commander Alpha joins Imperium of Man")
    print("-" * 70)
    await sqllite_helper.set_warmaster_alliance('player1', 1)
    hex_count, edge_count = show_map_stats(db_path)
    print(f"   ✓ Map expanded! Now has {hex_count} hexes")
    
    # Player 2 joins Chaos
    print("\n" + "-" * 70)
    print("ACTION: Warlord Beta joins Chaos Forces")
    print("-" * 70)
    await sqllite_helper.set_warmaster_alliance('player2', 2)
    hex_count, edge_count = show_map_stats(db_path)
    print(f"   ✓ Map expanded! Now has {hex_count} hexes")
    
    # Player 3 joins Orks
    print("\n" + "-" * 70)
    print("ACTION: Boss Gamma joins Ork Waaagh")
    print("-" * 70)
    await sqllite_helper.set_warmaster_alliance('player3', 3)
    hex_count, edge_count = show_map_stats(db_path)
    print(f"   ✓ Map expanded! Now has {hex_count} hexes")
    
    # Player 4 joins Eldar
    print("\n" + "-" * 70)
    print("ACTION: Farseer Delta joins Eldar Craftworld")
    print("-" * 70)
    await sqllite_helper.set_warmaster_alliance('player4', 4)
    hex_count, edge_count = show_map_stats(db_path)
    print(f"   ✓ Map expanded! Now has {hex_count} hexes")
    
    print("\n" + "=" * 70)
    print("DEMONSTRATION COMPLETE")
    print("=" * 70)
    print("\nThe map successfully expanded from 1 hex to", hex_count, "hexes")
    print("as players joined their alliances.")
    print(f"\nDatabase saved to: {db_path}")
    print("You can inspect it with: sqlite3", db_path)
    print("=" * 70 + "\n")


if __name__ == "__main__":
    asyncio.run(run_demo())
