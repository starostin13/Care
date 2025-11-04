#!/bin/bash

# Скрипт восстановления базы данных CareBot из бэкапа
# Восстанавливает базу из последнего или указанного бэкапа

set -e

# Конфигурация
CONTAINER_NAME="carebot"
DATABASE_PATH="/app/data/game_database.db"
BACKUP_DIR="/home/ubuntu/carebot/backups"
PROJECT_DIR="/home/ubuntu/carebot"

# Параметры
BACKUP_FILE="$1"
FORCE_RESTORE="$2"

function show_usage() {
    echo "Использование: $0 [backup_file] [--force]"
    echo ""
    echo "Параметры:"
    echo "  backup_file  - Путь к файлу бэкапа (по умолчанию: последний бэкап)"
    echo "  --force      - Восстановить без подтверждения"
    echo ""
    echo "Примеры:"
    echo "  $0                                    # Восстановить из последнего бэкапа"
    echo "  $0 --force                           # Восстановить без подтверждения"
    echo "  $0 backup_20241104_120000.sql        # Восстановить из конкретного файла"
    echo ""
}

# Проверка параметров
if [ "$BACKUP_FILE" = "--help" ] || [ "$BACKUP_FILE" = "-h" ]; then
    show_usage
    exit 0
fi

echo "🔄 Восстановление базы данных CareBot..."
echo "📅 Время: $(date)"

