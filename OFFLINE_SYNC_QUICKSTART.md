# Offline Sync Quick Start Guide

## 📦 Что было создано

Полная система офлайн синхронизации для CareBot мобильного приложения с поддержкой:

- ✅ Офлайн кеширования миссий и карты
- ✅ Офлайн сохранения боевых результатов
- ✅ Синхронизации при возврате онлайн
- ✅ Расчета эффектов территорий на сервере
- ✅ UI панели для управления синхронизацией

## 🚀 Быстрый старт

### 1. Включить сервер (HTTP mode)
```powershell
# На локальной машине или production
cd c:\Users\staro\Projects\Care
.\scripts\update-production.ps1 update
```

### 2. Открыть админ-панель в браузере
```
http://192.168.1.125:5555/admin/dashboard
```

### 3. Использовать поле синхронизации
На админ-панели появилась новая секция **"Синхронизация Офлайн Данных"** с тремя панелями:

#### 📦 Локальный Кеш
- **Кнопка "Обновить Кеш"** - Загружает текущие миссии и карту в браузер/мобильное приложение
- **Кнопка "Очистить"** - Удаляет весь локальный кеш

#### 🔄 Статус Синхронизации
- Показывает количество ожидающихся миссий
- Показывает завершённые миссии
- **Кнопка "Синхронизировать"** - Отправляет ожидающиеся результаты на сервер

#### ⚔️ Ожидающиеся Результаты
- Показывает количество ожидающихся боевых результатов
- **Кнопка "Просмотреть"** - Открывает модальное окно со списком ожидающихся результатов

### 4. На мобильном приложении
```kotlin
// Автоматически при запуске:
1. App подключается к http://192.168.1.125:5555/admin/dashboard
2. JavaScript вызывает CareBotSync.init()
3. Загружает кеш в локальное SQLite хранилище
4. Сохраняет результаты боев при офлайн режиме
5. Синхронизирует при возврате онлайн
```

## API Примеры

### Загрузить данные для кеша
```bash
curl http://192.168.1.125:5555/api/mobile/data-export
```

**Ответ:**
```json
{
    "status": "ok",
    "missions": {
        "missions": [
            {
                "id": 1,
                "title": "Loot Mission",
                "mission_type": "Loot",
                "hex_id": "A1B2",
                "participants": ["player1", "player2"],
                "status": "active"
            }
        ]
    },
    "map": {
        "edges": [
            {"from": "A1", "to": "B1"},
            {"from": "A1", "to": "B2"}
        ]
    }
}
```

### Синхронизировать результаты
```bash
curl -X POST http://192.168.1.125:5555/api/mobile/sync-results \
  -H "Content-Type: application/json" \
  -d '{
    "warmaster_id": 123,
    "results": [
        {
            "mission_id": 1,
            "winner_id": 10,
            "loser_id": 20,
            "mission_type": "Secure",
            "location": "A1B2",
            "timestamp": "2025-01-15T10:30:00Z"
        }
    ]
}'
```

**Ответ:**
```json
{
    "status": "ok",
    "processed": 1,
    "territories_affected": {
        "claimed": 1,
        "depots_created": 0,
        "depots_destroyed": 0
    }
}
```

### Проверить статус
```bash
curl http://192.168.1.125:5555/api/mobile/sync-status
```

**Ответ:**
```json
{
    "status": "ok",
    "pending_missions": 3,
    "completed_missions": 12,
    "last_sync_time": "2025-01-15T09:45:00Z"
}
```

## 📱 Android WebView Integration

### JavaScript API (в браузере)
```javascript
// Загрузить в кеш
await CareBotSync.downloadAndCache();

// Получить закешированные миссии
const missions = await CareBotSync.getCachedMissions();

// Сохранить боевой результат
await CareBotSync.saveBattleResult(
    missionId: 1,
    winnerId: 10,
    loserId: 20,
    missionType: "Secure",
    location: "A1B2"
);

// Синхронизировать все результаты
await CareBotSync.syncPendingChanges();

// Получить актуальный статус
const status = await CareBotSync.getSyncStatus();

// Очистить весь кеш
await CareBotSync.clearAllCache();
```

### Kotlin Native API (в приложении)
```kotlin
// Получить объект bridge
val bridge = AndroidBridge(context)

// Сохранить миссии
val missionsJson = """{"missions": [...]}"""
bridge.cacheMissions(missionsJson)

// Получить миссии
val result = bridge.getCachedMissions()
val missions = JSONObject(result).optJSONArray("missions")

// Сохранить боевой результат
val battleJson = """{"mission_id": 1, "winner_id": 10, ...}"""
bridge.savePendingBattleResult(battleJson)

// Получить ожидающиеся
val pending = bridge.getPendingBattles()

// Отметить как синхронизированные
val ids = listOf(1, 2, 3)
bridge.markBattlesAsSynced(JSONArray(ids).toString())

// Очистить кеш
bridge.clearAllCache()
```

