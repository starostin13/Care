# Mission Display Fix - Январь 31, 2026

## Проблема
Пользователи жаловались что вместо стартового меню (/start) бот отправляет последнюю миссию.

## Причина
В обработчике состояния `MISSIONS` был **generic** `CallbackQueryHandler(get_the_mission)` **БЕЗ pattern**. Это означал что он перехватывал **ЛЮБОЙ** callback query когда пользователь был в состоянии MISSIONS, включая даже невалидные или остаточные callbacks.

**Проблемный код в handlers.py:**
```python
MISSIONS: [
    CallbackQueryHandler(hello, pattern='^start$'),
    CallbackQueryHandler(get_the_mission)  # ❌ БЕЗ PATTERN!
]
```

Когда пользователь случайно был в состоянии MISSIONS и приходил любой callback (например, какой-то остаточный), функция `get_the_mission` перехватывала его и пытается обработать как миссию расписания.

## Решение

### 1. Добавлено валидирование в `get_the_mission()` (линия 64-81)
- Проверка что callback_data начинается с "mission_sch_"
- Обработка ValueError если парсинг номера миссии не удается
- Отправка ошибки пользователю вместо краша

```python
# Validate callback data - it should start with 'mission_sch_'
if not query.data.startswith("mission_sch_"):
    logger.error(f"Invalid mission callback data: {query.data}")
    await query.edit_message_text("❌ Ошибка: неверный формат запроса...")
    return MISSIONS
```

### 2. Добавлен pattern в handlers.py (линия 1218)
- Изменен `CallbackQueryHandler(get_the_mission)` на `CallbackQueryHandler(get_the_mission, pattern='^mission_sch_')`
- Теперь функция срабатывает ТОЛЬКО для валидных миссий расписания

```python
MISSIONS: [
    CallbackQueryHandler(hello, pattern='^start$'),
    CallbackQueryHandler(back_to_missions, pattern='^back_to_missions$'),  # ✅ НОВЫЙ
    CallbackQueryHandler(get_the_mission, pattern='^mission_sch_')  # ✅ С PATTERN!
]
```

### 3. Добавлена кнопка "Back" в миссии (линия 175-181)
- Пользователь может вернуться к списку миссий из сообщения о миссии
- Кнопка имеет callback_data="back_to_missions"

```python
back_button = [[InlineKeyboardButton("⬅️ Назад к миссиям", callback_data="back_to_missions")]]
back_markup = InlineKeyboardMarkup(back_button)

await query.edit_message_text(..., reply_markup=back_markup)
```

### 4. Добавлена функция `back_to_missions()` (линия 562-576)
- Новый обработчик для кнопки "Back from mission"
- Возвращает пользователя к списку расписаний

## Файлы измененные
- [CareBot/CareBot/handlers.py](CareBot/CareBot/handlers.py)
  - Валидирование в `get_the_mission()` (линии 64-81)
  - Кнопка Back в миссиях (линии 175-181)
  - Новая функция `back_to_missions()` (линии 562-576)
  - Добавлены handlers в конфиг (линия 1218)

## Тестирование
1. `/start` → должен отправить главное меню ✅
2. "Миссии" → показать расписание ✅
3. Нажать на миссию → показать миссию с кнопкой Back ✅
4. Back → вернуться к расписанию ✅
5. /start → вернуться в главное меню ✅

## Deploy
```powershell
.\scripts\update-production.ps1 update
```

## Backward Compatibility
✅ Все изменения backward compatible:
- Новый pattern не нарушает существующие callbacks
- Новая кнопка дополняет UI, не заменяет существующие функции
- Валидирование добавляет надежность без нарушения логики
