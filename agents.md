# Agents Guide - CareBot Project

Этот файл содержит принципы и соглашения для разработчиков и AI агентов, работающих с проектом CareBot.

## Миграции базы данных

### Структура миграций

Все миграции базы данных должны храниться в папке `CareBot/CareBot/migrations/` и следовать определенной схеме именования:

```
CareBot/CareBot/migrations/
    ├── 001_add_language_and_notifications.py
    ├── 003_migrate_texts_table.py
    ├── 004_fix_localization_table.py
    ├── 005_add_name_input_translations.py
    ├── 006_add_game_notification_text.py
    ├── 007_add_missions_title_text.py
    ├── 008_safe_warmasters_schema_update.py
    ├── 20251106_01_add_is_admin_to_warmasters.sql
    └── README.md
```

### Принципы именования миграций

1. **Номер миграции** - трехзначное число в начале имени (001, 002, 003, ...)
2. **Описательное название** - краткое описание изменений в snake_case
3. **Расширение файла**:
   - `.py` - для yoyo-migrations с логикой и проверками (ПРЕДПОЧТИТЕЛЬНО)
   - `.sql` - для простых SQL скриптов (использовать осторожно!)

### ⚠️ КРИТИЧЕСКИ ВАЖНО: Безопасность данных

**НИКОГДА не используйте деструктивные операции:**
- ❌ `DROP TABLE` 
- ❌ `DELETE FROM table`
- ❌ `TRUNCATE`
- ❌ Неполные `INSERT` операции

**Всегда используйте безопасные операции:**
- ✅ `ALTER TABLE ADD COLUMN`
- ✅ `CREATE TABLE IF NOT EXISTS`
- ✅ `UPDATE` с WHERE условиями
- ✅ Проверки существования данных

### Система деплоя миграций на production

#### 🏗️ Архитектура миграций

**Production использует volume-based систему:**
```yaml
# docker-compose.production.yml
volumes:
  - ./migrations:/app/CareBot/migrations  # Отдельный volume для миграций
```

#### 📤 Процесс деплоя миграций

1. **Создание миграции локально:**
   ```
   CareBot/CareBot/migrations/009_new_feature.py
   ```

2. **Синхронизация с production:**
   ```powershell
   .\scripts\update-production.ps1 migrations
   ```
   - Копирует ТОЛЬКО файлы миграций
   - Не требует пересборки контейнера
   - Обновляет volume `/home/ubuntu/carebot-production/migrations/`

3. **Применение миграций:**
   ```powershell
   .\scripts\update-production.ps1 apply-migrations
   ```
   - Запускает `docker exec carebot_production python /app/CareBot/migrate_db.py`
   - Автоматически применяет pending миграции

#### 🔍 Управление миграциями

**Доступные команды:**
```powershell
# Проверить статус миграций
.\scripts\update-production.ps1 migration-status

# Синхронизировать только миграции
.\scripts\update-production.ps1 migrations

# Применить pending миграции
.\scripts\update-production.ps1 apply-migrations

# Полное обновление (код + миграции + рестарт)
.\scripts\update-production.ps1 update
```

#### 📂 Расположение файлов

**На production сервере:**
- Production код: `/home/ubuntu/carebot-production/`
- **Миграции**: `/home/ubuntu/carebot-production/migrations/` (volume)
- В контейнере: `/app/CareBot/migrations/` (смонтировано из volume)

**Важно:** Миграции НЕ включены в Docker образ - они монтируются как volume!

### Примеры правильных миграций

#### Python миграция (рекомендуется):
```python
# 009_add_new_feature.py
"""
Migration 009: Безопасное добавление новой функции
"""
from yoyo import step

def add_feature_safely(conn):
    cursor = conn.cursor()
    
    # Проверяем существование колонки
    cursor.execute("PRAGMA table_info(table_name)")
    columns = [col[1] for col in cursor.fetchall()]
    
    if 'new_column' not in columns:
        cursor.execute("ALTER TABLE table_name ADD COLUMN new_column TEXT DEFAULT 'value'")
        print("✅ Добавлена колонка new_column")
    else:
        print("✅ Колонка new_column уже существует")

steps = [step(add_feature_safely)]
```

