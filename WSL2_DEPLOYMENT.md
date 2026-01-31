# WSL2 + Docker Deployment Guide

## 🎯 Обзор новой архитектуры

С использованием WSL2 + Docker на локальной машине, процесс деплоя упрощается и становится более прозрачным:

```
Windows Machine (PowerShell)
    ↓
WSL2 (Ubuntu)
    ↓ Build Docker Image
Docker Image (локально)
    ↓ Save & Transfer
Production Server (ubuntu@192.168.1.125)
    ↓ Load & Run
Docker Container (production)
```

### Преимущества WSL2 подхода

✅ **Прозрачность образа**: Точно видно какие файлы попали в образ  
✅ **Быстрая сборка**: Локальный кеш слоев Docker  
✅ **Независимость**: Не требуется Docker на production для сборки  
✅ **Тестирование**: Можно запустить тот же образ локально перед деплоем  
✅ **Контроль версий**: Легко управлять тегами и версиями образов  
✅ **Безопасность**: Production safety check перед сборкой образа

## 🔧 Настройка WSL2

### 1. Установка WSL2

```powershell
# В PowerShell (администратор)
wsl --install
wsl --set-default-version 2

# Установите Ubuntu (рекомендуется 22.04)
wsl --install -d Ubuntu-22.04
```

### 2. Настройка Docker в WSL2

```bash
# В WSL2 терминале
sudo apt update
sudo apt install -y docker.io docker-compose

# Добавьте пользователя в группу docker
sudo usermod -aG docker $USER

# Запустите Docker service
sudo service docker start

# Проверьте установку
docker --version
docker compose version
```

### 3. Настройка auto-start Docker в WSL2

Создайте файл для автозапуска:

```bash
# Создайте /etc/wsl.conf
sudo nano /etc/wsl.conf

# Добавьте содержимое:
[boot]
command = "service docker start"
```

Перезапустите WSL:

```powershell
wsl --shutdown
```

## 🚀 Новый процесс деплоя

### Шаг 1: Сборка образа в WSL2

```powershell
# Из директории проекта в PowerShell
.\scripts\wsl2-deploy.ps1 build

# Или вручную в WSL2:
wsl -e bash -c "cd /mnt/c/Users/staro/Projects/Care && docker build -t carebot:latest -f Dockerfile.production ."
```

### Шаг 2: Тестирование образа локально (опционально)

```powershell
.\scripts\wsl2-deploy.ps1 test

# Проверьте http://localhost:5556/health
```

### Шаг 3: Деплой на production

```powershell
.\scripts\wsl2-deploy.ps1 deploy

# Или полный цикл (build + test + deploy):
.\scripts\wsl2-deploy.ps1 full
```

## 📋 Команды wsl2-deploy.ps1

### Основные команды

```powershell
# Сборка образа
.\scripts\wsl2-deploy.ps1 build

# Тестирование образа локально
.\scripts\wsl2-deploy.ps1 test

# Деплой на production
.\scripts\wsl2-deploy.ps1 deploy

# Полный цикл (build → test → deploy)
.\scripts\wsl2-deploy.ps1 full

# Проверка что попало в образ
.\scripts\wsl2-deploy.ps1 inspect

# Список образов
.\scripts\wsl2-deploy.ps1 images

# Очистка старых образов
.\scripts\wsl2-deploy.ps1 cleanup
```

### Управление production

```powershell
# Статус
.\scripts\wsl2-deploy.ps1 status

# Логи
.\scripts\wsl2-deploy.ps1 logs

# Перезапуск
.\scripts\wsl2-deploy.ps1 restart

# Бэкап
.\scripts\wsl2-deploy.ps1 backup
```

### Работа с миграциями

```powershell
# Синхронизация миграций
.\scripts\wsl2-deploy.ps1 migrations

# Применение миграций
.\scripts\wsl2-deploy.ps1 apply-migrations

# Статус миграций
.\scripts\wsl2-deploy.ps1 migration-status
```

## 🔍 Инспекция образа

### Просмотр содержимого образа

```powershell
.\scripts\wsl2-deploy.ps1 inspect
```

Эта команда покажет:
- Список всех файлов в образе
- Размер каждого слоя
- Переменные окружения
- Exposed порты
- Команду запуска

### Проверка конкретных файлов

```bash
# В WSL2
docker run --rm carebot:latest ls -la /app/CareBot/

# Проверить наличие конкретного файла
docker run --rm carebot:latest cat /app/CareBot/mission_helper.py | head -20
```

## 🎯 Workflow для разработки

### Локальная разработка

1. **Редактируйте код в VS Code** (Windows)
2. **Тестируйте локально** с test-mode:
   ```powershell
   .\scripts\test-mode.ps1 start
   ```

### Деплой на production

3. **Production safety check**:
   ```powershell
   python scripts\check-production-safety.py
   ```

4. **Соберите образ в WSL2**:
   ```powershell
   .\scripts\wsl2-deploy.ps1 build
   ```

5. **Проверьте образ**:
   ```powershell
   .\scripts\wsl2-deploy.ps1 inspect
   ```

6. **Протестируйте локально** (опционально):
   ```powershell
   .\scripts\wsl2-deploy.ps1 test
   # Проверьте http://localhost:5556/health
   ```

7. **Задеплойте на production**:
   ```powershell
   .\scripts\wsl2-deploy.ps1 deploy
   ```

8. **Проверьте production**:
   ```powershell
   .\scripts\wsl2-deploy.ps1 status
   # Проверьте http://192.168.1.125:5555/health
   ```

