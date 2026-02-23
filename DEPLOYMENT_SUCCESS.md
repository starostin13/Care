# Успешное развертывание CareBot - Пошаговая инструкция

**Дата создания:** 4 ноября 2025
**Статус:** Протестировано и работает
**Цель:** Документация рабочего процесса развертывания для предотвращения экспериментов

## Проблемы которые были решены

### Исходная ситуация
1. ❌ Множество Docker файлов создавали путаницу (10+ вариантов)
2. ❌ CareBot контейнер не запускался из-за проблем с entrypoint.sh
3. ❌ Дублированные контакты в SQL запросах
4. ❌ Отсутствие удобного доступа к SQLite базе с Windows машины

### Что работает сейчас
1. ✅ CareBot: http://192.168.0.125:5555 (статус healthy)
2. ✅ SQLite Web: http://192.168.0.125:8080 (статус 200 OK)
3. ✅ Чистая Docker структура (2 файла вместо 10+)
4. ✅ Исправленные SQL запросы без дубликатов

## Рабочая Docker структура

### Финальные файлы (НЕ ИЗМЕНЯТЬ!)

#### Dockerfile.carebot
```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Установка системных пакетов
RUN apt-get update && apt-get install -y \
    sqlite3 \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Установка Python зависимостей
COPY CareBot/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копирование кода приложения
COPY CareBot/ .

# Создание директории для данных
RUN mkdir -p /app/data && chmod 755 /app/data

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:5555/health || exit 1

# Запуск приложения НАПРЯМУЮ
CMD ["python", "run_hybrid.py"]
```

#### Dockerfile.sqlite-web
```dockerfile
FROM python:3.11-slim
WORKDIR /app
RUN pip install --no-cache-dir flask
COPY sqlite_web_interface.py .
CMD ["python", "sqlite_web_interface.py"]
```

#### docker-compose.yml (переименованный из docker-compose.simple.yml)
```yaml
version: '3.8'

services:
  carebot:
    build:
      context: .
      dockerfile: Dockerfile.carebot
    container_name: carebot
    ports:
      - "5555:5555"
    volumes:
      - data:/app/data
    networks:
      - carebot_network
    environment:
      - DATABASE_PATH=/app/data/carebot.db
      - SERVER_HOST=0.0.0.0
      - SERVER_PORT=5555
    restart: unless-stopped

  sqlite-web:
    build:
      context: .
      dockerfile: Dockerfile.sqlite-web
    container_name: carebot_sqlite_web
    ports:
      - "8080:8080"
    volumes:
      - data:/app/data
    networks:
      - carebot_network
    restart: unless-stopped

volumes:
  data:

networks:
  carebot_network:
    driver: bridge
```

## Пошаговый процесс развертывания

### 1. Подготовка файлов (выполнять с локальной машины)

```powershell
# Копирование основного кода
scp -r CareBot ubuntu@192.168.0.125:/home/ubuntu/carebot/

# Копирование Docker файлов
scp Dockerfile.carebot ubuntu@192.168.0.125:/home/ubuntu/carebot/
scp Dockerfile.sqlite-web ubuntu@192.168.0.125:/home/ubuntu/carebot/
scp sqlite_web_interface.py ubuntu@192.168.0.125:/home/ubuntu/carebot/

# Копирование docker-compose (как simple, потом переименуем)
scp docker-compose.simple.yml ubuntu@192.168.0.125:/home/ubuntu/carebot/
```

### 2. Подготовка на сервере

```bash
# Подключение к серверу
ssh ubuntu@192.168.0.125

# Переход в рабочую директорию
cd /home/ubuntu/carebot

# Переименование docker-compose файла
mv docker-compose.simple.yml docker-compose.yml

# Остановка старых контейнеров (если есть)
docker-compose down
```

### 3. Сборка и запуск

```bash
# Сборка образов (БЕЗ кэша для чистой сборки)
docker-compose build --no-cache

# Запуск в фоновом режиме
docker-compose up -d

# Проверка статуса
docker-compose ps
```

### 4. Верификация развертывания

```bash
# Проверка логов CareBot
docker-compose logs carebot

# Проверка логов SQLite Web
docker-compose logs sqlite-web

# Проверка health endpoint
curl http://localhost:5555/health

# Должен вернуть:
# {"database":"available","status":"healthy","timestamp":"...","version":"1.0.0"}
```

### 5. Проверка с внешней машины

```powershell
# Health check CareBot
Invoke-WebRequest -Uri "http://192.168.0.125:5555/health" -UseBasicParsing

# Доступность SQLite Web
Invoke-WebRequest -Uri "http://192.168.0.125:8080" -UseBasicParsing
```

## Управление после развертывания

### Полезные команды для мониторинга

