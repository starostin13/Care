# WSL2 Deployment - Quick Start

## 🚀 Быстрый старт

### Первичная настройка WSL2 (один раз)

```powershell
# 1. Установить WSL2
wsl --install -d Ubuntu-22.04

# 2. Настроить Docker в WSL2
wsl -d Ubuntu-22.04
sudo apt update && sudo apt install -y docker.io
sudo usermod -aG docker $USER
sudo service docker start

# 3. Настроить auto-start Docker
sudo nano /etc/wsl.conf
# Добавить:
# [boot]
# command = "service docker start"

# 4. Перезапустить WSL
exit
wsl --shutdown
```

### Проверка готовности

```powershell
# Проверить WSL2 и Docker
.\scripts\wsl2-deploy.ps1 check-wsl

# Production safety check
python scripts\check-production-safety.py
```

## 📋 Основные команды

### Быстрый деплой (рекомендуется)

```powershell
# Полный цикл: build → test → deploy
.\scripts\wsl2-deploy.ps1 full
```

### Поэтапный деплой

```powershell
# 1. Собрать образ
.\scripts\wsl2-deploy.ps1 build

# 2. Проверить что попало в образ
.\scripts\wsl2-deploy.ps1 inspect

# 3. Протестировать локально (опционально)
.\scripts\wsl2-deploy.ps1 test
# Проверить: http://localhost:5556/health

# 4. Остановить тест (если запускали)
.\scripts\wsl2-deploy.ps1 stop-test

# 5. Задеплоить на production
.\scripts\wsl2-deploy.ps1 deploy

# 6. Проверить production
.\scripts\wsl2-deploy.ps1 status
```

## 🔍 Частые задачи

### Проверка образа

```powershell
# Что попало в образ?
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

### Миграции

```powershell
# Синхронизировать миграции
.\scripts\wsl2-deploy.ps1 migrations

# Применить миграции
.\scripts\wsl2-deploy.ps1 apply-migrations

# Статус миграций
.\scripts\wsl2-deploy.ps1 migration-status
```

## 🛠️ Опции сборки

```powershell
# Сборка без кеша
.\scripts\wsl2-deploy.ps1 build -NoCache

# Сборка с тегом версии
.\scripts\wsl2-deploy.ps1 build -Tag v1.2.3

# Деплой без подтверждений
.\scripts\wsl2-deploy.ps1 deploy -Force

# Полный цикл без health check
.\scripts\wsl2-deploy.ps1 full -SkipHealthCheck
```

## 🐛 Отладка

### Проверить файл в образе

```bash
# В WSL2
wsl -d Ubuntu-22.04

# Проверить список файлов
sudo docker run --rm carebot:latest ls -la /app/CareBot/

# Проверить конкретный файл
sudo docker run --rm carebot:latest cat /app/CareBot/handlers.py | head -20
```

### Локальное тестирование

```powershell
# Запустить образ локально
.\scripts\wsl2-deploy.ps1 test

# Проверить health
curl http://localhost:5556/health

# Посмотреть логи тестового контейнера
wsl -d Ubuntu-22.04 -e bash -c "sudo docker logs carebot_test"

# Остановить тест
.\scripts\wsl2-deploy.ps1 stop-test
```

### Production логи

```powershell
# Через скрипт
.\scripts\wsl2-deploy.ps1 logs

# Напрямую
ssh ubuntu@192.168.1.125 "cd /home/ubuntu/carebot-production && docker compose logs --tail=50"
```

## 🎯 Workflow для разных сценариев

### Быстрое исправление бага

```powershell
# 1. Исправить код
# 2. Быстрый деплой
.\scripts\wsl2-deploy.ps1 build
.\scripts\wsl2-deploy.ps1 deploy -Force
```

### Новая фича с тестированием

```powershell
# 1. Разработка в test mode
.\scripts\test-mode.ps1 start

# 2. Safety check
python scripts\check-production-safety.py

# 3. Полный цикл с тестированием
.\scripts\wsl2-deploy.ps1 full
```

### Только обновление миграций

```powershell
# Синхронизировать и применить
.\scripts\wsl2-deploy.ps1 migrations
.\scripts\wsl2-deploy.ps1 apply-migrations
```

### Откат на предыдущую версию

```bash
# На production сервере
ssh ubuntu@192.168.1.125

# Список бэкапов
ls -d /home/ubuntu/carebot-backup-*

# Откат
cd /home/ubuntu
sudo rm -rf carebot-production
sudo cp -r carebot-backup-YYYYMMDD-HHMMSS carebot-production
cd carebot-production
docker compose -f docker-compose.production.yml up -d
```

## ✅ Чеклист перед деплоем

- [ ] Код протестирован в test mode
- [ ] Production safety check пройден
- [ ] .env файл актуален
- [ ] Миграции созданы (если нужно)
- [ ] Образ собран успешно
- [ ] Образ проинспектирован (нужные файлы на месте)
- [ ] Локальное тестирование пройдено (опционально)
- [ ] Бэкап создан (автоматически при deploy)

## 📚 Документация

- **WSL2_DEPLOYMENT.md** - полная документация WSL2 деплоя
- **agents.md** - общие принципы и соглашения
- **DEPLOYMENT.md** - legacy документация (устарела)

## 🆘 Помощь

```powershell
# Справка по командам
.\scripts\wsl2-deploy.ps1

# Проверка WSL2
.\scripts\wsl2-deploy.ps1 check-wsl

# Production safety
python scripts\check-production-safety.py
```

## 🎓 Сравнение с legacy деплоем

| Задача | Legacy | WSL2 |
|--------|--------|------|
| Сборка образа | На production сервере | Локально в WSL2 ✅ |
| Скорость | Медленная (SSH) | Быстрая ✅ |
| Прозрачность | Низкая | Высокая ✅ |
| Тестирование | Сложное | Простое ✅ |
| Команда | `update-production.ps1` | `wsl2-deploy.ps1` ✅ |

---

**Последнее обновление**: January 31, 2026
