# Offline Sync & Caching System для Android CareBot App

## Архитектура

Система разделена на три компоненты:

### 1. Backend (Python Flask)
**Файл:** `sync_helper.py`
**Назначение:** Обработка синхронизации и расчет эффектов миссий

Основные функции:
- `export_missions_for_cache()` - Экспорт данных для кеша
- `export_map_data_for_cache()` - Экспорт карты для офлайн расчетов
- `process_synced_battle_results()` - Обработка офлайн результатов с расчетом территорий
- `get_sync_status()` - Статус синхронизации

**API Endpoints:**
- `GET /api/mobile/data-export` - Получить данные для кеша
- `POST /api/mobile/sync-results` - Синхронизировать боевые результаты
- `GET /api/mobile/sync-status` - Получить статус синхронизации

### 2. Frontend JavaScript
**Файл:** `static/js/sync.js`
**Назначение:** Управление синхронизацией на админ-панели

Основной объект: `CareBotSync`
- `init()` - Инициализация при загрузке страницы
- `downloadAndCache()` - Скачать данные в локальный кеш
- `getCachedMissions()` - Получить закешированные миссии
- `saveBattleResult()` - Сохранить боевой результат офлайн
- `syncPendingChanges()` - Синхронизировать с сервером
- `showSyncNotification()` - Показать уведомление

### 3. Android Native Bridge
**Файл:** `app/src/main/kotlin/com/carebot/adminapp/AndroidBridge.kt`
**Назначение:** JavaScript ↔ Kotlin коммуникация, локальное SQLite хранилище

SQLite таблицы:
- `missions` - Закешированные миссии (id, data, cached_at)
- `battles` - Офлайн боевые результаты (id, mission_id, result_json, synced)
- `pending_syncs` - Метаинформация синхронизации (id, status, count)

JavascriptInterface методы:
- `cacheMissions(json)` - Сохранить миссии в SQLite
- `getCachedMissions()` - Получить миссии из SQLite
- `savePendingBattleResult(json)` - Сохранить боевой результат
- `getPendingBattles()` - Получить неотправленные боевые результаты
- `markBattlesAsSynced(ids)` - Отметить результаты как отправленные
- `clearAllCache()` - Очистить весь кеш

## Workflow синхронизации

### Инициализация
```
1. App запускается
2. JavaScript вызывает CareBotSync.init()
3. Проверяется доступность AndroidBridge
4. Запрашивает /api/mobile/data-export
5. Сохраняет миссии в SQLite через AndroidBridge.cacheMissions()
```

### Офлайн работа
```
1. Пользователь выбирает миссию из кеша
2. Вводит результат боя
3. JavaScript вызывает CareBotSync.saveBattleResult()
4. AndroidBridge.savePendingBattleResult() сохраняет в SQLite
```

### Синхронизация
```
1. Пользователь нажимает "Синхронизировать"
2. JavaScript получает pending результаты через AndroidBridge.getPendingBattles()
3. POST на /api/mobile/sync-results с результатами
4. Backend sync_helper.process_synced_battle_results():
   - Проверяет каждый результат
   - Расчитывает эффекты территорий (Secure, Intel, Coordinates)
   - Обновляет map, map_depots и т.д.
5. JavaScript получает ответ и вызывает AndroidBridge.markBattlesAsSynced()
6. Показывает уведомление пользователю
```

## Эффекты миссий на территории

### Secure Mission (Завладение)
- **Эффект:** Победитель захватывает территорию
- **Изменение:** `map.controlled_by` = `winner_alliance_id`
- **Код:** `_claim_territory(hex_id, winner_alliance_id)`

### Intel Mission (Разведка)
- **Эффект:** Создание склада для победителя
- **Изменение:** `map_depots` добавляется новый склад
- **Код:** `_create_supply_depot(hex_id, winner_alliance_id)`

