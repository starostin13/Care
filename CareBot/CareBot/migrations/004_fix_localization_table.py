"""
Migration 004: Fix localization table structure and add essential translations

This migration:
1. Recreates texts table with proper structure (key, language, value)
2. Migrates existing data from old structure (name, rus)
3. Adds all essential translations for the interface
"""

from yoyo import step

def fix_texts_table_structure(conn):
    """Recreate texts table with proper structure."""
    cursor = conn.cursor()
    
    # Check if the table has the old structure
    cursor.execute("PRAGMA table_info(texts)")
    columns = [col[1] for col in cursor.fetchall()]
    
    if 'key' not in columns:
        print("Fixing texts table structure...")
        
        # Create new table with correct structure
        cursor.execute("""
            CREATE TABLE texts_new (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                key TEXT NOT NULL,
                language TEXT NOT NULL DEFAULT 'ru',
                value TEXT NOT NULL,
                UNIQUE(key, language)
            )
        """)
        
        # Copy existing data if old table has data
        if 'name' in columns and 'rus' in columns:
            cursor.execute("""
                INSERT OR IGNORE INTO texts_new (key, language, value)
                SELECT name, 'ru', rus FROM texts 
                WHERE name IS NOT NULL AND rus IS NOT NULL
            """)
        
        # Drop old table and rename new one
        cursor.execute("DROP TABLE texts")
        cursor.execute("ALTER TABLE texts_new RENAME TO texts")
        print("Texts table structure fixed!")

def add_essential_translations(conn):
    """Add essential translations for the interface."""
    cursor = conn.cursor()
    
    translations = [
        # Button texts
        ('button_settings', 'ru', 'Настройки'),
        ('button_settings', 'en', 'Settings'),
        ('button_missions', 'ru', 'Миссии'),
        ('button_missions', 'en', 'Missions'),
        ('button_games', 'ru', 'Игры'),
        ('button_games', 'en', 'Games'),
        ('button_set_name', 'ru', 'Установить имя'),
        ('button_set_name', 'en', 'Set Name'),
        ('button_registration', 'ru', 'Регистрация'),
        ('button_registration', 'en', 'Registration'),
        ('button_back', 'ru', 'Назад'),
        ('button_back', 'en', 'Back'),
        ('button_language', 'ru', 'Язык'),
        ('button_language', 'en', 'Language'),
        ('button_notifications', 'ru', 'Уведомления'),
        ('button_notifications', 'en', 'Notifications'),

        # Menu titles
        ('settings_title', 'ru', 'Настройки'),
        ('settings_title', 'en', 'Settings'),
        ('appointments_title', 'ru', 'Назначения'),
        ('appointments_title', 'en', 'Appointments'),
        ('select_language', 'ru', 'Выберите язык:'),
        ('select_language', 'en', 'Select language:'),

        # Status messages  
        ('language_updated', 'ru', 'Язык обновлен!'),
        ('language_updated', 'en', 'Language updated!'),
        ('notifications_enabled', 'ru', 'включены'),
        ('notifications_enabled', 'en', 'enabled'),
        ('notifications_disabled', 'ru', 'отключены'),
        ('notifications_disabled', 'en', 'disabled'),

        # Main menu messages
        ('main_menu_greeting', 'ru', 'Привет, {name}! Добро пожаловать в CareBot!'),
        ('main_menu_greeting', 'en', 'Hello, {name}! Welcome to CareBot!'),
        ('main_menu_nickname_required', 'ru', 'Привет, {name}! Сначала установите имя пользователя.'),
        ('main_menu_nickname_required', 'en', 'Hello, {name}! Please set your username first.')
    ]
    
    for key, language, value in translations:
        cursor.execute("""
            INSERT OR IGNORE INTO texts (key, language, value) 
            VALUES (?, ?, ?)
        """, (key, language, value))
    
    print(f"Added {len(translations)} translations")

def rollback_texts_table(conn):
    """Rollback to old texts table structure (if possible)."""
    # This is complex to rollback properly, so we'll leave it
    # In practice, rollbacks for structural changes are rarely needed
    pass

def remove_translations(conn):
    """Remove added translations (rollback)."""
    cursor = conn.cursor()
    
    # Remove translations added by this migration
    keys_to_remove = [
        'button_settings', 'button_missions', 'button_games', 'button_set_name',
        'button_registration', 'button_back', 'button_language', 'button_notifications',
        'settings_title', 'appointments_title', 'select_language', 'language_updated',
        'notifications_enabled', 'notifications_disabled', 'main_menu_greeting',
        'main_menu_nickname_required'
    ]
    
    for key in keys_to_remove:
        cursor.execute("DELETE FROM texts WHERE key = ?", (key,))

steps = [
    step(fix_texts_table_structure, rollback_texts_table),
    step(add_essential_translations, remove_translations)
]