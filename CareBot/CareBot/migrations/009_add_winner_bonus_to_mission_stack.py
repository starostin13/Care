"""
Migration 009: Add winner_bonus column to mission_stack table
"""
from yoyo import step

def add_winner_bonus_column(conn):
    cursor = conn.cursor()
    
    # Проверяем существование колонки winner_bonus
    cursor.execute("PRAGMA table_info(mission_stack)")
    columns = [col[1] for col in cursor.fetchall()]
    
    if 'winner_bonus' not in columns:
        cursor.execute("ALTER TABLE mission_stack ADD COLUMN winner_bonus TEXT DEFAULT NULL")
        print("✅ Добавлена колонка winner_bonus в таблицу mission_stack")
    else:
        print("✅ Колонка winner_bonus уже существует в mission_stack")

steps = [step(add_winner_bonus_column)]