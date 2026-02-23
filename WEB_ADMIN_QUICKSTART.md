# Web Admin Quickstart Guide

Быстрый старт для разработки и тестирования веб-админки CareBot.

## 🚀 Первый запуск

### 1. Убедитесь что есть администраторы

```bash
# Проверить список админов
python scripts/set_admin_password.py list
```

Если нет админов - назначьте через Telegram бота:
```
/make_admin @username
```

### 2. Установите веб-пароль

```bash
# Интерактивный режим
python scripts/set_admin_password.py

# Или напрямую
python scripts/set_admin_password.py set <warmaster_id> <password>
```

### 3. Запустите сервер

```bash
# Из корня проекта
cd CareBot
python runserver.py
```

Сервер запустится на `https://192.168.1.100:5000`

### 4. Установите SSL сертификат

При первом заходе браузер покажет предупреждение о самоподписанном сертификате.

**Chrome/Edge:**
1. Нажмите "Advanced" → "Proceed to 192.168.1.100 (unsafe)"
2. Или установите сертификат постоянно (см. `SSL_SETUP.md`)

**Mobile:**
- См. детальные инструкции в `SSL_SETUP.md`

### 5. Войдите в систему

1. Откройте `https://192.168.1.100:5000/login`
2. Выберите своего warmaster из dropdown
3. Введите пароль
4. Нажмите "Войти"

## 🏗️ Архитектура

```
┌─────────────────┐
│  Telegram Bot   │ Устанавливает is_admin=1
│  /make_admin    │ в таблице warmasters
└────────┬────────┘
         │
         ▼
┌─────────────────────────────────────┐
│      warmasters table               │
│  - id (PK)                          │
│  - telegram_id                      │
│  - nickname                         │
│  - is_admin (0 or 1) ◄── Источник  │
│                           истины    │
└────────┬────────────────────────────┘
         │
         │ set_admin_web_password()
         ▼
┌─────────────────────────────────────┐
│     admin_users table               │
│  - warmaster_id (PK, FK)            │
│  - password_hash (bcrypt)           │
│  - created_at                       │
│  - last_login                       │
└────────┬────────────────────────────┘
         │
         │ verify_admin_web_credentials()
         ▼
┌─────────────────────────────────────┐
│       Flask-Login                   │
│    + auth.py module                 │
│                                     │
│  1. Проверяет is_admin=1            │
│  2. Проверяет password_hash         │
│  3. Создает сессию на 1 час         │
└────────┬────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────┐
│      Admin Dashboard                │
│  - Статистика миссий                │
│  - Ввод результатов (в разработке)  │
│  - Создание миссий (в разработке)   │
└─────────────────────────────────────┘
```

## 📁 Ключевые файлы

| Файл | Назначение |
|------|-----------|
| `CareBot/auth.py` | Flask-Login integration, AdminUser class |
| `CareBot/sqllite_helper.py` | 7 функций для веб-аутентификации |
| `CareBot/server_app.py` | Flask routes, session config |
| `CareBot/database/admin_users.sql` | Таблица веб-паролей |
| `scripts/set_admin_password.py` | Утилита управления паролями |
| `templates/login.html` | Форма входа |
| `templates/admin_dashboard.html` | Главная панель |
| `templates/layout.html` | Базовый шаблон |

## 🔐 Функции аутентификации

### sqllite_helper.py

```python
# Установка/обновление пароля
await set_admin_web_password(telegram_id: int, password: str) -> bool

# Проверка логина
await verify_admin_web_credentials(telegram_id: int, password: str) -> bool

# Проверка наличия пароля
await has_admin_web_password(telegram_id: int) -> bool

# Список админов с индикатором веб-доступа
await get_all_admins_with_web_access() -> List[Tuple]
# Returns: [(warmaster_id, nickname, alliance, is_admin, has_web_password), ...]

# Обновить last_login
await update_admin_last_login(telegram_id: int) -> bool

# Информация о веб-доступе
await get_admin_web_info(telegram_id: int) -> Optional[Tuple]
```

### auth.py

```python
# Синхронная обертка для установки пароля
def set_admin_password(warmaster_id: int, password: str) -> bool

# Flask-Login user loader
@login_manager.user_loader
def load_user(user_id: str) -> Optional[AdminUser]

# Internal async verification
async def _verify_login_async(telegram_id: int, password: str) -> Optional[AdminUser]

# Получить админов для формы логина
async def _get_admins_for_login() -> List[Dict]
```

## 🎯 Текущий статус

### ✅ Готово

- [x] SSL/HTTPS настроен
- [x] Таблица admin_users создана
- [x] Flask-Login интегрирован
- [x] Двухслойная аутентификация (is_admin + web password)
- [x] Форма логина с dropdown админов
- [x] Dashboard со статистикой
- [x] Утилита set_admin_password.py
- [x] Документация agents.md обновлена

### 🚧 В разработке

- [ ] Admin Result Entry Page (ввод результата битвы)
- [ ] Admin Mission Generation Page (создание миссии)
- [ ] API endpoints для AJAX
- [ ] PWA Service Worker
- [ ] PWA Manifest
- [ ] Offline caching (IndexedDB)
- [ ] Background sync

### 📋 План

1. **Admin Result Entry** - форма для ввода результата с admin_entered=True
2. **Admin Mission Generation** - создание миссий офлайн
3. **API layer** - REST endpoints для AJAX операций
4. **PWA basics** - Service Worker + Manifest
5. **Offline mode** - IndexedDB + sync mechanism

## 🐛 Troubleshooting

### SSL сертификат не принимается

**Chrome/Edge:**
```
Settings → Privacy and Security → Security → 
Manage certificates → Trusted Root → Import cert.pem
```

**Firefox:**
```
Settings → Privacy & Security → Certificates → 
View Certificates → Authorities → Import cert.pem
```

**Android:**
```
Settings → Security → Install from storage → 
Select cert.pem → Name it "CareBot Local"
```

### Не могу войти

1. **Проверьте is_admin статус:**
   ```bash
   python scripts/set_admin_password.py list
   ```

2. **Проверьте веб-пароль:**
   ```bash
   python scripts/set_admin_password.py set <warmaster_id> <new_password>
   ```

3. **Очистите cookies:**
   - Chrome: Dev Tools (F12) → Application → Cookies → Delete all

### Сессия истекает слишком быстро

По умолчанию сессия живет 1 час. Измените в `server_app.py`:
```python
app.config['PERMANENT_SESSION_LIFETIME'] = 3600  # секунды
```

### Ошибка "Not found: admin_users table"

Выполните миграцию:
```bash
python CareBot/migrate_db.py
```

## 📚 Дополнительная документация

- `agents.md` - Полное руководство для AI агентов
- `SSL_SETUP.md` - Детальная настройка SSL по платформам
- `scripts/README.md` - Описание утилит
- `MISSION_RESULTS_GUIDE.md` - Работа с результатами миссий

## 🔗 Полезные ссылки

- **Dashboard:** https://192.168.1.100:5000/admin/dashboard
- **Login:** https://192.168.1.100:5000/login
- **Logout:** https://192.168.1.100:5000/logout
- **Health check:** https://192.168.1.100:5000/health (если есть)

---

*Последнее обновление: Автоматически через AI agent*
