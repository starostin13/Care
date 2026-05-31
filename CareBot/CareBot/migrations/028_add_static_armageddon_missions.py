"""
Migration 028: add static Armageddon missions table.

Stores imported mission texts and asset paths (relative to assets/deploys).
"""
from yoyo import step


def add_static_armageddon_missions_table(conn):
    cursor = conn.cursor()

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS static_armageddon_missions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            rules TEXT NOT NULL,
            source TEXT NOT NULL,
            source_url TEXT,
            mission_code TEXT NOT NULL,
            mission_name TEXT NOT NULL,
            mission_text_full TEXT NOT NULL,
            deploy_asset_path TEXT,
            map_asset_path TEXT,
            is_active INTEGER NOT NULL DEFAULT 1,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(rules, source, mission_code)
        )
        """
    )

    cursor.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_static_armageddon_rules_active
        ON static_armageddon_missions(rules, is_active)
        """
    )

    cursor.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_static_armageddon_source_code
        ON static_armageddon_missions(source, mission_code)
        """
    )

    print("✅ static_armageddon_missions table is ready")


steps = [step(add_static_armageddon_missions_table)]
