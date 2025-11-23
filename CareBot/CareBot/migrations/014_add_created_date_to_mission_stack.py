"""
Migration 014: Add created_date column to mission_stack table
This allows tracking when missions were created and unlocking old ones.
"""
from yoyo import step

def add_created_date_column(conn):
    cursor = conn.cursor()
    
    # Проверяем существование колонки created_date
    cursor.execute("PRAGMA table_info(mission_stack)")
    columns = [col[1] for col in cursor.fetchall()]
    
    if 'created_date' not in columns:
        # Добавляем колонку с текущей датой по умолчанию
        cursor.execute("ALTER TABLE mission_stack ADD COLUMN created_date TEXT DEFAULT NULL")
        print("✅ Добавлена колонка created_date в таблицу mission_stack")
    else:
        print("✅ Колонка created_date уже существует в mission_stack")

steps = [step(add_created_date_column)]
