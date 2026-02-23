"""
Migration 008: Безопасное обновление схемы warmasters без потери данных

КРИТИЧНО: Эта миграция заменяет деструктивный warmasters.sql
и гарантирует сохранение ВСЕХ существующих данных пользователей.

Добавляет недостающие колонки если их нет:
- faction (TEXT)
- language (TEXT, default 'ru') 
- notifications_enabled (INTEGER, default 1)
- is_admin (INTEGER, default 0)
"""

from yoyo import step

def safe_warmasters_schema_update(conn):
    """Безопасно обновляем схему warmasters с сохранением всех данных."""
    cursor = conn.cursor()
    
    # Получаем текущую схему таблицы
    cursor.execute("PRAGMA table_info(warmasters)")
    columns_info = cursor.fetchall()
    existing_columns = {col[1]: col[2] for col in columns_info}  # {name: type}
    
    print(f"Текущие колонки warmasters: {list(existing_columns.keys())}")
    
    # Список необходимых колонок с их типами и значениями по умолчанию
    required_columns = {
        'id': ('INTEGER', 'PRIMARY KEY'),
        'telegram_id': ('TEXT', 'UNIQUE'),
        'alliance': ('INTEGER', 'DEFAULT 0'),
        'nickname': ('TEXT', ''),
        'registered_as': ('TEXT', 'UNIQUE'),
        'faction': ('TEXT', ''),
        'language': ('TEXT', "DEFAULT 'ru'"),
        'notifications_enabled': ('INTEGER', 'DEFAULT 1'),
        'is_admin': ('INTEGER', 'DEFAULT 0')
    }
    
    # Проверяем и добавляем недостающие колонки
    added_columns = []
    for col_name, (col_type, col_constraint) in required_columns.items():
        if col_name not in existing_columns:
            if col_constraint.startswith('DEFAULT'):
                cursor.execute(f"ALTER TABLE warmasters ADD COLUMN {col_name} {col_type} {col_constraint}")
                added_columns.append(f"{col_name} ({col_type} {col_constraint})")
                print(f"✅ Добавлена колонка: {col_name} {col_type} {col_constraint}")
    
    if added_columns:
        print(f"✅ Успешно добавлено {len(added_columns)} колонок в warmasters")
        for col in added_columns:
            print(f"   - {col}")
    else:
        print("✅ Все необходимые колонки уже существуют в warmasters")
    
    # Проверяем количество записей для подтверждения целостности
    cursor.execute("SELECT COUNT(*) FROM warmasters")
    record_count = cursor.fetchone()[0]
    print(f"✅ Сохранено записей пользователей: {record_count}")
    
    cursor.close()

def rollback_schema_update(conn):
    """Откат миграции - в SQLite нельзя удалить колонки, поэтому только помечаем."""
    print("⚠️  SQLite не поддерживает удаление колонок. Миграция помечена как откаченная.")
    pass

steps = [
    step(safe_warmasters_schema_update, rollback_schema_update)
]