#### SQL миграция (использовать осторожно):
```sql
-- 009_add_simple_column.sql
-- depends:

-- Добавляем колонку только если её нет
ALTER TABLE table_name ADD COLUMN new_column TEXT DEFAULT 'value';
```

### 🚨 Устранение проблем

#### Миграция не применилась:
1. Проверить статус: `.\scripts\update-production.ps1 migration-status`
2. Проверить логи: `.\scripts\update-production.ps1 logs`
3. Синхронизировать заново: `.\scripts\update-production.ps1 migrations`

#### Новые миграции не видны:
1. Убедиться что файл создан в `CareBot/CareBot/migrations/`
2. Синхронизировать: `.\scripts\update-production.ps1 migrations`
3. Проверить в контейнере: `docker exec carebot_production ls -la /app/CareBot/migrations/`

#### Ошибка "duplicate column":
- Это нормально для повторного применения
- Значит колонка уже существует
- Миграция должна содержать проверки существования

### Лучшие практики

1. **Всегда создавать бэкап перед миграцией**
2. **Тестировать миграции локально**
3. **Использовать проверки существования в коде**
4. **Избегать деструктивных операций**
5. **Документировать назначение миграции**
6. **Синхронизировать миграции отдельно от кода для быстрых исправлений**

### Работа с winner_bonus

Специальные правила для работы с наградами победителей:

- `winner_bonus` хранится в таблице `mission_stack`
- Это **секретная** информация, недоступная до окончания битвы
- Используйте `get_winner_bonus(mission_id)` для получения после определения победителя
- НЕ возвращайте winner_bonus в `get_mission_details()`

## Структура миссий

### Типы миссий и их награды

#### Kill Team миссии:
- `Loot` - оба получают 1 ресурс, победитель дополнительные ресурсы
- `Transmission` - победитель получает ресурсы равные ресурсам противника
- `Secure` - победитель получает 2 ресурса
- `Intel` - создает склад в гексе миссии
- `Sabotage` - нет изменений ресурсов
- `Extraction` - победитель +1 ресурс, проигравший -1 ресурс
- `Power Surge` - проигравший теряет ресурсы равные количеству складов (минимум 1)
- `Coordinates` - проигравший теряет ресурсы + один склад уничтожается

#### WH40K миссии:
- Имеют секретный `winner_bonus` который раскрывается только победителю
- Примеры бонусов: дополнительный опыт для юнитов, бонусы к следующим битвам

### Функции для работы с миссиями

- `generate_new_one(rules)` - создает новую миссию с бонусом для wh40k
- `get_mission(rules)` - получает миссию без раскрытия секретов
- `apply_mission_rewards()` - применяет награды и раскрывает секретные бонусы
- `get_winner_bonus(mission_id)` - получает секретный бонус (только после битвы!)

## Веб-интерфейс администратора

### Архитектура аутентификации

**Двухслойная система доступа:**

1. **Таблица warmasters** - источник истины для статуса админа
   - Поле `is_admin` (INTEGER, 0 или 1)
   - Управляется через Telegram бота командой `/make_admin`
   - Определяет КТО может быть админом

2. **Таблица admin_users** - веб-пароли для админов
   - Хранит только `password_hash` (bcrypt)
   - `warmaster_id` как PRIMARY KEY (FOREIGN KEY -> warmasters.id)
   - Определяет ЧТО нужно для веб-входа

**Процесс авторизации:**
```python
# 1. Проверка статуса админа
if not is_user_admin(telegram_id):  # warmasters.is_admin == 1
    return False

# 2. Проверка веб-пароля
if not verify_admin_web_credentials(telegram_id, password):  # admin_users.password_hash
    return False

# 3. Успешный вход
```

### Управление веб-доступом

**Установка пароля для админа:**
```bash
# Интерактивный режим
python scripts/set_admin_password.py

# Просмотр админов
python scripts/set_admin_password.py list

# Установка напрямую
python scripts/set_admin_password.py set <warmaster_id> <password>
```

