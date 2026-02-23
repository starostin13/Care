# 🚀 CareBot - Шпаргалка команд (РАБОЧИЕ СПОСОБЫ)

**Обновлено:** 5 ноября 2025  
**Все команды протестированы и работают!**

## 📋 Основные операции

### 🛡️ Бэкап базы данных
```powershell
# РАБОЧИЙ способ создания бэкапа
ssh ubuntu@192.168.0.125 "cd /home/ubuntu/carebot && ./scripts/backup-database.sh"
```

### 📊 Проверка статуса
```powershell
# Статус контейнеров
ssh ubuntu@192.168.0.125 "cd /home/ubuntu/carebot && docker-compose ps"

# Health check приложения
Invoke-WebRequest -Uri "http://192.168.0.125:5555/health" -UseBasicParsing
```

### 📖 Просмотр логов
```powershell
# Логи CareBot
ssh ubuntu@192.168.0.125 "cd /home/ubuntu/carebot && docker-compose logs carebot"

# Логи в реальном времени
ssh ubuntu@192.168.0.125 "cd /home/ubuntu/carebot && docker-compose logs -f carebot"
```

### 🔄 Управление сервисами
```powershell
# Перезапуск сервисов
ssh ubuntu@192.168.0.125 "cd /home/ubuntu/carebot && docker-compose restart"

# Остановка сервисов
ssh ubuntu@192.168.0.125 "cd /home/ubuntu/carebot && docker-compose down"

# Запуск сервисов
ssh ubuntu@192.168.0.125 "cd /home/ubuntu/carebot && docker-compose up -d"
```

### 💾 Работа с бэкапами
```powershell
# Список всех бэкапов
ssh ubuntu@192.168.0.125 "ls -la /home/ubuntu/carebot/backups/"

# Размеры бэкапов
ssh ubuntu@192.168.0.125 "du -h /home/ubuntu/carebot/backups/*"

# Восстановление из последнего бэкапа
ssh ubuntu@192.168.0.125 "cd /home/ubuntu/carebot && ./scripts/restore-database.sh"
```

### 🗄️ Работа с базой данных
```powershell
# Просмотр таблиц в базе
ssh ubuntu@192.168.0.125 "cd /home/ubuntu/carebot && docker-compose exec -T carebot sqlite3 /app/data/game_database.db '.tables'"

# Количество записей в таблице
ssh ubuntu@192.168.0.125 "cd /home/ubuntu/carebot && docker-compose exec -T carebot sqlite3 /app/data/game_database.db 'SELECT COUNT(*) FROM warmasters;'"
```

## 🌐 Доступные сервисы

- **CareBot API:** http://192.168.0.125:5555
- **Health Check:** http://192.168.0.125:5555/health
- **SQLite Web UI:** http://192.168.0.125:8080

## 🚨 В случае проблем

1. **Сначала создайте бэкап!**
2. Проверьте статус контейнеров
3. Посмотрите логи приложения
4. При необходимости восстановите из бэкапа

## 📚 Полная документация

- **Развертывание:** `DEPLOYMENT_SUCCESS.md`
- **Для AI агентов:** `AI_AGENTS_READ_THIS.md`
- **Главная:** `README.md`

---

*Все команды протестированы 5 ноября 2025 и работают корректно.*