### Coordinates Mission (Координаты)
- **Эффект:** Уничтожение вражеского склада
- **Изменение:** `map_depots` удаляется вражеский склад
- **Код:** `_destroy_enemy_depot(hex_id, loser_alliance_id)`

## Использование UI компонента

### Включение в админ-панель
Компонент автоматически подключается через `layout.html`:
```html
{% include "components/sync-panel.html" %}
```

Отображает три раздела:
1. **Локальный Кеш** - Статус и управление кешем миссий
2. **Статус Синхронизации** - Информация о ожидающихся результатах
3. **Ожидающиеся Результаты** - Список и синхронизация боев

### JavaScript методы управления UI
```javascript
CareBotSync.updateCacheStatus()      // Обновить статус кеша
CareBotSync.updateSyncStatus()       // Обновить статус синхронизации
CareBotSync.updatePendingStatus()    // Обновить статус ожидающихся
CareBotSync.showPendingBattles()     // Показать модальное окно
CareBotSync.refreshUI()              // Обновить всю UI
```

## Обработка ошибок

### Нет проверки подходит/не подходит
```python
# sync_helper.py
if mission.id not in processed_missions:
    logger.warning(f'Mission {mission.id} not found for result')
    return {'error': 'Mission not found'}
```

### Недостаточно прав на синхронизацию
```python
# Проверяется warmaster_id перед sync
if not is_warmaster_admin(warmaster_id):
    return {'error': 'Insufficient permissions'}
```

### Конфликта данных (миссия изменилась на сервере)
```python
# Проверяется версия данных
if result.mission_version != server_mission.version:
    logger.warning(f'Version mismatch for mission {mission_id}')
```

## Локальные сессии и хранилище

### IndexedDB (для браузера)
```javascript
CareBotSync.storeCachedData('map_edges', edges)   // Сохранить в IndexedDB
CareBotSync.getCachedData('map_edges')            // Получить из IndexedDB
```

### SQLite (для Android приложения)
```kotlin
// Автоматически управляется через AndroidBridge
val db = AdminDBHelper(context)
db.cacheMissions(missions)                        // Сохранить в SQLite
val cached = db.getCachedMissions()               // Получить из SQLite
```

## Тестирование

### Локальное тестирование
```bash
# Скачать данные в кеш
curl http://192.168.1.125:5555/api/mobile/data-export

# Синхронизировать результаты (параметры см. в sync_helper.py)
curl -X POST http://192.168.1.125:5555/api/mobile/sync-results \
  -H "Content-Type: application/json" \
  -d '{"warmaster_id": 1, "results": [...]}'

# Проверить статус
curl http://192.168.1.125:5555/api/mobile/sync-status
```

### Отладка JavaScript
```javascript
// В консоли браузера
CareBotSync.downloadAndCache()         // Загрузить кеш
CareBotSync.getCachedMissions()        // Просмотреть миссии
CareBotSync.syncPendingChanges()       // Отправить результаты
CareBotSync.clearAllCache()            // Очистить кеш
```

## Безопасность

- ✅ Синхронизация требует `warmaster_id` и проверки прав
- ✅ Версионирование данных предотвращает конфликты
- ✅ Параметризованные SQL запросы защищают от инъекций
- ✅ Логирование всех операций синхронизации
- ✅ Асинхронные операции предотвращают блокировку БД

## Производительность

- 🚀 Офлайн кеширование устраняет сетевые задержки
- 🚀 Батч синхронизация уменьшает количество HTTP запросов
- 🚀 SQLite индексы ускоряют поиск миссий
- 🚀 gzip сжатие уменьшает размер данных

## Будущие улучшения

- [ ] Conflict resolution при одновременных изменениях
- [ ] Differential sync (синхронизация только изменений)
- [ ] Incremental backup
- [ ] Peer-to-peer sync между приложениями
- [ ] Обновление маршрутизации в реальном времени

---

**Последнее обновление:** 2025-01-15
**Версия:** 1.0.0
**Статус:** Production Ready (готово к продакшену)