## 🧪 Тестирование локально

### 1. Запустить тестовый режим
```powershell
.\scripts\test-mode.ps1 start
```

### 2. В консоли браузера протестировать (F12)
```javascript
// Проверить наличие bridge
console.log(window.Android); // Undefined в браузере, доступен в WebView

// Используемый для тестов - просто JavaScript:
CareBotSync.downloadAndCache();  // Загрузить в IndexedDB
CareBotSync.getCachedMissions(); // Получить из IndexedDB
CareBotSync.syncPendingChanges(); // Синхронизировать с сервером
```

### 3. Проверить API endpoints с curl
```bash
# Проверить health
curl http://localhost:5555/health

# Загрузить данные для кеша
curl http://localhost:5555/api/mobile/data-export

# Синхронизировать (требует данных)
curl -X POST http://localhost:5555/api/mobile/sync-results \
  -H "Content-Type: application/json" \
  -d '{"warmaster_id": 1, "results": []}'
```

## 🔧 Архитектура файлов

```
CareBot/
├── CareBot/
│   ├── sync_helper.py               ← Backend логика синхронизации
│   ├── server_app.py                ← API endpoints интегрированы
│   ├── sqllite_helper.py            ← Работа с БД
│   └── static/
│       └── js/
│           └── sync.js              ← JavaScript UI логика
├── templates/
│   ├── layout.html                  ← Подключает sync.js
│   ├── admin_dashboard.html         ← Includes sync-panel.html
│   └── components/
│       └── sync-panel.html          ← UI компонент синхронизации
└── android/
    ├── build.gradle
    └── src/main/kotlin/
        └── AndroidBridge.kt         ← SQLite bridge для приложения
```

## 📊 Типы миссий и эффекты

| Тип Миссии | Эффект | Реализация |
|-----------|--------|---------|
| **Secure** | Захват территории | map.controlled_by = winner_alliance |
| **Intel** | Создаёт склад | Добавляет в map_depots |
| **Coordinates** | Уничтожает чужой склад | Удаляет из map_depots |
| **Loot** | Обмен ресурсов | (встроена в game_logic) |
| **Transmission** | Ресурсы победителя | (встроена в game_logic) |

## ⚙️ Configuration

### Environment переменные
```bash
# Путь к базе данных (для server_app.py)
DATABASE_PATH=/app/data/game_database.db

# Порт сервера (для Flask)
SERVER_PORT=5555

# Host сервера (для Flask)
SERVER_HOST=0.0.0.0

# HTTPS (отключено для мобильного)
SSL_CERT_PATH=''
SSL_KEY_PATH=''
```

### В docker-compose.yml
```yaml
services:
  carebot:
    environment:
      - DATABASE_PATH=/app/data/game_database.db
      - SERVER_PORT=5555
      - SERVER_HOST=0.0.0.0
    ports:
      - "5555:5555"
    volumes:
      - ./data:/app/data
      - ./migrations:/app/CareBot/migrations
```

## 🐛 Отладка

### Включить verbose логирование
```python
# В config.py
import logging
logging.basicConfig(level=logging.DEBUG)
```

### Посмотреть логи в браузере
```javascript
// F12 → Console
CareBotSync.refreshUI();           // Обновить UI
console.log('Pending:', await CareBotSync.getCachedMissions());
```

### Посмотреть логи в приложении
```bash
# Логкат с фильтром на приложение
adb logcat | grep -i carebot
```

## 📝 Лучшие практики

1. **Всегда проверяйте online/offline статус** перед операциями
2. **Используйте try/catch** для sync операций
3. **Логируйте все ошибки синхронизации** для отладки
4. **Периодически очищайте старый кеш** чтобы сэкономить место
5. **Тестируйте с плохой сетью** для реальных сценариев

## 🆘 Troubleshooting

### Ошибка: "Android bridge not available"
- ✅ Проверить что приложение запущено в WebView
- ✅ Проверить что AndroidBridge.kt подключена в AndroidManifest.xml
- ✅ Проверить что JavaScript interface включен в WebViewSettings

### Ошибка: "Mission not found"
- ✅ Проверить что миссия существует в БД
- ✅ Проверить что warmaster имеет доступ к миссии
- ✅ Проверить что эта миссия была в импортированном кеше

### Ошибка: "ERR_CONNECTION_RESET"
- ✅ Проверить что сервер HttpOnly (без SSL)
- ✅ Проверить IP адрес и порт
- ✅ Проверить firewall правила

---

**Quick Start Version:** 1.0  
**Created:** 2025-01-15  
**For:** CareBot Offline Sync System  
