"""
Migration 025: Add feature_flags table for toggleable features.

This enables administrators to control which features are active.
The first toggleable feature is common_resource which controls
whether alliance resource mechanics are active.
"""
from yoyo import step


def create_feature_flags_table(conn):
    """Create the feature_flags table and populate with initial flags."""
    cursor = conn.cursor()
    
    # Check if feature_flags table already exists
    cursor.execute("""
        SELECT name FROM sqlite_master 
        WHERE type='table' AND name='feature_flags'
    """)
    table_exists = cursor.fetchone()
    
    if not table_exists:
        # Create feature_flags table
        cursor.execute("""
            CREATE TABLE feature_flags (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                flag_name TEXT NOT NULL UNIQUE,
                enabled INTEGER NOT NULL DEFAULT 1,
                description TEXT,
                updated_at TEXT
            )
        """)
        print("✅ Created feature_flags table")
        
        # Insert initial feature flags
        # common_resource flag controls alliance resource mechanics
        cursor.execute("""
            INSERT INTO feature_flags (flag_name, enabled, description, updated_at)
            VALUES (?, ?, ?, datetime('now'))
        """, ('common_resource', 0, 'Alliance resource mechanics'))
        
        print("✅ Added common_resource feature flag (disabled by default)")
    else:
        print("✅ feature_flags table already exists")
    
    conn.commit()


def add_feature_flags_texts(conn):
    """Add localization texts for feature flags UI."""
    cursor = conn.cursor()
    
    texts_to_add = [
        # Admin menu button
        ('button_admin_feature_flags', 'ru', '⚙️ Управление фичами'),
        ('button_admin_feature_flags', 'en', '⚙️ Feature Flags'),
        
        # Feature flags menu title
        ('admin_feature_flags_title', 'ru', '⚙️ Управление фичами\n\nВключите или выключите функции системы:'),
        ('admin_feature_flags_title', 'en', '⚙️ Feature Flags\n\nToggle system features:'),
        
        # Feature flag names and descriptions
        ('feature_common_resource_name', 'ru', '💎 Общие ресурсы альянсов'),
        ('feature_common_resource_name', 'en', '💎 Alliance Common Resources'),
        ('feature_common_resource_desc', 'ru', 'Механика общих ресурсов альянсов'),
        ('feature_common_resource_desc', 'en', 'Alliance resource mechanics'),
        
        # Status labels
        ('feature_flag_enabled', 'ru', '✅ Включено'),
        ('feature_flag_enabled', 'en', '✅ Enabled'),
        ('feature_flag_disabled', 'ru', '❌ Отключено'),
        ('feature_flag_disabled', 'en', '❌ Disabled'),
        
        # Success messages
        ('feature_flag_toggled', 'ru', 'Фича "{feature_name}" {status}'),
        ('feature_flag_toggled', 'en', 'Feature "{feature_name}" {status}'),
    ]
    
    for key, lang, text in texts_to_add:
        # Check if text already exists
        cursor.execute("""
            SELECT 1 FROM texts WHERE key = ? AND language = ?
        """, (key, lang))
        
        if not cursor.fetchone():
            cursor.execute("""
                INSERT INTO texts (key, language, value)
                VALUES (?, ?, ?)
            """, (key, lang, text))
            print(f"✅ Added text: {key} ({lang})")
        else:
            print(f"⏭️  Text already exists: {key} ({lang})")
    
    conn.commit()


steps = [
    step(create_feature_flags_table),
    step(add_feature_flags_texts)
]