**Требования:**
- Warmaster должен иметь `is_admin=1` (устанавливается через Telegram)
- Пароль минимум 4 символа
- Пароль хешируется bcrypt с солью

### Функции sqllite_helper для веб-доступа

- `set_admin_web_password(telegram_id, password)` - установить/обновить веб-пароль
- `verify_admin_web_credentials(telegram_id, password)` - проверка логина
- `has_admin_web_password(telegram_id)` - есть ли веб-пароль
- `get_all_admins_with_web_access()` - список админов с индикатором пароля
- `update_admin_last_login(telegram_id)` - обновить last_login
- `get_admin_web_info(telegram_id)` - информация о веб-доступе админа

### Endpoints

**Публичные:**
- `GET /login` - форма входа с выбором админа
- `POST /login` - обработка логина
- `GET /logout` - выход из системы

**Защищенные (требуют @auth.admin_required):**
- `GET /admin/dashboard` - главная панель с статистикой
- `GET /admin/enter-result` - (в разработке) ввод результата битвы
- `GET /admin/create-mission` - (в разработке) создание новой миссии

**API endpoints (в разработке):**
- `GET /api/warmasters` - список warmasters
- `GET /api/active-missions` - активные миссии
- `POST /api/complete-mission` - завершить миссию от админа

### Безопасность

**Настройки сессий:**
- `SESSION_TYPE = 'filesystem'` - сессии на диске
- `SESSION_COOKIE_SECURE = True` - только HTTPS
- `SESSION_COOKIE_HTTPONLY = True` - защита от XSS
- `PERMANENT_SESSION_LIFETIME = 3600` - 1 час
- `SECRET_KEY` - случайный 32-байтный ключ

**HTTPS/SSL:**
- Flask adhoc SSL для разработки (`ssl_context='adhoc'`)
- Самоподписанные сертификаты нужно установить на устройствах
- См. `SSL_SETUP.md` для инструкций по платформам

**Защита от атак:**
- Bcrypt для хеширования паролей (cost factor 12)
- Параметризованные SQL запросы (SQLite injection защита)
- Flask-Login для управления сессиями
- HttpOnly cookies против XSS

### PWA поддержка (в разработке)

**Требования для PWA:**
- ✅ HTTPS (adhoc SSL настроен)
- ⏳ Service Worker (планируется)
- ⏳ Web Manifest (планируется)
- ⏳ Offline caching (IndexedDB)

**Offline функционал:**
- Кеширование карты и edges для офлайн генерации миссий
- IndexedDB для хранения pending результатов
- Background sync при восстановлении соединения

### Лучшие практики веб-админки

1. **Никогда не дублируйте is_admin статус** - всегда используйте `warmasters.is_admin`
2. **Всегда проверяйте is_admin перед операциями** - двойная проверка (таблица + функция)
3. **Логируйте admin действия** - кто, когда, что изменил
4. **Используйте транзакции** - особенно для критичных операций
5. **Тестируйте через mock режим** - не используйте production базу для тестов

## Соглашения по коду

### База данных
- Используйте `aiosqlite` для асинхронного доступа к SQLite
- Всегда используйте параметризованные запросы для предотвращения SQL-инъекций
- Закрывайте соединения с базой данных (`async with aiosqlite.connect()`)

### Логирование
- Используйте `logging` для отслеживания важных операций
- Особенно важно логировать применение наград и изменения ресурсов

### Обработка ошибок
- Проверяйте существование записей перед их использованием
- Graceful degradation при отсутствии данных
- Логируйте ошибки для отладки

## Деплой и инфраструктура

### 🐳 WSL2 + Docker деплой (ПРИОРИТЕТНЫЙ СПОСОБ)

С января 2026 года **единственный приоритетный** способ деплоя — использование WSL2 + Docker на локальной машине.
**Не копировать код на сервер для сборки образа**: сборка и тестирование выполняются локально в WSL2, на сервер отправляется только готовый образ и команды деплоя.

#### Преимущества WSL2 подхода