# Если файл бэкапа не указан, используем последний
if [ -z "$BACKUP_FILE" ] || [ "$BACKUP_FILE" = "--force" ]; then
    if [ "$BACKUP_FILE" = "--force" ]; then
        FORCE_RESTORE="--force"
    fi
    
    BACKUP_FILE="$BACKUP_DIR/latest_backup.sql"
    
    if [ ! -f "$BACKUP_FILE" ]; then
        echo "❌ Последний бэкап не найден: $BACKUP_FILE"
        echo "📋 Доступные бэкапы:"
        ls -la "$BACKUP_DIR"/*.sql 2>/dev/null || echo "   (Нет доступных бэкапов)"
        exit 1
    fi
    
    echo "📁 Используем последний бэкап: $BACKUP_FILE"
else
    # Проверка существования указанного файла
    if [[ ! "$BACKUP_FILE" = /* ]]; then
        # Относительный путь - добавляем базовую директорию
        BACKUP_FILE="$BACKUP_DIR/$BACKUP_FILE"
    fi
    
    if [ ! -f "$BACKUP_FILE" ]; then
        echo "❌ Файл бэкапа не найден: $BACKUP_FILE"
        exit 1
    fi
    
    echo "📁 Используем указанный бэкап: $BACKUP_FILE"
fi

# Получение информации о бэкапе
BACKUP_SIZE=$(stat -f%z "$BACKUP_FILE" 2>/dev/null || stat -c%s "$BACKUP_FILE" 2>/dev/null)
BACKUP_DATE=$(stat -f%Sm -t "%Y-%m-%d %H:%M:%S" "$BACKUP_FILE" 2>/dev/null || stat -c%y "$BACKUP_FILE" 2>/dev/null)

echo "📊 Информация о бэкапе:"
echo "   📄 Файл: $(basename "$BACKUP_FILE")"
echo "   📏 Размер: $BACKUP_SIZE байт"
echo "   📅 Дата: $BACKUP_DATE"

# Проверка размера бэкапа
if [ "$BACKUP_SIZE" -lt 1000 ]; then
    echo "⚠️  Предупреждение: Размер бэкапа очень мал ($BACKUP_SIZE байт)"
    if [ "$FORCE_RESTORE" != "--force" ]; then
        read -p "Продолжить восстановление? (y/n): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            echo "❌ Восстановление отменено"
            exit 1
        fi
    fi
fi

# Подтверждение восстановления
if [ "$FORCE_RESTORE" != "--force" ]; then
    echo ""
    echo "⚠️  ВНИМАНИЕ: Это действие полностью заменит текущую базу данных!"
    echo "🗑️  Все текущие данные будут утеряны!"
    echo ""
    read -p "Вы уверены, что хотите продолжить? (y/n): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "❌ Восстановление отменено"
        exit 1
    fi
fi

# Проверка что контейнер работает
if ! docker container inspect "$CONTAINER_NAME" >/dev/null 2>&1; then
    echo "❌ Контейнер $CONTAINER_NAME не найден!"
    exit 1
fi

if [ "$(docker container inspect -f '{{.State.Status}}' "$CONTAINER_NAME")" != "running" ]; then
    echo "❌ Контейнер $CONTAINER_NAME не запущен!"
    exit 1
fi

# Создание бэкапа текущей базы перед восстановлением
echo "💾 Создаем бэкап текущей базы данных перед восстановлением..."
CURRENT_BACKUP="$BACKUP_DIR/before_restore_$(date +%Y%m%d_%H%M%S).sql"
if docker exec -t "$CONTAINER_NAME" sqlite3 "$DATABASE_PATH" .dump > "$CURRENT_BACKUP" 2>/dev/null; then
    echo "✅ Текущая база сохранена: $CURRENT_BACKUP"
else
    echo "⚠️  Предупреждение: Не удалось создать бэкап текущей базы"
fi

# Остановка приложения (но не контейнера)
echo "⏸️  Останавливаем CareBot приложение..."
docker exec "$CONTAINER_NAME" pkill -f "python run_hybrid.py" 2>/dev/null || true
sleep 2

# Очистка текущей базы данных
echo "🗑️  Очищаем текущую базу данных..."
docker exec -t "$CONTAINER_NAME" sqlite3 "$DATABASE_PATH" "PRAGMA foreign_keys = OFF; DROP TABLE IF EXISTS warmasters; DROP TABLE IF EXISTS battles; DROP TABLE IF EXISTS alliances; DROP TABLE IF EXISTS map; DROP TABLE IF EXISTS edges; DROP TABLE IF EXISTS mission_stack; DROP TABLE IF EXISTS schedule; DROP TABLE IF EXISTS texts; DROP TABLE IF EXISTS battle_attenders; DROP TABLE IF EXISTS map_story;" 2>/dev/null || true

# Восстановление из бэкапа
echo "📥 Восстанавливаем базу данных из бэкапа..."
if docker exec -i "$CONTAINER_NAME" sqlite3 "$DATABASE_PATH" < "$BACKUP_FILE"; then
    echo "✅ База данных восстановлена успешно"
else
    echo "❌ Ошибка восстановления базы данных!"
    
    # Попытка восстановить из бэкапа текущей базы
    if [ -f "$CURRENT_BACKUP" ]; then
        echo "🔄 Пытаемся восстановить предыдущее состояние..."
        docker exec -i "$CONTAINER_NAME" sqlite3 "$DATABASE_PATH" < "$CURRENT_BACKUP" 2>/dev/null || true
    fi
    
    exit 1
fi

# Проверка целостности восстановленной базы
echo "🔍 Проверяем целостность восстановленной базы..."
TABLES_COUNT=$(docker exec -t "$CONTAINER_NAME" sqlite3 "$DATABASE_PATH" "SELECT COUNT(*) FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' AND name NOT LIKE '_yoyo_%' AND name != 'yoyo_lock';" 2>/dev/null | tr -d '\r\n' || echo "0")

if [ "$TABLES_COUNT" -gt 5 ]; then
    echo "✅ База данных содержит $TABLES_COUNT таблиц - восстановление успешно"
else
    echo "⚠️  Предупреждение: База данных содержит только $TABLES_COUNT таблиц"
fi

# Перезапуск контейнера для корректного запуска приложения
echo "🔄 Перезапускаем контейнер CareBot..."
cd "$PROJECT_DIR"
docker-compose restart carebot

echo "⏳ Ожидаем запуска приложения..."
sleep 10

# Проверка что приложение запустилось
if curl -f http://localhost:5555/health >/dev/null 2>&1; then
    echo "✅ CareBot запущен и работает корректно"
else
    echo "⚠️  Предупреждение: CareBot может не работать корректно"
fi

echo ""
echo "🎉 Восстановление базы данных завершено!"
echo "📁 Использованный бэкап: $(basename "$BACKUP_FILE")"
echo "💾 Предыдущая база сохранена: $(basename "$CURRENT_BACKUP")"
echo "🔍 Проверьте работоспособность через SQLite Web: http://localhost:8080"