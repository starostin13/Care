# WSL2 Deployment - Examples & Use Cases

## 📚 Примеры использования wsl2-deploy.ps1

### Базовые сценарии

#### 1. Первый деплой после настройки WSL2

```powershell
# Проверяем готовность
.\scripts\wsl2-deploy.ps1 check-wsl

# Проверяем безопасность
python scripts\check-production-safety.py

# Полный цикл с тестированием
.\scripts\wsl2-deploy.ps1 full
```

**Что происходит:**
1. ✅ Сборка образа в WSL2
2. 🔍 Инспекция содержимого образа
3. 🧪 Локальное тестирование на порту 5556
4. 📤 Деплой на production (с подтверждением)
5. ✅ Проверка health endpoint

#### 2. Быстрое исправление бага

```powershell
# Вносим изменения в код

# Сборка и деплой без тестирования
.\scripts\wsl2-deploy.ps1 build
.\scripts\wsl2-deploy.ps1 deploy -Force
```

**Опция `-Force`:** Пропускает подтверждения (но создает бэкап)

#### 3. Разработка новой фичи

```powershell
# 1. Тестируем локально в test mode
.\scripts\test-mode.ps1 start
# ... тестирование с Telegram ...
.\scripts\test-mode.ps1 stop

# 2. Проверяем безопасность
python scripts\check-production-safety.py

# 3. Собираем образ
.\scripts\wsl2-deploy.ps1 build

# 4. Проверяем что попало в образ
.\scripts\wsl2-deploy.ps1 inspect

# 5. Тестируем образ локально
.\scripts\wsl2-deploy.ps1 test
# Проверяем http://localhost:5556/health
# Тестируем функционал через Telegram

# 6. Деплоим на production
.\scripts\wsl2-deploy.ps1 deploy

# 7. Проверяем production
.\scripts\wsl2-deploy.ps1 status
curl http://192.168.1.125:5555/health
```

### Работа с образами

#### 4. Инспекция образа перед деплоем

```powershell
# Собрать образ
.\scripts\wsl2-deploy.ps1 build

# Детальная инспекция
.\scripts\wsl2-deploy.ps1 inspect
```

**Вывод покажет:**
```
ℹ️  INFO: Image details:
REPOSITORY   TAG      IMAGE ID      CREATED         SIZE
carebot      latest   abc123def456  2 minutes ago   280MB

ℹ️  INFO: Listing files in image /app/CareBot/:
-rw-r--r-- 1 root root  15234 Jan 31 12:30 handlers.py
-rw-r--r-- 1 root root   8901 Jan 31 12:30 mission_helper.py
...

✅ SUCCESS: /app/run_hybrid.py - EXISTS
✅ SUCCESS: /app/CareBot/handlers.py - EXISTS
```

#### 5. Проверка конкретного файла в образе

```powershell
# Вход в WSL2
wsl -d Ubuntu-22.04

# Проверить файл
sudo docker run --rm carebot:latest cat /app/CareBot/mission_helper.py | head -50

# Проверить переменные окружения
sudo docker inspect carebot:latest --format='{{.Config.Env}}'

# Размер слоев
sudo docker history carebot:latest
```

#### 6. Управление версиями образов

```powershell
# Сборка с тегом версии
.\scripts\wsl2-deploy.ps1 build -Tag v1.2.3

# Список образов
.\scripts\wsl2-deploy.ps1 images

# Деплой конкретной версии
.\scripts\wsl2-deploy.ps1 deploy -Tag v1.2.3

# Очистка старых версий
.\scripts\wsl2-deploy.ps1 cleanup
```

### Тестирование

#### 7. Локальное тестирование образа

```powershell
# Запустить тестовый контейнер
.\scripts\wsl2-deploy.ps1 test

# Тестируем функционал
# http://localhost:5556/health - health check
# Telegram бот доступен с тестовым токеном

# Логи тестового контейнера
wsl -d Ubuntu-22.04 -e bash -c "sudo docker logs carebot_test --tail=50"

# Остановить тест
.\scripts\wsl2-deploy.ps1 stop-test
```

#### 8. Тестирование с разными конфигурациями

```powershell
# Сборка без кеша (чистая сборка)
.\scripts\wsl2-deploy.ps1 build -NoCache

# Запуск теста
.\scripts\wsl2-deploy.ps1 test

# Проверка health
curl http://localhost:5556/health

# Если все ок - деплой
.\scripts\wsl2-deploy.ps1 deploy
```

### Миграции

#### 9. Обновление только миграций

