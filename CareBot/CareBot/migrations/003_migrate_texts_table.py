# -*- coding: utf-8 -*-
"""
Migration 003: Migrate existing texts table to new localization structure

This migration:
- Renames existing texts table to texts_old
- Creates new texts table with proper localization structure
- Migrates existing data from old structure
"""

from yoyo import step

def migrate_texts_table(conn):
    """Migrate the texts table to new structure."""
    cursor = conn.cursor()
    
    # Rename existing table
    cursor.execute('ALTER TABLE texts RENAME TO texts_old')
    
    # Create new texts table
    cursor.execute('''
        CREATE TABLE texts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            key TEXT NOT NULL,
            language TEXT NOT NULL,
            value TEXT NOT NULL,
            UNIQUE(key, language)
        )
    ''')
    
    # Migrate existing data (rus column to ru language)
    cursor.execute('''
        INSERT INTO texts (key, language, value)
        SELECT name, 'ru', rus FROM texts_old WHERE rus IS NOT NULL
    ''')
    
    # Add basic English translations
    english_texts = [
        ('welcome_message', 'en', 'Welcome to the Crusade Bot! Type /start to begin.'),
        ('main_menu_greeting', 'en', 'Hello, {name}! Choose an action:'),
        ('btn_set_name', 'en', 'Set Name'),
        ('btn_settings', 'en', 'Settings'),
        ('btn_game', 'en', 'Game'),
        ('btn_registration', 'en', 'Registration'),
        ('btn_missions', 'en', 'Missions'),
        ('btn_back', 'en', 'Back'),
        ('settings_menu_title', 'en', 'Settings:'),
        ('btn_change_language', 'en', 'Change Language'),
        ('select_language', 'en', 'Select your language:'),
        ('language_updated', 'en', 'Language updated! Your settings:'),
        ('choose_rules', 'en', 'Choose the rules, {name}'),
        ('error_occurred', 'en', 'An error occurred. Please try again.'),
    ]
    
    for key, language, value in english_texts:
        cursor.execute('''
            INSERT OR REPLACE INTO texts (key, language, value)
            VALUES (?, ?, ?)
        ''', (key, language, value))

def rollback_texts_migration(conn):
    """Rollback the texts table migration."""
    cursor = conn.cursor()
    cursor.execute('DROP TABLE IF EXISTS texts')
    cursor.execute('ALTER TABLE texts_old RENAME TO texts')

steps = [
    step(migrate_texts_table, rollback_texts_migration)
]