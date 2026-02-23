#!/usr/bin/env python3
"""
Скрипт для очистки карты планеты и генерации новой
Использует ТОЛЬКО ASCII символы для совместимости с production
"""
import sqlite3
import random
import os
from collections import Counter

# Constants
PLANET_ID = 1
STATES = [
    "Forest",
    "Tundra/Snow",
    "Desert", 
    "Poisoned Lands",
    "Factory",
    "City",
    "Ruined City",
    "Underground Systems",
    "Ship Wreckage", 
    "Junkyard",
    "Temple Quarter",
    "Warp-altered Space"
]

HEX_DIRECTIONS = [
    (1, 0), (1, -1), (0, -1),
    (-1, 0), (-1, 1), (0, 1)
]

def clear_planet_data(db_path):
    """Clear existing planet data from map and edges tables"""
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    
    print("Clearing existing planet data...")
    
    # Clear map table
    cur.execute("DELETE FROM map")
    print(f"Cleared map table")
    
    # Clear edges table  
    cur.execute("DELETE FROM edges")
    print(f"Cleared edges table")
    
    # Reset autoincrement counters
    cur.execute("DELETE FROM sqlite_sequence WHERE name IN ('map', 'edges')")
    
    conn.commit()
    conn.close()
    print("Planet data cleared successfully")

def hex_ring(center_q, center_r, radius):
    if radius == 0:
        return [(center_q, center_r)]
    results = []
    q, r = center_q + HEX_DIRECTIONS[4][0] * radius, center_r + HEX_DIRECTIONS[4][1] * radius
    for i in range(6):
        for _ in range(radius):
            results.append((q, r))
            dq, dr = HEX_DIRECTIONS[i]
            q += dq
            r += dr
    return results

def hex_neighbors(q, r):
    return [(q + dq, r + dr) for dq, dr in HEX_DIRECTIONS]

def most_common_state(neighbor_coords, hex_map):
    states = [hex_map[coord]["state"] for coord in neighbor_coords if coord in hex_map]
    if not states:
        return random.choice(STATES)
    return Counter(states).most_common(1)[0][0]

def generate_new_planet(db_path):
    """Generate new planet map and edges"""
    
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()

    # Get ring count from warmasters
    cur.execute("SELECT COUNT(*) FROM warmasters WHERE alliance != 0")
    ring_count = cur.fetchone()[0]
    print(f"Generating planet with {ring_count} rings")

    # Get all patron ids from alliances
    cur.execute("SELECT id FROM alliances")
    patron_ids = [row[0] for row in cur.fetchall()]
    if not patron_ids:
        raise ValueError("No data in alliances table")

    hex_map = {}  # (q, r) -> {'id', 'state', ...}
    hex_id = 1
    edge_id = 1

    for radius in range(ring_count + 1):
        for q, r in hex_ring(0, 0, radius):
            coord = (q, r)

            # Choose state
            if radius == 0:
                state = random.choice(STATES)
            else:
                if random.random() < 0.1:
                    neighbors = hex_neighbors(q, r)
                    state = most_common_state(neighbors, hex_map)
                else:
                    state = random.choice(STATES)

            has_warehouse = 1 if random.random() < 0.1 else 0
            patron = random.choice(patron_ids)

            # Insert into map
            cur.execute("""
                INSERT INTO map (id, planet_id, state, patron, has_warehouse)
                VALUES (?, ?, ?, ?, ?)
            """, (hex_id, PLANET_ID, state, patron, has_warehouse))

            hex_map[coord] = {
                'id': hex_id,
                'state': state,
                'patron': patron
            }
            hex_id += 1

    # Create edges
    for (q, r), hex_data in hex_map.items():
        current_id = hex_data['id']
        for nq, nr in hex_neighbors(q, r):
            neighbor = hex_map.get((nq, nr))
            if neighbor:
                neighbor_id = neighbor['id']
                # Add only one connection for each pair
                if current_id < neighbor_id:
                    cur.execute("""
                        INSERT INTO edges (id, left_hexagon, right_hexagon, state)
                        VALUES (?, ?, ?, NULL)
                    """, (edge_id, current_id, neighbor_id))
                    edge_id += 1

    conn.commit()
    conn.close()
    print(f"New planet generated: {hex_id-1} hexes, {edge_id-1} edges")

def main():
    """Main function to clear old planet and generate new one"""
    
    # Determine database path
    db_path = None
    if os.path.exists('/app/data/game_database.db'):
        db_path = '/app/data/game_database.db'
    elif os.path.exists('../db/game_database.db'):
        db_path = '../db/game_database.db'
    elif os.path.exists('game_database.db'):
        db_path = 'game_database.db'
    else:
        raise FileNotFoundError("Database not found")
    
    print(f"Using database: {db_path}")
    
    # Clear existing data
    clear_planet_data(db_path)
    
    # Generate new planet
    generate_new_planet(db_path)
    
    print("Planet regeneration completed successfully!")

if __name__ == "__main__":
    main()