## 🏗️ Архитектура образа

### Структура Dockerfile.production

```dockerfile
FROM python:3.11-slim

# Системные зависимости
RUN apt-get update && apt-get install -y sqlite3

# Python зависимости (отдельный слой для кеша)
COPY CareBot/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Код приложения
COPY CareBot/run_hybrid.py .
COPY CareBot/CareBot/ ./CareBot/

# Данные и миграции (через volumes)
# - /app/data - база данных
# - /app/CareBot/migrations - миграции

# Запуск
CMD ["python", "run_hybrid.py"]
```

### Что НЕ попадает в образ

- ❌ `mock_sqlite_helper.py` (тестовые файлы)
- ❌ `test_*.py` (тесты)
- ❌ `.git/` (репозиторий)
- ❌ `scripts/` (deployment скрипты)
- ❌ База данных (монтируется через volume)
- ❌ Миграции (монтируются через volume для гибкости)

### Что попадает в образ

- ✅ Python runtime
- ✅ Все зависимости из requirements.txt
- ✅ Production код (handlers, helpers)
- ✅ Config файлы
- ✅ Localization файлы
- ✅ Entrypoint скрипты

## 🔒 Безопасность

### Production Safety Check

Перед каждой сборкой образа автоматически запускается проверка:

```powershell
python scripts\check-production-safety.py
```

Проверяет:
- ❌ Нет тестовых файлов в production
- ❌ CAREBOT_TEST_MODE не установлен
- ❌ Нет mock файлов
- ✅ Все production файлы на месте

### Sensitive данные

- `.env` файл НЕ включается в образ
- Токены передаются через environment variables
- База данных монтируется как volume (не в образе)

## 🐛 Отладка проблем

### Образ не собирается

```powershell
# Просмотр логов сборки
.\scripts\wsl2-deploy.ps1 build

# Очистка кеша и повторная сборка
.\scripts\wsl2-deploy.ps1 cleanup
.\scripts\wsl2-deploy.ps1 build --no-cache
```

### Файл отсутствует в образе

```bash
# Проверьте .dockerignore
cat .dockerignore

# Проверьте образ
docker run --rm carebot:latest ls -la /app/CareBot/

# Проверьте конкретный файл
docker run --rm carebot:latest cat /app/CareBot/handlers.py | head
```

### Образ не запускается на production

```powershell
# Проверьте логи
.\scripts\wsl2-deploy.ps1 logs

# Проверьте переменные окружения
ssh ubuntu@192.168.1.125 "docker exec carebot_production env"

# Проверьте health
curl http://192.168.1.125:5555/health
```

### WSL2 Docker не запускается

```bash
# В WSL2
sudo service docker status
sudo service docker start

# Проверка
docker ps
```

## 📊 Сравнение старого и нового подхода

| Аспект | Старый (remote build) | Новый (WSL2) |
|--------|----------------------|--------------|
| Сборка | На production сервере | Локально в WSL2 |
| Скорость | Медленная (SSH) | Быстрая (локально) |
| Прозрачность | Низкая | Высокая ✅ |
| Тестирование | Сложное | Простое ✅ |
| Отладка | Сложная | Легкая ✅ |
| Нагрузка на production | Высокая | Низкая ✅ |
| Контроль версий | Сложный | Простой ✅ |

## 🎓 Best Practices

### 1. Всегда проверяйте образ перед деплоем

```powershell
.\scripts\wsl2-deploy.ps1 inspect
.\scripts\wsl2-deploy.ps1 test
```

### 2. Используйте версионирование

```powershell
# Тегируйте образы
.\scripts\wsl2-deploy.ps1 build --tag v1.2.3
```

### 3. Делайте бэкапы

```powershell
# Автоматический бэкап перед деплоем
.\scripts\wsl2-deploy.ps1 full
```

### 4. Проверяйте безопасность

```powershell
# Автоматическая проверка
python scripts\check-production-safety.py
```

### 5. Тестируйте локально

```powershell
# Запустите тот же образ локально
.\scripts\wsl2-deploy.ps1 test
```

## 🚨 Миграция со старого workflow

### Первый деплой через WSL2

1. **Создайте финальный бэкап старым способом**:
   ```powershell
   .\scripts\update-production.ps1 backup
   ```

2. **Соберите образ в WSL2**:
   ```powershell
   .\scripts\wsl2-deploy.ps1 build
   ```

3. **Протестируйте локально**:
   ```powershell
   .\scripts\wsl2-deploy.ps1 test
   ```

4. **Задеплойте новым способом**:
   ```powershell
   .\scripts\wsl2-deploy.ps1 deploy
   ```

5. **Проверьте работоспособность**:
   ```powershell
   .\scripts\wsl2-deploy.ps1 status
   curl http://192.168.1.125:5555/health
   ```

### Откат (если нужно)

```bash
# На production сервере
ssh ubuntu@192.168.1.125
cd /home/ubuntu
sudo rm -rf carebot-production
sudo cp -r carebot-backup-YYYYMMDD-HHMMSS carebot-production
cd carebot-production
docker compose -f docker-compose.production.yml up -d
```

## 📚 Дополнительные ресурсы

- [Docker в WSL2 официальная документация](https://docs.docker.com/desktop/wsl/)
- [WSL2 Best Practices](https://learn.microsoft.com/en-us/windows/wsl/setup/environment)
- [Docker Multi-stage builds](https://docs.docker.com/build/building/multi-stage/)

---

*Последнее обновление: January 31, 2026*
