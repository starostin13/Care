# Исправление ошибки: winner_bonus попадает в battles.mission_id

## 🐛 Описание проблемы

В таблицу `battles` в колонку `mission_id` попадали некорректные значения вместо ID миссии:
- Значения `winner_bonus` из таблицы `mission_stack`
- Текстовые описания миссий вместо числовых ID
- Несуществующие ID миссий

## 🔍 Причина проблемы

### Структура данных

**Миссия из БД (`SELECT * FROM mission_stack`):**
```python
(id, deploy, rules, cell, mission_description, winner_bonus, locked, created_date)
# Индексы:
# 0: id (mission_id)
# 1: deploy
# 2: rules
# 3: cell
# 4: mission_description
# 5: winner_bonus
```

**Генерируемая миссия (`generate_new_one()`):**
```python
(deploy, rules, cell, mission_description, winner_bonus)
# Индексы:
# 0: deploy
# 1: rules
# 2: cell
# 3: mission_description
# 4: winner_bonus
```

### Ошибочный код

В [mission_helper.py](CareBot/CareBot/mission_helper.py) (строки 176, 182):

```python
# НЕПРАВИЛЬНО!
await sqllite_helper.update_mission_cell(mission[4], cell_id)  # mission[4] = winner_bonus ❌
await sqllite_helper.lock_mission(mission[4])                  # mission[4] = winner_bonus ❌
```

Код предполагал что `mission[4]` это всегда mission_id, но:
- Для миссии из БД: `mission[4]` = `mission_description` (текст)
- Для сгенерированной миссии: `mission[4]` = `winner_bonus` (текст или None)

В результате в `battles.mission_id` попадали текстовые значения вместо числового ID.

## ✅ Решение

### 1. Исправление кода

**[mission_helper.py](CareBot/CareBot/mission_helper.py) - функция `get_mission()`:**

```python
async def get_mission(rules: Optional[str], attacker_id: Optional[str] = None, defender_id: Optional[str] = None):
    mission = await sqllite_helper.get_mission(rules)
    
    # Определяем формат миссии
    is_from_db = mission is not None
    
    if not mission:
        # Генерируем новую и сразу получаем из БД
        mission = generate_new_one(rules)
        await sqllite_helper.save_mission(mission)
        mission = await sqllite_helper.get_mission(rules)
        is_from_db = True

    # Правильно извлекаем mission_id и cell_id
    if is_from_db:
        # DB format: (id, deploy, rules, cell, ...)
        mission_id = mission[0]  # ✅ Правильно!
        cell_id = mission[3]
    else:
        # Generated format (shouldn't happen anymore)
        mission_id = None
        cell_id = mission[2]
    
    # Теперь используем правильный mission_id
    await sqllite_helper.update_mission_cell(mission_id, cell_id)
    await sqllite_helper.lock_mission(mission_id)
```

**Ключевые изменения:**
1. ✅ Всегда получаем миссию из БД (даже после генерации)
2. ✅ Правильно определяем `mission_id = mission[0]`
3. ✅ Используем `mission_id` вместо `mission[4]`

### 2. Миграция базы данных

**[migrations/019_final_fix_battles_mission_id.py](CareBot/CareBot/migrations/019_final_fix_battles_mission_id.py):**

Миграция выполняет:
1. 🔍 Находит все некорректные записи в `battles`
2. 🧹 Удаляет battles с несуществующими mission_id
3. 🛡️ Создает trigger для предотвращения будущих ошибок

**Trigger:**
```sql
CREATE TRIGGER validate_battle_mission_id
BEFORE UPDATE OF mission_id ON battles
FOR EACH ROW
WHEN NEW.mission_id IS NOT NULL
BEGIN
    SELECT CASE
        WHEN NOT EXISTS (SELECT 1 FROM mission_stack WHERE id = NEW.mission_id)
        THEN RAISE(ABORT, 'Invalid mission_id: must reference existing mission')
    END;
END;
```

## 📋 Деплой исправления

### Шаг 1: Проверка безопасности

```powershell
python scripts\check-production-safety.py
```

### Шаг 2: Сборка образа

```powershell
.\scripts\wsl2-deploy.ps1 build
```

### Шаг 3: Проверка образа

```powershell
.\scripts\wsl2-deploy.ps1 inspect
```

### Шаг 4: Синхронизация миграции

```powershell
.\scripts\wsl2-deploy.ps1 migrations
```

### Шаг 5: Деплой

```powershell
.\scripts\wsl2-deploy.ps1 deploy
```

### Шаг 6: Применение миграции

```powershell
.\scripts\wsl2-deploy.ps1 apply-migrations
```

### Шаг 7: Проверка логов

```powershell
.\scripts\wsl2-deploy.ps1 logs
```

## 🔍 Проверка результата

### Через SQLite Web UI

http://192.168.1.125:8080/

```sql
-- Проверить что все battles имеют валидные mission_id
SELECT b.id, b.mission_id, m.id as mission_exists
FROM battles b
LEFT JOIN mission_stack m ON b.mission_id = m.id
WHERE b.mission_id IS NOT NULL;

-- Должно быть 0 записей с mission_exists = NULL
```

### Через скрипт

```powershell
.\scripts\wsl2-deploy.ps1 migration-status
```

## 📊 Статистика до и после

**До исправления:**
- ❌ Некорректные mission_id (текст, winner_bonus)
- ❌ Несуществующие ID миссий
- ❌ Невозможность получить детали миссии по battle_id

**После исправления:**
- ✅ Все mission_id - числовые ID из mission_stack
- ✅ Trigger предотвращает будущие ошибки
- ✅ Можно получить детали миссии через JOIN

## 🛡️ Предотвращение в будущем

1. **Код:** Исправлен логический баг с индексами tuple
2. **БД:** Trigger валидирует mission_id при UPDATE
3. **Тесты:** Добавить unit-тесты для get_mission()

## 📚 Связанные файлы

- [mission_helper.py](CareBot/CareBot/mission_helper.py) - исправлен основной баг
- [sqllite_helper.py](CareBot/CareBot/sqllite_helper.py) - функции работы с БД
- [migrations/016_fix_battles_mission_id.py](CareBot/CareBot/migrations/016_fix_battles_mission_id.py) - первая попытка исправления
- [migrations/019_final_fix_battles_mission_id.py](CareBot/CareBot/migrations/019_final_fix_battles_mission_id.py) - финальное исправление с trigger

## 🎯 Дата исправления

**31 января 2026**

---

**Статус:** ✅ Исправлено и готово к деплою