✅ **Прозрачность образа**: Точно видно какие файлы попали в Docker образ  
✅ **Быстрая сборка**: Локальный кеш слоев Docker  
✅ **Независимость**: Не требуется Docker на production для сборки  
✅ **Тестирование**: Можно запустить тот же образ локально перед деплоем  
✅ **Контроль версий**: Легко управлять тегами и версиями образов  
✅ **Безопасность**: Production safety check перед сборкой образа

#### Основной workflow деплоя

```powershell
# Полный цикл (build → inspect → test → deploy)
.\scripts\wsl2-deploy.ps1 full

# Или по шагам:
.\scripts\wsl2-deploy.ps1 build          # Сборка образа в WSL2
.\scripts\wsl2-deploy.ps1 inspect        # Проверка содержимого образа
.\scripts\wsl2-deploy.ps1 test           # Тестирование локально
.\scripts\wsl2-deploy.ps1 deploy         # Деплой на production
```

#### Ключевые команды wsl2-deploy.ps1

**Сборка и тестирование:**
- `build` - сборка Docker образа в WSL2
- `inspect` - просмотр содержимого образа (что попало в образ)
- `test` - запуск образа локально на порту 5556
- `stop-test` - остановка локального тестового контейнера

**Деплой:**
- `deploy` - деплой на production
- `full` - полный цикл (build → test → deploy)

**Управление production:**
- `status` - статус production сервиса
- `logs` - логи production
- `restart` - перезапуск production
- `backup` - создание бэкапа

**Миграции:**
- `migrations` - синхронизация файлов миграций
- `apply-migrations` - применение миграций
- `migration-status` - статус миграций

**Утилиты:**
- `images` - список Docker образов
- `cleanup` - очистка старых образов
- `check-wsl` - проверка WSL2 и Docker
- `safety-check` - production safety проверка

#### Инспекция образа

**Проверка что попало в образ:**
```powershell
.\scripts\wsl2-deploy.ps1 inspect
```

Показывает:
- Список всех файлов в образе
- Размер каждого слоя
- Переменные окружения
- Exposed порты
- Команду запуска

**Проверка конкретных файлов:**
```bash
# В WSL2
wsl -d Ubuntu-22.04
cd /mnt/c/Users/staro/Projects/Care

# Проверить файлы
sudo docker run --rm carebot:latest ls -la /app/CareBot/

# Проверить конкретный файл
sudo docker run --rm carebot:latest cat /app/CareBot/mission_helper.py | head -20
```

#### Типичный workflow для агентов

1. **Разработка и тестирование локально:**
   ```powershell
   # Тестируем без Docker
   .\scripts\test-mode.ps1 start
   ```

2. **Production safety check:**
   ```powershell
   python scripts\check-production-safety.py
   ```

3. **Сборка образа:**
   ```powershell
   .\scripts\wsl2-deploy.ps1 build
   ```

4. **Проверка образа:**
   ```powershell
   .\scripts\wsl2-deploy.ps1 inspect
   ```

5. **Тестирование образа локально (опционально):**
   ```powershell
   .\scripts\wsl2-deploy.ps1 test
   # Проверить http://localhost:5556/health
   ```

6. **Деплой на production:**
   ```powershell
   .\scripts\wsl2-deploy.ps1 deploy
   ```

7. **Проверка production:**
   ```powershell
   .\scripts\wsl2-deploy.ps1 status
   ```

#### Что попадает в образ, а что нет

**✅ Попадает в образ:**
- Python runtime (3.11-slim)
- Все зависимости из requirements.txt
- Production код (handlers, helpers, config)
- Localization файлы
- Entrypoint скрипты

**❌ НЕ попадает в образ:**
- `mock_sqlite_helper.py` (тестовые файлы)
- `test_*.py` (тесты)
- `.git/` (репозиторий)
- `scripts/` (deployment скрипты)
- База данных (монтируется через volume)
- Миграции (монтируются через volume)

#### Отладка проблем

