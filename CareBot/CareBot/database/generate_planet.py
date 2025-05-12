import sqlite3
import random
from collections import Counter

# Константы
PLANET_ID = 1
STATES = [
    "пустыня",
    "лес",
    "черта города",
    "скалы",
    "токсичная зона",
    "разрушенные руины",
    "заражённая чаща"
]

HEX_DIRECTIONS = [
    (1, 0), (1, -1), (0, -1),
    (-1, 0), (-1, 1), (0, 1)
]

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

def generate_map_and_edges(db_path='your_database.sqlite'):
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()

    # Получаем количество колец по warmasters
    cur.execute("SELECT COUNT(*) FROM warmasters WHERE alliance != 0")
    ring_count = cur.fetchone()[0]

    # Получаем все patron id (из alliances)
    cur.execute("SELECT id FROM alliances")
    patron_ids = [row[0] for row in cur.fetchall()]
    if not patron_ids:
        raise ValueError("Нет записей в таблице alliances")

    hex_map = {}  # (q, r) -> {'id', 'state', ...}
    hex_id = 1
    edge_id = 1

    for radius in range(ring_count + 1):
        for q, r in hex_ring(0, 0, radius):
            coord = (q, r)

            # Выбор state
            if radius == 0:
                state = random.choice(STATES)
            else:
                if random.random() < 0.5:
                    neighbors = hex_neighbors(q, r)
                    state = most_common_state(neighbors, hex_map)
                else:
                    state = random.choice(STATES)

            has_warehouse = 1 if random.random() < 0.1 else 0
            patron = random.choice(patron_ids)

            # Вставка в map
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

    # Вставка ребер
    for (q, r), hex_data in hex_map.items():
        current_id = hex_data['id']
        for nq, nr in hex_neighbors(q, r):
            neighbor = hex_map.get((nq, nr))
            if neighbor:
                neighbor_id = neighbor['id']
                # Вставляем только один раз для каждой пары
                if current_id < neighbor_id:
                    cur.execute("""
                        INSERT INTO edges (id, left_hexagon, right_hexagon, state)
                        VALUES (?, ?, ?, NULL)
                    """, (edge_id, current_id, neighbor_id))
                    edge_id += 1

    conn.commit()
    conn.close()

generate_map_and_edges()
