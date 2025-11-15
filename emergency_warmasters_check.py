#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Скрипт экстренной диагностики базы данных warmasters.
Проверяет текущее состояние данных и схемы таблицы warmasters.
"""

import sqlite3
import os
import sys

def check_warmasters_data(db_path):
    """Проверяем состояние таблицы warmasters."""
    
    if not os.path.exists(db_path):
        print(f"❌ ОШИБКА: База данных не найдена по пути: {db_path}")
        return False
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        print("🔍 ДИАГНОСТИКА ТАБЛИЦЫ WARMASTERS")
        print("=" * 50)
        
        # Проверяем существование таблицы
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='warmasters'")
        if not cursor.fetchone():
            print("❌ КРИТИЧНО: Таблица warmasters НЕ СУЩЕСТВУЕТ!")
            return False
        
        print("✅ Таблица warmasters существует")
        
        # Получаем схему таблицы
        cursor.execute("PRAGMA table_info(warmasters)")
        columns = cursor.fetchall()
        
        print("\n📋 СХЕМА ТАБЛИЦЫ:")
        print("-" * 30)
        for col in columns:
            print(f"  {col[1]:20} | {col[2]:10} | NotNull: {col[3]} | Default: {col[4]}")
        
        # Проверяем количество записей
        cursor.execute("SELECT COUNT(*) FROM warmasters")
        total_records = cursor.fetchone()[0]
        
        print(f"\n📊 КОЛИЧЕСТВО ЗАПИСЕЙ: {total_records}")
        
        if total_records == 0:
            print("❌ КРИТИЧНО: В таблице warmasters НЕТ ПОЛЬЗОВАТЕЛЕЙ!")
            return False
        
        # Показываем примеры записей (без telegram_id для безопасности)
        # Сначала проверяем какие колонки существуют
        cursor.execute("PRAGMA table_info(warmasters)")
        available_columns = [col[1] for col in cursor.fetchall()]
        
        # Формируем запрос только с существующими колонками
        select_fields = ['id', 'alliance', 'nickname', 'registered_as']
        optional_fields = {
            'faction': 'faction',
            'language': 'language', 
            'notifications_enabled': 'notifications_enabled',
            'is_admin': 'is_admin'
        }
        
        for col_name, col_alias in optional_fields.items():
            if col_name in available_columns:
                select_fields.append(f"{col_name} as {col_alias}")
            else:
                select_fields.append(f"'отсутствует' as {col_alias}")
        
        query = f"""
            SELECT {', '.join(select_fields)}
            FROM warmasters 
            ORDER BY id 
            LIMIT 5
        """
        
        cursor.execute(query)
        
        sample_records = cursor.fetchall()
        
        print("\n👥 ПРИМЕРЫ ЗАПИСЕЙ (первые 5):")
        print("-" * 80)
        print(f"{'ID':3} | {'Alliance':8} | {'Nickname':15} | {'RegAs':15} | {'Faction':7} | {'Lang':4} | {'Notif':5} | {'Admin':5}")
        print("-" * 80)
        
        for record in sample_records:
            print(f"{record[0]:3} | {record[1]:8} | {str(record[2])[:15]:15} | {str(record[3])[:15]:15} | {record[4]:7} | {record[5]:4} | {record[6]:5} | {record[7]:5}")
        
        # Проверяем целостность данных
        cursor.execute("SELECT COUNT(*) FROM warmasters WHERE telegram_id IS NULL OR telegram_id = ''")
        null_telegram = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM warmasters WHERE alliance IS NULL")
        null_alliance = cursor.fetchone()[0]
        
        print(f"\n🔍 ПРОВЕРКА ЦЕЛОСТНОСТИ:")
        print(f"  Записей без telegram_id: {null_telegram}")
        print(f"  Записей без alliance: {null_alliance}")
        
        if null_telegram > 0:
            print("⚠️  ВНИМАНИЕ: Есть записи без telegram_id!")
        
        if null_alliance > 0:
            print("⚠️  ВНИМАНИЕ: Есть записи без alliance!")
        
        # Проверяем распределение по альянсам
        cursor.execute("""
            SELECT alliance, COUNT(*) as count 
            FROM warmasters 
            WHERE alliance != 0 
            GROUP BY alliance 
            ORDER BY alliance
        """)
        alliance_distribution = cursor.fetchall()
        
        print(f"\n🏛️  РАСПРЕДЕЛЕНИЕ ПО АЛЬЯНСАМ:")
        for alliance_id, count in alliance_distribution:
            print(f"  Альянс {alliance_id}: {count} участников")
        
        cursor.execute("SELECT COUNT(*) FROM warmasters WHERE alliance = 0")
        unaligned = cursor.fetchone()[0]
        print(f"  Без альянса: {unaligned} участников")
        
        conn.close()
        
        print(f"\n✅ ДИАГНОСТИКА ЗАВЕРШЕНА: {total_records} пользователей в базе данных")
        return True
        
    except sqlite3.Error as e:
        print(f"❌ ОШИБКА SQLite: {e}")
        return False
    except Exception as e:
        print(f"❌ КРИТИЧЕСКАЯ ОШИБКА: {e}")
        return False

def main():
    print("🚨 ЭКСТРЕННАЯ ДИАГНОСТИКА БАЗЫ ДАННЫХ WARMASTERS")
    print("=" * 60)
    
    # Пути к возможным локациям базы данных
    possible_paths = [
        "/app/data/game_database.db",  # В контейнере
        "./data/game_database.db",     # Локально в production
        "../data/game_database.db",    # Относительный путь
        "game_database.db"             # Текущая папка
    ]
    
    db_path = None
    for path in possible_paths:
        if os.path.exists(path):
            db_path = path
            print(f"📍 Найдена база данных: {db_path}")
            break
    
    if db_path is None:
        print("❌ КРИТИЧНО: База данных не найдена ни по одному из путей:")
        for path in possible_paths:
            print(f"   - {path}")
        return False
    
    return check_warmasters_data(db_path)

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)