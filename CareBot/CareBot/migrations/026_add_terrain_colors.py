"""
Migration 026: Add terrain_colors table for customizable terrain hex fill colors.
Colors stored here override the built-in defaults in map_exporter.TERRAIN_STYLES.
"""
from yoyo import step


def add_terrain_colors(conn):
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS terrain_colors (
            name  TEXT PRIMARY KEY,
            color TEXT NOT NULL
        )
    """)

    defaults = [
        ("Леса",                              "#2E7D32"),
        ("Тундра/снег",                       "#E3F2FD"),
        ("Пустыня",                           "#D4A373"),
        ("Отравленные земли",                 "#6B8E23"),
        ("Завод",                             "#6C757D"),
        ("Город",                             "#5C6BC0"),
        ("Разрушенный город",                 "#8D6E63"),
        ("Подземные системы",                 "#37474F"),
        ("Останки корабля",                   "#B0BEC5"),
        ("Свалка",                            "#8D6E63"),
        ("Храмовый квартал",                  "#FBC02D"),
        ("Изменённое варпом пространство",    "#6A1B9A"),
    ]

    for name, color in defaults:
        cursor.execute(
            "INSERT OR IGNORE INTO terrain_colors (name, color) VALUES (?, ?)",
            (name, color),
        )

    print("✅ Migration 026: terrain_colors table created with default colors")


steps = [step(add_terrain_colors)]
