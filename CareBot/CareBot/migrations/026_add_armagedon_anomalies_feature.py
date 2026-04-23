"""
Migration 026: Add Armagedon Anomalies feature flag and localization.

This migration adds the armagedon_anomalies feature flag which controls
warp-based mission modifiers during the Armagedon crusade.
"""
from yoyo import step


def add_armagedon_anomalies_flag(conn):
    """Add armagedon_anomalies feature flag."""
    cursor = conn.cursor()

    # Check if feature_flags table exists
    cursor.execute("""
        SELECT name FROM sqlite_master
        WHERE type='table' AND name='feature_flags'
    """)
    table_exists = cursor.fetchone()

    if not table_exists:
        print("⚠️  feature_flags table does not exist - skipping")
        return

    # Check if flag already exists
    cursor.execute("""
        SELECT flag_name FROM feature_flags WHERE flag_name = 'armagedon_anomalies'
    """)
    flag_exists = cursor.fetchone()

    if not flag_exists:
        cursor.execute("""
            INSERT INTO feature_flags (flag_name, enabled, description, updated_at)
            VALUES (?, ?, ?, datetime('now'))
        """, ('armagedon_anomalies', 1, 'Warp-based anomalies and hellscapes for Armagedon crusade'))
        print("✅ Added armagedon_anomalies feature flag (enabled by default)")
    else:
        print("✅ armagedon_anomalies feature flag already exists")

    conn.commit()


def add_armagedon_anomalies_texts(conn):
    """Add localization texts for armagedon_anomalies feature."""
    cursor = conn.cursor()

    texts_to_add = [
        # Feature flag names and descriptions
        ('feature_armagedon_anomalies_name', 'ru', '🌀 Аномалии Армагеддона'),
        ('feature_armagedon_anomalies_name', 'en', '🌀 Armagedon Anomalies'),
        ('feature_armagedon_anomalies_desc', 'ru', 'Аномалии и хеллскейпы на варп-территориях'),
        ('feature_armagedon_anomalies_desc', 'en', 'Warp-based anomalies and hellscapes'),
    ]

    for key, lang, text in texts_to_add:
        # Check if text already exists
        cursor.execute("""
            SELECT 1 FROM texts WHERE key = ? AND language = ?
        """, (key, lang))

        if not cursor.fetchone():
            cursor.execute("""
                INSERT INTO texts (key, language, text)
                VALUES (?, ?, ?)
            """, (key, lang, text))
            print(f"✅ Added text: {key} ({lang})")
        else:
            print(f"⏭️  Text already exists: {key} ({lang})")

    conn.commit()


steps = [
    step(add_armagedon_anomalies_flag),
    step(add_armagedon_anomalies_texts)
]