```bash
# Статус контейнеров
docker-compose ps

# Логи в реальном времени
docker-compose logs -f carebot

# Рестарт сервисов
docker-compose restart

# Остановка
docker-compose down

# Полная пересборка при изменениях
docker-compose down
docker-compose build --no-cache
docker-compose up -d
```

### Доступ к базе данных

1. **Веб-интерфейс:** http://192.168.0.125:8080
2. **Прямой доступ к контейнеру:**
   ```bash
   docker-compose exec carebot sqlite3 /app/data/carebot.db
   ```

## Важные исправления в коде

### SQL запрос для получения противников (sqllite_helper.py)

**ИСПРАВЛЕНО:** Изменен JOIN в функции `get_warmasters_opponents`:

```python
# БЫЛО (неправильно - дублировало контакты):
JOIN warmasters w2 ON w1.battle_id = w2.battle_id

# СТАЛО (правильно - уникальные противники):
JOIN warmasters w2 ON w1.battle_id = w2.battle_id AND w1.telegram_id != w2.telegram_id
```

Это исправление устранило проблему дублированных контактов при записи на игры.

## Файлы которые НЕ нужны (удалены для упрощения)

- ❌ `Dockerfile` (базовый, заменен на Dockerfile.carebot)
- ❌ `Dockerfile.production` 
- ❌ `Dockerfile-fixed`
- ❌ `Dockerfile-final`
- ❌ `docker-compose.yml` (старый запутанный)
- ❌ `docker-compose.production.yml`
- ❌ `docker-compose.sqlite-web.yml`
- ❌ `entrypoint.sh` (источник проблем, заменен на прямой CMD)

## Почему эта конфигурация работает

1. **Простота:** Только 2 Dockerfile'а вместо 10+
2. **Прямой запуск:** `CMD ["python", "run_hybrid.py"]` без промежуточных скриптов
3. **Здоровые проверки:** Health check для мониторинга
4. **Общий volume:** Оба сервиса используют один том для данных
5. **Правильная сеть:** Bridge network для межсервисного взаимодействия

## Troubleshooting

### Если контейнеры не запускаются

```bash
# Проверить логи
docker-compose logs

# Пересобрать без кэша
docker-compose build --no-cache

# Проверить порты
netstat -tulpn | grep :5555
netstat -tulpn | grep :8080
```

### Если база недоступна

```bash
# Проверить volume
docker volume ls
docker volume inspect carebot_data

# Проверить права доступа к файлам
docker-compose exec carebot ls -la /app/data/
```

## КРИТИЧЕСКИ ВАЖНО

1. **НЕ изменяйте структуру Docker файлов** - она работает как есть
2. **НЕ добавляйте entrypoint.sh** - он был источником проблем
3. **НЕ создавайте новые docker-compose файлы** - используйте существующий
4. **ВСЕГДА используйте --no-cache** при пересборке после изменений кода
5. **Проверяйте health endpoint** после каждого развертывания

## 🛡️ СИСТЕМА БЭКАПОВ

### ✅ Создание бэкапа (РАБОЧИЙ СПОСОБ)

**С Windows машины через SSH:**
```powershell
# ПРОВЕРЕНО РАБОТАЕТ! (Протестировано 5 ноября 2025)
ssh ubuntu@192.168.0.125 "cd /home/ubuntu/carebot && ./scripts/backup-database.sh"
```

**На сервере Ubuntu напрямую:**
```bash
cd /home/ubuntu/carebot
./scripts/backup-database.sh
```

### ✅ Проверка бэкапов

```powershell
# Список всех бэкапов
ssh ubuntu@192.168.0.125 "ls -la /home/ubuntu/carebot/backups/"

# Размеры бэкапов
ssh ubuntu@192.168.0.125 "du -h /home/ubuntu/carebot/backups/*"

# Последний бэкап
ssh ubuntu@192.168.0.125 "ls -la /home/ubuntu/carebot/backups/latest_backup.*"
```

### ✅ Восстановление из бэкапа

```bash
# На сервере Ubuntu
cd /home/ubuntu/carebot
./scripts/restore-database.sh              # Из последнего бэкапа
./scripts/restore-database.sh backup.sql   # Из конкретного файла
```

### 📊 Статистика бэкапов

- **Автоматические:** Ежедневно в 03:30 UTC
- **Хранение:** SQL дампы 30 дней, бинарные 7 дней
- **Расположение:** `/home/ubuntu/carebot/backups/`
- **Логи:** `/tmp/carebot_backup.log`

## Контакты и доступность

- **CareBot API:** http://192.168.0.125:5555
- **Health Check:** http://192.168.0.125:5555/health  
- **SQLite Web UI:** http://192.168.0.125:8080
- **SSH доступ:** `ssh ubuntu@192.168.0.125`
- **Рабочая директория:** `/home/ubuntu/carebot/`

---

**Последнее обновление:** 5 ноября 2025  
**Протестировано:** ✅ Работает  
**Статус:** Продакшен готово