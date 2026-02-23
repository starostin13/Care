#!/bin/bash
if [ ! -f "/app/data/game_database.db" ]; then
    echo "Initializing database from dump..."
    if [ -f "/app/db_deploy/database_dump_20251027_131158.sql" ]; then
        echo "Found database dump, initializing..."
        # Используем sqlite3 напрямую для восстановления
        cd /app
        sqlite3 /app/data/game_database.db < /app/db_deploy/database_dump_20251027_131158.sql
        echo "Database initialized successfully!"
    else
        echo "Dump file not found, starting with empty database"
    fi
else
    echo "Database already exists, skipping initialization"
fi

echo "Starting CareBot application..."
exec python CareBot/run_hybrid.py