```powershell
# Создали новую миграцию: CareBot/CareBot/migrations/009_new_table.py

# Синхронизируем миграции на production
.\scripts\wsl2-deploy.ps1 migrations

# Проверяем статус
.\scripts\wsl2-deploy.ps1 migration-status

# Применяем
.\scripts\wsl2-deploy.ps1 apply-migrations

# Проверяем логи
.\scripts\wsl2-deploy.ps1 logs
```

#### 10. Миграции + деплой кода

```powershell
# Создали миграцию и обновили код

# Сначала синхронизируем миграции
.\scripts\wsl2-deploy.ps1 migrations
.\scripts\wsl2-deploy.ps1 apply-migrations

# Затем деплоим новый код
.\scripts\wsl2-deploy.ps1 build
.\scripts\wsl2-deploy.ps1 deploy
```

### Production управление

#### 11. Мониторинг production

```powershell
# Статус контейнера
.\scripts\wsl2-deploy.ps1 status

# Последние 50 строк логов
.\scripts\wsl2-deploy.ps1 logs

# Прямой доступ к логам
ssh ubuntu@192.168.1.125 "cd /home/ubuntu/carebot-production && docker compose logs --tail=100 --follow"
```

#### 12. Перезапуск production

```powershell
# Простой перезапуск (без пересборки)
.\scripts\wsl2-deploy.ps1 restart

# Полный перезапуск с новым образом
.\scripts\wsl2-deploy.ps1 build
.\scripts\wsl2-deploy.ps1 deploy
```

#### 13. Создание бэкапа

```powershell
# Ручной бэкап
.\scripts\wsl2-deploy.ps1 backup

# Автоматический бэкап создается при:
.\scripts\wsl2-deploy.ps1 deploy
.\scripts\wsl2-deploy.ps1 full
```

### Отладка и troubleshooting

#### 14. Отладка проблем со сборкой

```powershell
# Проверка WSL2 и Docker
.\scripts\wsl2-deploy.ps1 check-wsl

# Очистка кеша
.\scripts\wsl2-deploy.ps1 cleanup

# Сборка без кеша с подробным выводом
.\scripts\wsl2-deploy.ps1 build -NoCache
```

#### 15. Отладка проблем с запуском

```powershell
# Локальный тест для отладки
.\scripts\wsl2-deploy.ps1 test

# Логи тестового контейнера
wsl -d Ubuntu-22.04 -e bash -c "sudo docker logs carebot_test"

# Проверка health
curl http://localhost:5556/health

# Заходим внутрь контейнера
wsl -d Ubuntu-22.04 -e bash -c "sudo docker exec -it carebot_test bash"
```

#### 16. Проверка что файл попал в образ

```powershell
# Инспекция образа
.\scripts\wsl2-deploy.ps1 inspect

# Или напрямую в WSL2
wsl -d Ubuntu-22.04 -e bash -c "sudo docker run --rm carebot:latest ls -la /app/CareBot/ | grep mission_helper"

# Проверка содержимого файла
wsl -d Ubuntu-22.04 -e bash -c "sudo docker run --rm carebot:latest cat /app/CareBot/config.py"
```

### Сложные сценарии

#### 17. Откат на предыдущую версию

```powershell
# 1. Посмотреть доступные бэкапы
ssh ubuntu@192.168.1.125 "ls -ld /home/ubuntu/carebot-backup-* | tail -5"

# 2. Откатиться на предыдущую версию
ssh ubuntu@192.168.1.125
cd /home/ubuntu
sudo docker compose -f carebot-production/docker-compose.production.yml down
sudo rm -rf carebot-production
sudo cp -r carebot-backup-20260131-120000 carebot-production
cd carebot-production
sudo docker compose -f docker-compose.production.yml up -d
exit

# 3. Проверить
.\scripts\wsl2-deploy.ps1 status
```

#### 18. Сохранение образа для архива

```powershell
# Сохранить образ в tar файл
.\scripts\wsl2-deploy.ps1 save

# Файл создается: carebot-latest.tar

# Можно указать тег
.\scripts\wsl2-deploy.ps1 build -Tag v1.2.3
.\scripts\wsl2-deploy.ps1 save -Tag v1.2.3
# Создается: carebot-v1.2.3.tar
```

#### 19. Деплой с пропуском health check

```powershell
# Быстрый деплой без проверки (для emergency fixes)
.\scripts\wsl2-deploy.ps1 build
.\scripts\wsl2-deploy.ps1 deploy -Force -SkipHealthCheck

# Проверка вручную потом
.\scripts\wsl2-deploy.ps1 status
```

