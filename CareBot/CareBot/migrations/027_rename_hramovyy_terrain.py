"""
Migration 027: Rename terrain typo 'Храовый квартал' -> 'Храмовый квартал'.
Applies to both map.state and terrain_colors.name in a safe, idempotent way.
"""
from yoyo import step


def rename_terrain_typo(conn):
    cursor = conn.cursor()

    # 1) Ensure canonical row exists in terrain_colors.
    cursor.execute(
        """
        INSERT OR IGNORE INTO terrain_colors (name, color)
        SELECT 'Храмовый квартал', color
        FROM terrain_colors
        WHERE name = 'Храовый квартал'
        """
    )

    # 2) If canonical row still doesn't exist, create with default color.
    cursor.execute(
        """
        INSERT OR IGNORE INTO terrain_colors (name, color)
        VALUES ('Храмовый квартал', '#FBC02D')
        """
    )

    # 3) Rename in map state values.
    cursor.execute(
        """
        UPDATE map
        SET state = 'Храмовый квартал'
        WHERE state = 'Храовый квартал'
        """
    )

    # 4) Keep legacy row untouched (non-destructive policy).

    print("✅ Migration 027: terrain typo renamed to 'Храмовый квартал'")


steps = [step(rename_terrain_typo)]
