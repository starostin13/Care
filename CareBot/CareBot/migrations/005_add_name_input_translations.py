"""
Migration 005: Add missing translations for name input workflow

This migration adds translations for the improved name setting workflow.
"""

from yoyo import step

def add_name_input_translations(conn):
    """Add translations for name input workflow."""
    cursor = conn.cursor()
    
    translations = [
        # Name input workflow
        ('enter_name_prompt', 'ru', 'Введите ваше имя (без пробелов, до 50 символов):'),
        ('enter_name_prompt', 'en', 'Enter your name (no spaces, up to 50 characters):'),
        ('invalid_name_error', 'ru', 'Некорректное имя. Попробуйте еще раз (без пробелов, до 50 символов):'),
        ('invalid_name_error', 'en', 'Invalid name. Try again (no spaces, up to 50 characters):'),
        ('name_set_success', 'ru', 'Отлично! Ваше имя установлено: {name}'),
        ('name_set_success', 'en', 'Great! Your name is set: {name}'),
    ]
    
    for key, language, value in translations:
        cursor.execute("""
            INSERT OR IGNORE INTO texts (key, language, value) 
            VALUES (?, ?, ?)
        """, (key, language, value))
    
    print(f"Added {len(translations)} name input translations")

def remove_name_input_translations(conn):
    """Remove name input translations (rollback)."""
    cursor = conn.cursor()
    
    keys_to_remove = [
        'enter_name_prompt', 'invalid_name_error', 'name_set_success'
    ]
    
    for key in keys_to_remove:
        cursor.execute("DELETE FROM texts WHERE key = ?", (key,))

steps = [
    step(add_name_input_translations, remove_name_input_translations)
]