#!/bin/bash

# Скрипт автоматического бэкапа базы данных CareBot
# Создает резервные копии с временными метками

set -e

# Конфигурация
CONTAINER_NAME="carebot"
DATABASE_PATH="/app/data/game_database.db"
BACKUP_DIR="/home/ubuntu/carebot/backups"
PROJECT_DIR="/home/ubuntu/carebot"

# Создание директории для бэкапов если не существует
mkdir -p "$BACKUP_DIR"

# Генерация имени файла с временной меткой
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
BACKUP_FILENAME="carebot_backup_${TIMESTAMP}.sql"
BACKUP_PATH="$BACKUP_DIR/$BACKUP_FILENAME"

echo "🔄 Начинаем создание бэкапа базы данных CareBot..."
echo "📅 Время: $(date)"
echo "📁 Путь: $BACKUP_PATH"

# Проверка что контейнер работает
if ! docker container inspect "$CONTAINER_NAME" >/dev/null 2>&1; then
    echo "❌ Контейнер $CONTAINER_NAME не найден!"
    exit 1
fi

if [ "$(docker container inspect -f '{{.State.Status}}' "$CONTAINER_NAME")" != "running" ]; then
    echo "❌ Контейнер $CONTAINER_NAME не запущен!"
    exit 1
fi

# Создание SQL дампа через sqlite3
echo "📦 Создаем SQL дамп..."
if docker exec -t "$CONTAINER_NAME" sqlite3 "$DATABASE_PATH" .dump > "$BACKUP_PATH" 2>/dev/null; then
    echo "✅ SQL дамп создан: $BACKUP_PATH"
    
    # Проверка размера файла
    BACKUP_SIZE=$(stat -f%z "$BACKUP_PATH" 2>/dev/null || stat -c%s "$BACKUP_PATH" 2>/dev/null)
    if [ "$BACKUP_SIZE" -gt 1000 ]; then
        echo "✅ Размер бэкапа: $BACKUP_SIZE байт"
    else
        echo "⚠️  Предупреждение: Размер бэкапа очень мал ($BACKUP_SIZE байт)"
    fi
else
    echo "❌ Ошибка создания SQL дампа!"
    exit 1
fi

# Создание копии бинарного файла базы данных
BINARY_BACKUP_PATH="$BACKUP_DIR/carebot_binary_${TIMESTAMP}.db"
echo "📦 Создаем копию бинарного файла..."
if docker cp "$CONTAINER_NAME:$DATABASE_PATH" "$BINARY_BACKUP_PATH" 2>/dev/null; then
    echo "✅ Бинарная копия создана: $BINARY_BACKUP_PATH"
else
    echo "⚠️  Предупреждение: Не удалось создать бинарную копию"
fi

# Создание ссылки на последний бэкап
ln -sf "$BACKUP_PATH" "$BACKUP_DIR/latest_backup.sql"
if [ -f "$BINARY_BACKUP_PATH" ]; then
    ln -sf "$BINARY_BACKUP_PATH" "$BACKUP_DIR/latest_backup.db"
fi

echo "✅ Ссылка на последний бэкап обновлена"

# Очистка старых бэкапов (хранить последние 30 дней SQL + 7 дней бинарных)
echo "🧹 Очистка старых бэкапов..."

# Удаление SQL бэкапов старше 30 дней
find "$BACKUP_DIR" -name "carebot_backup_*.sql" -type f -mtime +30 -delete 2>/dev/null || true

# Удаление бинарных бэкапов старше 7 дней  
find "$BACKUP_DIR" -name "carebot_binary_*.db" -type f -mtime +7 -delete 2>/dev/null || true

# Подсчет количества бэкапов
SQL_COUNT=$(find "$BACKUP_DIR" -name "carebot_backup_*.sql" -type f | wc -l)
BINARY_COUNT=$(find "$BACKUP_DIR" -name "carebot_binary_*.db" -type f | wc -l)

echo "📊 Статистика бэкапов:"
echo "   SQL файлы: $SQL_COUNT"
echo "   Бинарные файлы: $BINARY_COUNT"

# Запись информации в лог
LOG_FILE="$BACKUP_DIR/backup.log"
echo "$(date): Backup created successfully - $BACKUP_FILENAME (${BACKUP_SIZE} bytes)" >> "$LOG_FILE"

echo "🎉 Бэкап завершен успешно!"
echo "📁 Последний бэкап: $BACKUP_DIR/latest_backup.sql"

# Возврат пути к созданному бэкапу для использования в других скриптах
echo "$BACKUP_PATH"