#### 20. Параллельная разработка (feature branch)

```powershell
# Feature branch development
git checkout feature/new-missions

# Сборка с тегом ветки
.\scripts\wsl2-deploy.ps1 build -Tag feature-new-missions

# Локальное тестирование
.\scripts\wsl2-deploy.ps1 test -Tag feature-new-missions

# Если готово к мержу
git checkout main
git merge feature/new-missions

# Production деплой
.\scripts\wsl2-deploy.ps1 full
```

### Автоматизация

#### 21. Continuous Integration пример

```powershell
# CI/CD скрипт (можно использовать в GitHub Actions)
function Deploy-CI {
    # 1. Safety check
    python scripts\check-production-safety.py
    if ($LASTEXITCODE -ne 0) { exit 1 }
    
    # 2. Build
    .\scripts\wsl2-deploy.ps1 build -NoCache
    if ($LASTEXITCODE -ne 0) { exit 1 }
    
    # 3. Test locally
    .\scripts\wsl2-deploy.ps1 test
    Start-Sleep -Seconds 30
    
    $health = curl http://localhost:5556/health 2>$null
    .\scripts\wsl2-deploy.ps1 stop-test
    
    if (-not $health) { exit 1 }
    
    # 4. Deploy to production
    .\scripts\wsl2-deploy.ps1 deploy -Force -SkipHealthCheck
    
    # 5. Verify production
    Start-Sleep -Seconds 15
    .\scripts\wsl2-deploy.ps1 status
}

Deploy-CI
```

#### 22. Scheduled maintenance

```powershell
# Еженедельное обслуживание
function Weekly-Maintenance {
    Write-Host "Weekly maintenance started..."
    
    # Бэкап
    .\scripts\wsl2-deploy.ps1 backup
    
    # Очистка старых образов
    .\scripts\wsl2-deploy.ps1 cleanup
    
    # Проверка health
    .\scripts\wsl2-deploy.ps1 status
    
    # Логи за последние 24 часа
    ssh ubuntu@192.168.1.125 "cd /home/ubuntu/carebot-production && docker compose logs --since 24h > /home/ubuntu/logs-$(date +%Y%m%d).txt"
    
    Write-Host "Maintenance completed!"
}

Weekly-Maintenance
```

## 🎯 Шпаргалка команд

```powershell
# Разработка
.\scripts\test-mode.ps1 start              # Локальная разработка
python scripts\check-production-safety.py  # Проверка безопасности

# Сборка
.\scripts\wsl2-deploy.ps1 build            # Собрать образ
.\scripts\wsl2-deploy.ps1 build -NoCache   # Без кеша
.\scripts\wsl2-deploy.ps1 build -Tag v1.0  # С версией

# Проверка
.\scripts\wsl2-deploy.ps1 inspect          # Что в образе
.\scripts\wsl2-deploy.ps1 images           # Список образов
.\scripts\wsl2-deploy.ps1 test             # Тест локально

# Деплой
.\scripts\wsl2-deploy.ps1 deploy           # Деплой на prod
.\scripts\wsl2-deploy.ps1 full             # Полный цикл
.\scripts\wsl2-deploy.ps1 deploy -Force    # Без подтверждений

# Production
.\scripts\wsl2-deploy.ps1 status           # Статус
.\scripts\wsl2-deploy.ps1 logs             # Логи
.\scripts\wsl2-deploy.ps1 restart          # Перезапуск
.\scripts\wsl2-deploy.ps1 backup           # Бэкап

# Миграции
.\scripts\wsl2-deploy.ps1 migrations       # Синхронизация
.\scripts\wsl2-deploy.ps1 apply-migrations # Применить
.\scripts\wsl2-deploy.ps1 migration-status # Статус

# Утилиты
.\scripts\wsl2-deploy.ps1 cleanup          # Очистка
.\scripts\wsl2-deploy.ps1 check-wsl        # Проверка WSL2
.\scripts\wsl2-deploy.ps1 safety-check     # Проверка безопасности
```

---

**Документация:**
- [WSL2_QUICKSTART.md](WSL2_QUICKSTART.md) - быстрый старт
- [WSL2_DEPLOYMENT.md](WSL2_DEPLOYMENT.md) - полная документация
- [WSL2_TECHNICAL.md](WSL2_TECHNICAL.md) - технические детали
- [agents.md](agents.md) - для AI агентов

**Дата:** January 31, 2026
