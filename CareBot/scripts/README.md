# CareBot Scripts

Утилиты для управления CareBot.

## set_admin_password.py

Управление веб-доступом для администраторов.

### Требования

- У warmaster должен быть `is_admin=1` в таблице `warmasters` (устанавливается через Telegram бота)
- Скрипт только добавляет веб-пароль для входа в admin панель

### Использование

**Интерактивный режим:**
```bash
python scripts/set_admin_password.py
```

**Показать список администраторов:**
```bash
python scripts/set_admin_password.py list
```

**Установить пароль напрямую:**
```bash
python scripts/set_admin_password.py set <warmaster_id> <password>
```

### Примеры

```bash
# Интерактивная установка
python scripts/set_admin_password.py

# Посмотреть кто имеет права админа
python scripts/set_admin_password.py list

# Установить пароль для warmaster_id 123
python scripts/set_admin_password.py set 123 mySecurePassword
```

### Архитектура

- **is_admin** определяется полем `warmasters.is_admin` (управляется через Telegram)
- **admin_users** хранит только `password_hash` для веб-доступа
- Для входа нужны ОБА условия: `is_admin=1` + валидный веб-пароль

### Workflow

1. Назначить админа через Telegram бота: `/make_admin @username`
2. Установить веб-пароль: `python scripts/set_admin_password.py`
3. Войти в веб-панель: `https://server-ip:5000/login`