**Файл отсутствует в образе:**
```bash
# Проверьте .dockerignore
cat .dockerignore

# Проверьте образ
wsl -d Ubuntu-22.04 -e bash -c "sudo docker run --rm carebot:latest ls -la /app/CareBot/"
```

**Образ не запускается:**
```powershell
# Проверьте логи
.\scripts\wsl2-deploy.ps1 logs

# Проверьте health
curl http://192.168.1.125:5555/health
```

**Полная документация:** См. [WSL2_DEPLOYMENT.md](WSL2_DEPLOYMENT.md)

### Legacy Docker деплой (УСТАРЕЛ, ТОЛЬКО ДЛЯ ЭКСТРЕННЫХ СЛУЧАЕВ)

- ⚠️ **Устаревший способ**: `scripts/update-production.ps1`
- Использовать **только если WSL2 недоступен**. Не копируйте код на сервер для сборки образа — это больше не основной путь.
- Собирает образ на production сервере
- Менее прозрачен и медленнее
- **Рекомендуется мигрировать на WSL2 деплой**

### Система бэкапов (ВАЖНО ДЛЯ АГЕНТОВ!)
- **Расположение бэкапов**: `/home/ubuntu/carebot-backup-YYYYMMDD-HHMMSS/` на сервере ubuntu@192.168.1.125
- **Автоматические бэкапы**: создаются перед каждым обновлением через `update-production.ps1`
- **Формат имени**: `carebot-backup-20251114-003209` (год-месяц-день-час-минута-секунда)
- **Команды для работы с бэкапами**:
  - Просмотр: `ssh ubuntu@192.168.1.125 'ls -d /home/ubuntu/carebot-backup-*'`
  - Создание: `.\scripts\update-production.ps1 backup`
  - Восстановление: см. документацию в `scripts/README.md`

### Скрипты управления

#### Production деплой и управление
- `scripts/update-production.ps1` - **ОСНОВНОЙ СКРИПТ** для управления production
  - `update` - полное обновление с бэкапом и проверками
  - `migrations` - синхронизация только файлов миграций
  - `apply-migrations` - применение pending миграций
  - `migration-status` - проверка статуса миграций
  - `admin` - запуск SQLite веб-интерфейса
  - `backup` - создание резервной копии
  - `status`, `logs`, `start`, `stop`, `restart` - управление сервисом

#### Устаревшие скрипты (НЕ ИСПОЛЬЗОВАТЬ)
- `scripts/deploy.ps1` - устарел, заменен на `update-production.ps1`
- `scripts/test-local.ps1` - локальное тестирование Docker образа

