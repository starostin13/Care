#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Скрипт для удаления записей о миграции 007 из базы данных
"""
import sqlite3

def remove_migration_007():
    """Удаляет записи о миграции 007 из таблиц yoyo"""
    
    db_path = '/app/data/game_database.db'
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Удаляем из _yoyo_migration
        cursor.execute("DELETE FROM _yoyo_migration WHERE migration_id = ?", ('007_redistribute_alliances',))
        deleted_migrations = cursor.rowcount
        
        # Удаляем из _yoyo_log
        cursor.execute("DELETE FROM _yoyo_log WHERE migration_id = ?", ('007_redistribute_alliances',))
        deleted_logs = cursor.rowcount
        
        conn.commit()
        conn.close()
        
        print(f"✅ Удалено записей из _yoyo_migration: {deleted_migrations}")
        print(f"✅ Удалено записей из _yoyo_log: {deleted_logs}")
        print("🎉 Миграция 007 полностью удалена из базы данных")
        
        return True
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        return False

if __name__ == "__main__":
    remove_migration_007()