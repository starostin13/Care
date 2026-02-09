"""
Migration 021: Add map_description column to mission_stack table
This allows storing generated map descriptions for battlefleet missions.
"""
from yoyo import step

def add_map_description_column(conn):
    cursor = conn.cursor()
    
    # Проверяем существование колонки map_description
    cursor.execute("PRAGMA table_info(mission_stack)")
    columns = [col[1] for col in cursor.fetchall()]
    
    if 'map_description' not in columns:
        cursor.execute("ALTER TABLE mission_stack ADD COLUMN map_description TEXT DEFAULT NULL")
        print("✅ Добавлена колонка map_description в таблицу mission_stack")
    else:
        print("✅ Колонка map_description уже существует в mission_stack")

steps = [step(add_map_description_column)]