#### Endpoints и мониторинг
- `/health` - health check для мониторинга (http://192.168.1.125:5555/health)
- Возвращает статус приложения и базы данных
- SQLite веб-интерфейс: http://192.168.1.125:8080 (только в admin режиме)

### Переменные окружения
- `DATABASE_PATH` - путь к файлу базы данных SQLite
- `SERVER_HOST` - хост для привязки сервера (0.0.0.0 в продакшене)
- `SERVER_PORT` - порт сервера (по умолчанию 5555)

## Тестовый режим

### Обзор
CareBot поддерживает специальный локальный тестовый режим для безопасного тестирования без воздействия на production данные.

### Архитектура тестового режима
- **Mock база данных**: Все операции эмулируются в памяти без реального SQLite
- **Отдельный Telegram токен**: `8270355955:AAGm2RuyzbUO_2p4lhXwkOtolkrcgshuZ-4`
- **Локальный Python процесс**: Запускается напрямую, не через Docker
- **Автоматическое переключение**: Все `*_helper.py` файлы автоматически используют mock версии

### Запуск локального тестового режима
```powershell
# Основные команды
.\scripts\test-mode.ps1 start     # Запустить локально
.\scripts\test-mode.ps1 status    # Проверить статус  
.\scripts\test-mode.ps1 debug     # Debug информация
.\scripts\test-mode.ps1 stop      # Остановить процессы
```

### Ключевые файлы
- `mock_sqlite_helper.py` - mock версия базы данных  
- `scripts/test-mode.ps1` - управление локальным тестовым режимом
- `TEST_MODE_GUIDE.md` - подробная документация

### Переменные окружения
- `CAREBOT_TEST_MODE=true` - автоматически устанавливается скриптом
- `TELEGRAM_BOT_TOKEN_TEST` - токен тестового бота (настроен в config.py)

### Mock данные
- 2 тестовых пользователя (admin и обычный)
- 5 альянсов с разными цветами  
- Предустановленные миссии и настройки
- Все данные эфемерны (существуют только во время работы процесса)

### Безопасность тестового режима
- ❌ НЕ сохраняет данные (только в памяти)
- ✅ Полностью изолирован от production
- ✅ Отдельный Telegram токен
- ✅ Локальный Python процесс без Docker

### 🛡️ КРИТИЧЕСКИ ВАЖНО: Production безопасность

**Тестовые файлы НЕ ДОЛЖНЫ попадать в production!**

Защитные механизмы:
- ✅ `.dockerignore` исключает `mock_sqlite_helper.py` и тестовые файлы
- ✅ `mock_sqlite_helper.py` падает с ошибкой если `CAREBOT_TEST_MODE != true`
- ✅ `scripts/check-production-safety.py` проверяет наличие тестовых файлов
- ✅ `update-production.ps1` автоматически запускает проверку безопасности

**Автоматическая проверка при деплое:**
```powershell
.\scripts\update-production.ps1 update
# Автоматически запускает:
# 1. Production safety check
# 2. Блокирует деплой если найдены тестовые файлы
# 3. Проверяет что CAREBOT_TEST_MODE != true
```

**Ручная проверка безопасности:**
```powershell
python scripts\check-production-safety.py
```

### Преимущества локального режима
- ✅ Быстрый запуск без Docker
- ✅ Логи прямо в консоли  
- ✅ Легкая отладка с breakpoints
- ✅ Мгновенный перезапуск
- ✅ Не требует сборки образа

### Workflow
1. Разработка: `test-mode.ps1 start` (логи в консоли)
2. Отладка: Ctrl+C для остановки, редактирование кода, повторный запуск
3. Тестирование: быстрые итерации без пересборки
4. Production: `update-production.ps1 update`

### VS Code Integration
- **F5** - запуск тестового режима с отладчиком
- **Ctrl+Shift+P** → "Tasks: Run Task" - доступ к автоматизированным задачам
- Настроенные конфигурации launch.json для всех режимов
- Breakpoints работают в тестовом режиме
- Подробности в `VSCODE_QUICKSTART.md`

## 🔧 Исправление процесса деплоя (Ноябрь 2025)

### ⚠️ КРИТИЧЕСКАЯ ПРОБЛЕМА РЕШЕНА

**Проблема:** Повторяющиеся ошибки `KeyError: 'ContainerConfig'` при деплое

**Причина:** Несовместимость legacy docker-compose v1.29.2 с modern Docker v28.5.1

**Решение:** Все функции в `update-production.ps1` исправлены для использования `docker compose` (v2.40.0) вместо `docker-compose` (v1.29.2)

### 🎯 Исправленные функции

- ✅ Update-Production() - полный деплой
- ✅ Start-Service() - запуск
- ✅ Stop-Service() - остановка  
- ✅ Restart-Service() - перезапуск
- ✅ Start-AdminMode() - admin режим
- ✅ Stop-AdminMode() - выход из admin
- ✅ logs action - просмотр логов

### 📋 Версии на production

```bash
Docker version 28.5.1        # Modern 
docker-compose version 1.29.2 # Legacy (НЕ используется)
Docker Compose version v2.40.0 # Modern (используется)
```

### ✅ Проверенный workflow

```powershell
# Стабильный деплой
.\scripts\update-production.ps1 update

# Быстрый перезапуск  
.\scripts\update-production.ps1 restart

# Проверка здоровья
.\scripts\update-production.ps1 status
# SUCCESS: Service is healthy! Status: healthy
```

**Детали в `DEPLOYMENT_FIX.md`**

---

*Этот документ должен обновляться при добавлении новых соглашений и принципов работы с проектом.*