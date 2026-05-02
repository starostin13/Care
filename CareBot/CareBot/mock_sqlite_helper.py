"""
Mock SQLite helper для тестового режима CareBot.
Эмулирует все функции sqllite_helper.py без обращения к реальной базе данных.

⚠️ ВАЖНО: ЭТОТ ФАЙЛ ПРЕДНАЗНАЧЕН ТОЛЬКО ДЛЯ ТЕСТИРОВАНИЯ!
⚠️ НЕ ДОЛЖЕН ИСПОЛЬЗОВАТЬСЯ В PRODUCTION!
"""

import datetime
import asyncio
import random
import os
from typing import List, Tuple, Optional, Dict, Any
from models import Mission

# Критическая защита от использования в production
if os.getenv('CAREBOT_TEST_MODE', 'false').lower() != 'true':
    raise RuntimeError(
        "🚨 КРИТИЧЕСКАЯ ОШИБКА: mock_sqlite_helper.py НЕ ДОЛЖЕН использоваться в production! "
        "Установите CAREBOT_TEST_MODE=true для тестового режима или используйте sqllite_helper.py"
    )

# Mock данные для тестирования
MOCK_WARMASTERS = {
    1: {
        'id': 1,
        'telegram_id': '325313837',
        'alliance': 1,
        'nickname': 'TestUser1',
        'registered_as': '+79111111111',
        'faction': 'Империум',
        'language': 'ru',
        'notifications_enabled': 1,
        'is_admin': 1
    },
    2: {
        'id': 2,
        'telegram_id': '123456789',
        'alliance': 2,
        'nickname': 'TestUser2',
        'registered_as': '+79222222222',
        'faction': 'Хаос',
        'language': 'ru',
        'notifications_enabled': 1,
        'is_admin': 0
    }
}

MOCK_MISSIONS = {}
MOCK_BATTLES = {}
MOCK_SCHEDULES = {}
MOCK_ALLIANCES = {
    1: {'id': 1, 'name': 'Crimson Legion', 'color': 'red', 'common_resource': 0},
    2: {'id': 2, 'name': 'Shadow Pact', 'color': 'black', 'common_resource': 0},
    3: {'id': 3, 'name': 'Iron Brotherhood', 'color': 'gray', 'common_resource': 0},
    4: {'id': 4, 'name': 'Storm Guard', 'color': 'blue', 'common_resource': 0},
    5: {'id': 5, 'name': 'Void Seekers', 'color': 'purple', 'common_resource': 0}
}

print("🧪 Mock SQLite Helper loaded for TEST MODE")

# Battle functions
async def add_battle_participant(battle_id, participant):
    print(f"🧪 Mock: add_battle_participant({battle_id}, {participant})")
    return True

async def add_battle(mission_id):
    print(f"🧪 Mock: add_battle({mission_id})")
    battle_id = random.randint(1000, 9999)
    MOCK_BATTLES[battle_id] = {'id': battle_id, 'mission_id': mission_id}
    return (battle_id,)

async def get_mission_id_for_battle(battle_id):
    print(f"🧪 Mock: get_mission_id_for_battle({battle_id})")
    if battle_id in MOCK_BATTLES:
        return MOCK_BATTLES[battle_id]['mission_id']
    return None

# Map story functions
async def add_to_story(cell_id, text):
    print(f"🧪 Mock: add_to_story({cell_id}, {text[:50]}...)")
    return True

async def get_cell_history(cell_id):
    print(f"🧪 Mock: get_cell_history({cell_id})")
    return [("Mock история для гекса",), ("Тестовые данные",)]

async def set_cell_patron(cell_id, winner_alliance_id):
    print(f"🧪 Mock: set_cell_patron({cell_id}, {winner_alliance_id})")
    return True

# Alliance functions
async def get_alliance_by_id(alliance_id):
    print(f"🧪 Mock: get_alliance_by_id({alliance_id})")
    alliance = MOCK_ALLIANCES.get(alliance_id)
    if not alliance:
        return None
    return (alliance['id'], alliance['name'], alliance.get('common_resource', 0))

async def get_all_alliances():
    print("🧪 Mock: get_all_alliances()")
    # Возвращаем (id, name) как ожидает keyboard_constructor
    return [(alliance['id'], alliance['name']) for alliance in MOCK_ALLIANCES.values()]


async def get_all_alliances_with_resources():
    print("🧪 Mock: get_all_alliances_with_resources()")
    return [
        (alliance['id'], alliance['name'], alliance.get('common_resource', 0))
        for alliance in MOCK_ALLIANCES.values()
    ]


async def create_alliance(name, initial_resources=0):
    """Create a new alliance (mock version)."""
    print(f"🧪 Mock: create_alliance({name}, {initial_resources})")
    import html
    import re
    
    # Validate name
    if not name or not isinstance(name, str):
        raise ValueError("Alliance name must be a non-empty string")
    
    # Escape HTML and limit length
    name = html.escape(name.strip())
    if len(name) > 50:
        raise ValueError("Alliance name must be 50 characters or less")
    
    # Check for valid characters
    if not re.match(r'^[a-zA-Zа-яА-Я0-9\s\-_\.\!\?]+$', name):
        raise ValueError("Alliance name contains invalid characters")
    
    # Check if name already exists
    for alliance in MOCK_ALLIANCES.values():
        if alliance['name'] == name:
            return None  # Name already exists
    
    # Create alliance
    new_id = max(MOCK_ALLIANCES.keys()) + 1
    MOCK_ALLIANCES[new_id] = {
        'id': new_id,
        'name': name,
        'color': random.choice(['red', 'black', 'gray', 'blue', 'purple']),
        'common_resource': initial_resources
    }
    
    return new_id


async def get_alliance_by_name(name):
    """Get alliance by name (mock version)."""
    print(f"🧪 Mock: get_alliance_by_name({name})")
    for alliance in MOCK_ALLIANCES.values():
        if alliance['name'] == name:
            return (alliance['id'], alliance['name'], alliance['common_resource'])
    return None


async def update_alliance_name(alliance_id, new_name):
    """Update alliance name (mock version)."""
    print(f"🧪 Mock: update_alliance_name({alliance_id}, {new_name})")
    import html
    import re
    
    # Validate name
    if not new_name or not isinstance(new_name, str):
        raise ValueError("Alliance name must be a non-empty string")
    
    # Escape HTML and limit length
    new_name = html.escape(new_name.strip())
    if len(new_name) > 50:
        raise ValueError("Alliance name must be 50 characters or less")
    
    # Check for valid characters
    if not re.match(r'^[a-zA-Zа-яА-Я0-9\s\-_\.\!\?]+$', new_name):
        raise ValueError("Alliance name contains invalid characters")
    
    # Check if new name already exists (excluding current alliance)
    for aid, alliance in MOCK_ALLIANCES.items():
        if aid != alliance_id and alliance['name'] == new_name:
            return False  # Name already exists
    
    # Check if alliance exists
    if alliance_id not in MOCK_ALLIANCES:
        return False  # Alliance not found
    
    # Update name
    MOCK_ALLIANCES[alliance_id]['name'] = new_name
    return True


async def redistribute_players_from_alliance(alliance_id):
    """Redistribute players from alliance (mock version)."""
    print(f"🧪 Mock: redistribute_players_from_alliance({alliance_id})")
    import random
    
    # Get players from the alliance to delete
    players_to_move = []
    for user in MOCK_WARMASTERS.values():
        if user['alliance'] == alliance_id:
            players_to_move.append(user['telegram_id'])
    
    if not players_to_move:
        return 0
    
    # Get remaining alliances with their player counts
    remaining_alliances = []
    for aid, alliance in MOCK_ALLIANCES.items():
        if aid != alliance_id:
            player_count = len([u for u in MOCK_WARMASTERS.values() if u['alliance'] == aid])
            remaining_alliances.append((aid, player_count))
    
    if not remaining_alliances:
        # No other alliances, set players to no alliance (0)
        for user in MOCK_WARMASTERS.values():
            if user['alliance'] == alliance_id:
                user['alliance'] = 0
        return len(players_to_move)
    
    # Redistribute players one by one to alliances with least players
    remaining_alliances.sort(key=lambda x: (x[1], x[0]))  # Sort by player count, then ID
    
    for player_id in players_to_move:
        # Find alliance with minimum players (random choice if tie)
        min_count = remaining_alliances[0][1]
        min_alliances = [alliance for alliance in remaining_alliances if alliance[1] == min_count]
        target_alliance = random.choice(min_alliances)
        
        # Assign player to target alliance
        for user in MOCK_WARMASTERS.values():
            if user['telegram_id'] == player_id:
                user['alliance'] = target_alliance[0]
                break
        
        # Update counts in our tracking list
        for i, alliance in enumerate(remaining_alliances):
            if alliance[0] == target_alliance[0]:
                remaining_alliances[i] = (alliance[0], alliance[1] + 1)
                break
        
        # Re-sort by player count
        remaining_alliances.sort(key=lambda x: (x[1], x[0]))
    
    return len(players_to_move)


async def redistribute_territories_from_alliance(alliance_id):
    """Redistribute territories from alliance (mock version)."""
    print(f"🧪 Mock: redistribute_territories_from_alliance({alliance_id})")
    # In mock, we don't track territories, so just return 0
    return 0


async def delete_alliance(alliance_id):
    """Delete an alliance and redistribute its players and territories (mock version)."""
    print(f"🧪 Mock: delete_alliance({alliance_id})")
    
    # Check if alliance exists
    if alliance_id not in MOCK_ALLIANCES:
        return {
            'success': False,
            'players_redistributed': 0,
            'territories_redistributed': 0,
            'message': 'Alliance not found'
        }
    
    alliance_name = MOCK_ALLIANCES[alliance_id]['name']
    
    # Check if this is the last alliance
    if len(MOCK_ALLIANCES) <= 1:
        return {
            'success': False,
            'players_redistributed': 0,
            'territories_redistributed': 0,
            'message': 'Cannot delete the last alliance'
        }
    
    # Redistribute territories (mock returns 0)
    territories_moved = await redistribute_territories_from_alliance(alliance_id)
    
    # Redistribute players
    players_moved = await redistribute_players_from_alliance(alliance_id)
    
    # Delete alliance
    del MOCK_ALLIANCES[alliance_id]
    
    return {
        'success': True,
        'players_redistributed': players_moved,
        'territories_redistributed': territories_moved,
        'message': f'Alliance "{alliance_name}" deleted, {players_moved} players and {territories_moved} territories redistributed'
    }


async def check_and_clean_empty_alliances():
    """Check for empty alliances and delete them (mock version)."""
    print(f"🧪 Mock: check_and_clean_empty_alliances()")
    
    # Find alliances with 0 members
    empty_alliances = []
    for alliance_id, alliance_data in MOCK_ALLIANCES.items():
        member_count = sum(1 for w in MOCK_WARMASTERS.values() if w['alliance'] == alliance_id)
        if member_count == 0:
            empty_alliances.append((alliance_id, alliance_data['name']))
    
    results = []
    for alliance_id, alliance_name in empty_alliances:
        result = await delete_alliance(alliance_id)
        results.append({
            'alliance_id': alliance_id,
            'alliance_name': alliance_name,
            'result': result
        })
    
    return results


# User/Warmaster functions
async def get_warmasters_by_alliance(alliance_id):
    print(f"🧪 Mock: get_warmasters_by_alliance({alliance_id})")
    return [w for w in MOCK_WARMASTERS.values() if w['alliance'] == alliance_id]

async def get_user_by_telegram_id(telegram_id):
    print(f"🧪 Mock: get_user_by_telegram_id({telegram_id})")
    for user in MOCK_WARMASTERS.values():
        if user['telegram_id'] == str(telegram_id):
            return user
    return None

async def get_user_by_id(user_id):
    print(f"🧪 Mock: get_user_by_id({user_id})")
    return MOCK_WARMASTERS.get(user_id)

async def save_user(user_data):
    print(f"🧪 Mock: save_user({user_data})")
    user_id = user_data.get('id') or len(MOCK_WARMASTERS) + 1
    MOCK_WARMASTERS[user_id] = {**user_data, 'id': user_id}
    return True

async def update_user_language(telegram_id, language):
    print(f"🧪 Mock: update_user_language({telegram_id}, {language})")
    for user in MOCK_WARMASTERS.values():
        if user['telegram_id'] == str(telegram_id):
            user['language'] = language
            return True
    return False

async def update_user_notifications(telegram_id, enabled):
    print(f"🧪 Mock: update_user_notifications({telegram_id}, {enabled})")
    for user in MOCK_WARMASTERS.values():
        if user['telegram_id'] == str(telegram_id):
            user['notifications_enabled'] = enabled
            return True
    return False

async def update_user_nickname(telegram_id, nickname):
    print(f"🧪 Mock: update_user_nickname({telegram_id}, {nickname})")
    for user in MOCK_WARMASTERS.values():
        if user['telegram_id'] == str(telegram_id):
            user['nickname'] = nickname
            return True
    return False

# Mission functions  
async def unlock_expired_missions():
    """Mock: Unlock all missions with past dates that are still locked."""
    print(f"🧪 Mock: unlock_expired_missions()")
    # В mock-режиме просто возвращаем 0 разблокированных миссий
    return 0

async def save_mission(mission_data):
    print(f"🧪 Mock: save_mission({mission_data})")
    mission_id = len(MOCK_MISSIONS) + 1
    today = datetime.date.today().isoformat()
    MOCK_MISSIONS[mission_id] = {
        **mission_data, 
        'id': mission_id,
        'created_date': today,
        'status': 0
    }
    return mission_id

async def get_mission_by_id(mission_id):
    print(f"🧪 Mock: get_mission_by_id({mission_id})")
    return MOCK_MISSIONS.get(mission_id, {
        'id': mission_id,
        'name': 'Mock Mission',
        'rules': 'wh40k',
        'description': 'Тестовая миссия для отладки'
    })

async def get_winner_bonus(mission_id):
    print(f"🧪 Mock: get_winner_bonus({mission_id})")
    return "Секретный бонус победителя (тестовый)"

# Schedule functions
async def save_schedule(schedule_data):
    print(f"🧪 Mock: save_schedule({schedule_data})")
    schedule_id = len(MOCK_SCHEDULES) + 1
    MOCK_SCHEDULES[schedule_id] = {**schedule_data, 'id': schedule_id}
    return schedule_id

async def get_schedule_by_mission_id(mission_id):
    print(f"🧪 Mock: get_schedule_by_mission_id({mission_id})")
    return {
        'id': 1,
        'mission_id': mission_id,
        'datetime': '2025-11-16 15:00:00',
        'participants': '1,2'
    }

async def update_schedule_participants(mission_id, participants):
    print(f"🧪 Mock: update_schedule_participants({mission_id}, {participants})")
    return True

async def get_users_by_ids(user_ids):
    print(f"🧪 Mock: get_users_by_ids({user_ids})")
    return [MOCK_WARMASTERS.get(uid) for uid in user_ids if uid in MOCK_WARMASTERS]

# Notification functions
async def get_users_with_notifications():
    print("🧪 Mock: get_users_with_notifications()")
    return [u for u in MOCK_WARMASTERS.values() if u['notifications_enabled'] == 1]

# Map functions
async def get_hex_by_id(hex_id):
    print(f"🧪 Mock: get_hex_by_id({hex_id})")
    return {
        'id': hex_id,
        'planet_id': 1,
        'state': 'Лес',
        'patron': random.randint(1, 5),
        'has_warehouse': random.choice([0, 1])
    }

async def get_hexes_by_patron(alliance_id):
    print(f"🧪 Mock: get_hexes_by_patron({alliance_id})")
    # Возвращаем несколько тестовых гексов
    return [
        {'id': i, 'state': f'Тест-{i}', 'patron': alliance_id, 'has_warehouse': i % 2}
        for i in range(1, 4)
    ]

# Admin functions
async def is_user_admin(telegram_id):
    print(f"🧪 Mock: is_user_admin({telegram_id})")
    user = await get_user_by_telegram_id(telegram_id)
    return user and user.get('is_admin') == 1

# Локализация
async def get_localized_text(key, language='ru'):
    print(f"🧪 Mock: get_localized_text({key}, {language})")
    
    mock_texts = {
        'welcome_message': 'Добро пожаловать в тестовый режим CareBot!',
        'main_menu': 'Главное меню (тест)',
        'settings_menu': 'Настройки (тест)',
        'game_notification': 'Игровое уведомление (тест)',
        'missions_title': 'Миссии (тест)',
        'language_updated': 'Язык обновлен (тест)',
        'name_updated': 'Имя обновлено (тест)',
        'notifications_enabled': 'Уведомления включены (тест)',
        'notifications_disabled': 'Уведомления отключены (тест)',
        'back_to_main': 'Назад в главное меню (тест)',
        'enter_name': 'Введите ваше имя (тест):',
        'invalid_name': 'Неверное имя (тест)',
        'admin_menu': 'Админ меню (тест)',
        'access_denied': 'Доступ запрещен (тест)',
        'button_alliance_resources': 'Информация об альянсе (тест)',
        'alliance_resources_message': 'Ресурсы альянса {alliance_name}: {resources}',
        'alliance_info_message': '📊 Информация об альянсе {alliance_name}\n\n💎 Ресурсы: {resources}\n👥 Игроков: {player_count}\n🗺️ Территорий: {territory_count}',
        'alliance_no_alliance': 'У вас пока нет альянса (тест)',
        'button_admin_adjust_resources': 'Ресурсы альянсов (тест)',
        'admin_adjust_resources_title': 'Выберите альянс для изменения ресурсов (тест)',
        'admin_adjust_resource_prompt': 'Введите изменение ресурсов для {alliance_name} (текущее: {current})',
        'admin_adjust_resource_success': 'Ресурсы изменены на {delta}, теперь {new_value}',
        'admin_adjust_resource_invalid': 'Введите целое число',
        'button_admin_stats': 'Статистика (тест)',
        'button_admin_stats_users': 'Список пользователей (тест)',
        'button_admin_stats_alliances': 'Список альянсов (тест)',
        'admin_stats_title': 'Статистика (тест)',
        'admin_stats_users_title': 'Игроки за месяц (тест)',
        'admin_stats_alliances_title': 'Альянсы за месяц (тест)',
        'admin_stats_alliance_users_title': 'Игроки альянса {alliance_name} (тест)',
        'admin_stats_no_data': 'Нет данных за последний месяц (тест)',
        'admin_stats_games_label': 'игр'
    }
    
    return mock_texts.get(key, f'[ТЕСТ] {key}')

async def add_localized_text(key, language, text):
    print(f"🧪 Mock: add_localized_text({key}, {language}, {text})")
    return True

# Battle и Winner bonus functions (добавляем недостающие)
async def apply_mission_rewards(mission_id, winner_alliance_id, participants):
    print(f"🧪 Mock: apply_mission_rewards({mission_id}, {winner_alliance_id}, {participants})")
    return {"resources_updated": True, "bonus_applied": "Тестовый бонус"}

async def get_battle_by_mission_id(mission_id):
    print(f"🧪 Mock: get_battle_by_mission_id({mission_id})")
    return {'id': mission_id, 'mission_id': mission_id, 'status': 'active'}

# Warehouse functions
async def get_warehouses_by_alliance(alliance_id):
    print(f"🧪 Mock: get_warehouses_by_alliance({alliance_id})")
    return [
        {'hex_id': 1, 'alliance_id': alliance_id, 'resources': 5},
        {'hex_id': 2, 'alliance_id': alliance_id, 'resources': 3}
    ]

# Resource functions  
async def update_alliance_resources(alliance_id, change):
    print(f"🧪 Mock: update_alliance_resources({alliance_id}, {change})")
    return True

async def get_alliance_resources(alliance_id):
    print(f"🧪 Mock: get_alliance_resources({alliance_id})")
    alliance = MOCK_ALLIANCES.get(alliance_id)
    return alliance.get('common_resource', 0) if alliance else 0

# Complete function implementations for all sqllite_helper functions
async def add_warmaster(telegram_id):
    print(f"🧪 Mock: add_warmaster({telegram_id})")
    return True

async def destroy_warehouse(cell_id):
    print(f"🧪 Mock: destroy_warehouse({cell_id})")
    return True

async def get_event_participants(eventId):
    """
    Mock реализация для получения участников события.
    Возвращает список кортежей формата: [(user_telegram,), (user_telegram,)]
    """
    print(f"🧪 Mock: get_event_participants({eventId})")
    # Возвращаем двух тестовых пользователей как кортежи (как SQL fetchall())
    return [('325313837',), ('123456789',)]

async def get_user_telegram_by_schedule_id(schedule_id):
    """
    Mock реализация для получения user_telegram по schedule_id.
    
    Args:
        schedule_id: The ID of the schedule entry
        
    Returns:
        str: The user_telegram ID from the schedule entry
    """
    print(f"🧪 Mock: get_user_telegram_by_schedule_id({schedule_id})")
    # Возвращаем telegram_id второго тестового пользователя как оппонента
    return '123456789'

async def get_telegram_id_by_warmaster_id(warmaster_id):
    """
    Mock реализация для получения telegram_id по warmaster.id.
    
    Args:
        warmaster_id: The internal ID of the warmaster (warmasters.id)
        
    Returns:
        str: The telegram_id of the warmaster, or None if not found
    """
    print(f"🧪 Mock: get_telegram_id_by_warmaster_id({warmaster_id})")
    user = await get_user_by_id(warmaster_id)
    return user.get('telegram_id') if user else None

async def get_faction_of_warmaster(user_telegram_id):
    print(f"🧪 Mock: get_faction_of_warmaster({user_telegram_id})")
    user = await get_user_by_telegram_id(user_telegram_id)
    return user.get('faction', 'Империум') if user else 'Империум'

async def get_mission(rules):
    """
    Mock реализация для получения миссии по правилам.
    Возвращает Mission объект совместимо с реальной структурой.
    """
    print(f"🧪 Mock: get_mission({rules})")
    
    # Разблокируем просроченные миссии перед получением
    await unlock_expired_missions()
    
    # Генерируем тестовые данные
    mission_id = random.randint(1, 100)
    cell_id = random.randint(1, 50)
    today = datetime.date.today().isoformat()
    
    # For battlefleet, include map description
    map_description = None
    if rules == "battlefleet":
        map_description = "🗺️ BATTLEFLEET MAP - TEST\n\nCelestial Phenomena:\n  • Test Area: Mock Phenomenon"
    
    # Create Mission object
    return Mission(
        id=mission_id,
        deploy=f"Mock {rules} Deploy",
        rules=rules,
        cell=cell_id,
        mission_description=f"Тестовая миссия для {rules}",
        winner_bonus=None,
        status=0,
        created_date=today,
        map_description=map_description,
        reward_config=None
    )

async def get_schedule_by_user(user_telegram, date=None):
    print(f"🧪 Mock: get_schedule_by_user({user_telegram}, {date})")
    return []

async def get_schedule_with_warmasters(user_telegram, date=None):
    """
    Mock реализация для получения расписания миссий на сегодня.
    Возвращает список записей формата: (schedule_id, rules, nickname, warmaster_id)
    Генерирует миссии для всех игровых режимов с одним противником.
    Исключает союзников по альянсу.
    Uses warmaster.id instead of telegram_id for security.
    """
    print(f"🧪 Mock: get_schedule_with_warmasters({user_telegram}, {date})")
    
    # Получаем текущего пользователя
    current_user = await get_user_by_telegram_id(user_telegram)
    if not current_user:
        return []
    
    # Получаем альянс текущего пользователя
    current_user_alliance = current_user.get('alliance')
    
    # Находим другого пользователя для противостояния (не союзника)
    opponent = None
    for user in MOCK_WARMASTERS.values():
        if user['telegram_id'] != str(user_telegram):
            # Исключаем союзников по альянсу
            user_alliance = user.get('alliance')
            # Показываем только если:
            # - У противника нет альянса (None или 0)
            # - У текущего пользователя нет альянса (None или 0)
            # - Альянсы разные
            if (not user_alliance or user_alliance == 0 or
                not current_user_alliance or current_user_alliance == 0 or
                user_alliance != current_user_alliance):
                opponent = user
                break
    
    if not opponent:
        print("🧪 Mock: Нет доступных противников для расписания (исключены союзники)")
        return []
    
    # Генерируем расписание для всех игровых режимов
    game_rules = ["killteam", "wh40k", "combat_patrol", "boarding_action", "battlefleet"]
    
    schedule_entries = []
    for i, rules in enumerate(game_rules, start=1):
        schedule_id = 1000 + i  # Уникальный ID для расписания
        schedule_entries.append((
            schedule_id,
            rules, 
            opponent['nickname'],
            opponent['id']  # Используем warmaster.id вместо telegram_id для безопасности
        ))
    
    print(f"🧪 Mock: Сгенерировано {len(schedule_entries)} записей расписания")
    return schedule_entries


async def get_user_bookings_for_dates(user_telegram, dates):
    """
    Mock реализация для получения бронирований пользователя на указанные даты.
    
    Args:
        user_telegram: User's telegram ID
        dates: List of date strings in format YYYY-MM-DD
        
    Returns:
        Dictionary mapping date to rule name for dates where user has bookings
    """
    print(f"🧪 Mock: get_user_bookings_for_dates({user_telegram}, {dates})")
    
    # В mock режиме возвращаем пустой словарь (нет бронирований)
    # В реальных тестах можно добавить mock данные
    return {}


async def get_settings(telegram_user_id):
    print(f"🧪 Mock: get_settings({telegram_user_id})")
    user = await get_user_by_telegram_id(telegram_user_id)
    if user:
        # Return tuple matching real function: (nickname, registered_as, language, notifications_enabled)
        return (
            user.get('nickname'),
            user.get('registered_as'),
            user.get('language', 'ru'),
            user.get('notifications_enabled', 1)
        )
    return None

async def get_warehouses_of_warmaster(telegram_user_id):
    print(f"🧪 Mock: get_warehouses_of_warmaster({telegram_user_id})")
    return [{'hex_id': 1, 'resources': 3}, {'hex_id': 5, 'resources': 2}]

async def get_players_for_game(rule, date):
    print(f"🧪 Mock: get_players_for_game({rule}, {date})")
    return list(MOCK_WARMASTERS.values())

async def get_weekly_rule_participant_count(rule: str, week_number: int) -> int:
    """Mock implementation for getting weekly participant count"""
    print(f"🧪 Mock: get_weekly_rule_participant_count({rule}, {week_number})")
    # Return random count between 0-8 for testing
    return random.randint(0, 8)

async def get_daily_rule_participant_count(rule: str, date: str) -> int:
    """Mock implementation for getting daily participant count"""
    print(f"🧪 Mock: get_daily_rule_participant_count({rule}, {date})")
    # Return random count between 0-6 for testing
    return random.randint(0, 6)

async def get_weekly_rule_participant_counts(rules: List[str], week_number: int) -> Dict[str, int]:
    """Mock implementation for getting weekly participant counts for multiple rules.
    Only counts dates that are today or in the future."""
    print(f"🧪 Mock: get_weekly_rule_participant_counts({rules}, {week_number})")
    if not rules:
        raise ValueError("Rules list cannot be empty")
    # Return random counts for all rules
    return {rule: random.randint(0, 8) for rule in rules}

async def get_warmasters_opponents(against_alliance, rule, date):
    print(f"🧪 Mock: get_warmasters_opponents({against_alliance}, {rule}, {date})")
    # Приводим кортеж (id,) к числу, чтобы совпадало с prod-логикой
    alliance_id = against_alliance[0] if isinstance(against_alliance, (list, tuple)) else against_alliance
    # Возвращаем как в реальной БД: список кортежей (nickname, registered_as)
    return [
        (w.get('nickname'), w.get('registered_as'))
        for w in MOCK_WARMASTERS.values()
        if w.get('alliance') != alliance_id
    ]

async def get_other_rule_opponents(against_alliance, rule, date):
    print(f"🧪 Mock: get_other_rule_opponents({against_alliance}, {rule}, {date})")
    alliance_id = against_alliance[0] if isinstance(against_alliance, (list, tuple)) else against_alliance
    date_key = str(datetime.datetime.strptime(str(date), "%c").date())
    opponents = []
    for record in MOCK_SCHEDULES.get(date_key, []):
        user = await get_user_by_telegram_id(record.get('user_telegram'))
        if not user:
            continue
        if user.get('alliance') == alliance_id:
            continue
        if record.get('rules') == rule:
            continue
        opponents.append((user.get('nickname'), user.get('registered_as'), record.get('rules')))
    return opponents

async def get_alliance_of_warmaster(telegram_user_id):
    """
    Mock реализация для получения альянса игрока.
    Возвращает кортеж формата: (alliance_id,)
    """
    print(f"🧪 Mock: get_alliance_of_warmaster({telegram_user_id})")
    user = await get_user_by_telegram_id(telegram_user_id)
    alliance_id = user.get('alliance') if user else 1
    return (alliance_id,)  # Возвращаем как кортеж для совместимости с SQL fetchone()

async def insert_to_schedule(date, rules, user_telegram):
    print(f"🧪 Mock: insert_to_schedule({date}, {rules}, {user_telegram})")
    date_key = str(getattr(date, "date", lambda: date)())
    # Сохраняем расписание, чтобы использовать его в тестовых выборках
    MOCK_SCHEDULES.setdefault(date_key, []).append({
        'date': date_key,
        'rules': rules,
        'user_telegram': str(user_telegram)
    })
    return True

async def has_route_to_warehouse(start_id, patron):
    print(f"🧪 Mock: has_route_to_warehouse({start_id}, {patron})")
    return True

async def is_warmaster_registered(user_telegram_id):
    print(f"🧪 Mock: is_warmaster_registered({user_telegram_id})")
    user = await get_user_by_telegram_id(user_telegram_id)
    return user is not None

async def is_hex_patroned_by(cell_id, participant_telegram):
    print(f"🧪 Mock: is_hex_patroned_by({cell_id}, {participant_telegram})")
    return random.choice([True, False])

async def lock_mission(mission_id):
    print(f"🧪 Mock: lock_mission({mission_id})")
    return True

async def update_mission_status(mission_id, status):
    print(f"🧪 Mock: update_mission_status({mission_id}, {status})")
    return True

async def set_mission_score_submitted(mission_id):
    """Set mission locked status to 2 when battle score is submitted."""
    print(f"🧪 Mock: set_mission_score_submitted({mission_id})")
    return True

async def register_warmaster(user_telegram_id, phone):
    print(f"🧪 Mock: register_warmaster({user_telegram_id}, {phone})")
    return True

async def set_nickname(user_telegram_id, nickname):
    print(f"🧪 Mock: set_nickname({user_telegram_id}, {nickname})")
    for user in MOCK_WARMASTERS.values():
        if user['telegram_id'] == str(user_telegram_id):
            user['nickname'] = nickname
            return True
    return False

async def set_language(user_telegram_id, language):
    print(f"🧪 Mock: set_language({user_telegram_id}, {language})")
    for user in MOCK_WARMASTERS.values():
        if user['telegram_id'] == str(user_telegram_id):
            user['language'] = language
            return True
    return False

async def toggle_notifications(user_telegram_id):
    print(f"🧪 Mock: toggle_notifications({user_telegram_id})")
    for user in MOCK_WARMASTERS.values():
        if user['telegram_id'] == str(user_telegram_id):
            user['notifications_enabled'] = 1 - user['notifications_enabled']
            return user['notifications_enabled']
    return 1

async def increase_common_resource(alliance_id, amount=1):
    print(f"🧪 Mock: increase_common_resource({alliance_id}, {amount})")
    alliance = MOCK_ALLIANCES.get(alliance_id)
    if not alliance:
        return 0
    alliance['common_resource'] = alliance.get('common_resource', 0) + amount
    return alliance['common_resource']

async def decrease_common_resource(alliance_id, amount=1):
    print(f"🧪 Mock: decrease_common_resource({alliance_id}, {amount})")
    alliance = MOCK_ALLIANCES.get(alliance_id)
    if not alliance:
        return 0
    alliance['common_resource'] = max(0, alliance.get('common_resource', 0) - amount)
    return alliance['common_resource']

async def create_warehouse(cell_id):
    print(f"🧪 Mock: create_warehouse({cell_id})")
    return True

async def has_warehouse_in_hex(cell_id):
    print(f"🧪 Mock: has_warehouse_in_hex({cell_id})")
    return random.choice([True, False])

async def get_hexes_by_alliance(alliance_id):
    print(f"🧪 Mock: get_hexes_by_alliance({alliance_id})")
    return [{'id': i, 'state': f'Test-{i}'} for i in range(1, 4)]

async def get_adjacent_hexes_between_alliances(alliance1_id, alliance2_id):
    print(f"🧪 Mock: get_adjacent_hexes_between_alliances({alliance1_id}, {alliance2_id})")
    # Return mock adjacent hexes belonging to alliance2
    return [(2,), (3,)]

async def get_warehouse_count_by_alliance(alliance_id):
    print(f"🧪 Mock: get_warehouse_count_by_alliance({alliance_id})")
    return random.randint(1, 5)

async def get_mission_id_by_battle_id(battle_id):
    print(f"🧪 Mock: get_mission_id_by_battle_id({battle_id})")
    return battle_id  # Simple mapping for mock

async def get_mission_details(mission_id):
    print(f"🧪 Mock: get_mission_details({mission_id})")
    today = datetime.date.today().isoformat()
    return Mission(
        id=mission_id,
        deploy='Mock Deploy',
        rules='wh40k',
        cell=None,
        mission_description='Test mission details',
        winner_bonus=None,
        status=0,
        created_date=today,
        map_description=None,
        reward_config=None
    )

async def destroy_warehouse_by_alliance(alliance_id):
    print(f"🧪 Mock: destroy_warehouse_by_alliance({alliance_id})")
    return True

async def get_text_by_key(key, language='ru'):
    print(f"🧪 Mock: get_text_by_key({key}, {language})")
    return await get_localized_text(key, language)

async def add_or_update_text(key, language, value):
    print(f"🧪 Mock: add_or_update_text({key}, {language}, {value})")
    return True

async def get_all_texts_for_language(language='ru'):
    print(f"🧪 Mock: get_all_texts_for_language({language})")
    return {
        'welcome_message': 'Добро пожаловать в тестовый режим!',
        'main_menu': 'Главное меню (тест)'
    }

async def make_user_admin(user_telegram_id):
    print(f"🧪 Mock: make_user_admin({user_telegram_id})")
    for user in MOCK_WARMASTERS.values():
        if user['telegram_id'] == str(user_telegram_id):
            user['is_admin'] = 1
            return True
    return False

async def get_warmasters_with_nicknames():
    print("🧪 Mock: get_warmasters_with_nicknames()")
    # Возвращаем только нужные поля: telegram_id, nickname, alliance
    result = []
    for user in MOCK_WARMASTERS.values():
        if user.get('nickname'):  # Только пользователи с никнеймами
            result.append((user['telegram_id'], user['nickname'], user['alliance']))
    return result

async def get_alliance_player_count(alliance_id):
    print(f"🧪 Mock: get_alliance_player_count({alliance_id})")
    count = len([w for w in MOCK_WARMASTERS.values() if w['alliance'] == alliance_id])
    return count

async def get_alliance_territory_count(alliance_id):
    print(f"🧪 Mock: get_alliance_territory_count({alliance_id})")
    # Mock: Return 0 for alliance 0 (no alliance), 1+ for valid alliances
    if alliance_id == 0 or alliance_id is None:
        return 0
    return random.randint(1, 5)  # Mock alliances have some territories

async def get_user_game_counts_last_month(alliance_id: int = None):
    print(f"🧪 Mock: get_user_game_counts_last_month(alliance_id={alliance_id})")
    sample_stats = [
        ('325313837', 'TestUser1', 1, 5),
        ('123456789', 'TestUser2', 2, 3),
        ('987654321', 'NoAlliance', 0, 1)
    ]
    if alliance_id is not None:
        sample_stats = [row for row in sample_stats if row[2] == alliance_id]
    return sample_stats


async def get_alliance_game_counts_last_month():
    print("🧪 Mock: get_alliance_game_counts_last_month()")
    return [
        (aid, alliance['name'], random.randint(1, 5))
        for aid, alliance in MOCK_ALLIANCES.items()
    ]

async def get_dominant_alliance():
    """Mock: Get the alliance with the most territories (cells) on the map."""
    print("🧪 Mock: get_dominant_alliance()")
    # For testing, return alliance 1 as dominant (Crimson Legion)
    return 1

async def set_warmaster_alliance(user_telegram_id, alliance_id):
    print(f"🧪 Mock: set_warmaster_alliance({user_telegram_id}, {alliance_id})")
    for user in MOCK_WARMASTERS.values():
        if user['telegram_id'] == str(user_telegram_id):
            user['alliance'] = alliance_id
            return True
    return False

async def ensure_first_user_is_admin():
    print("🧪 Mock: ensure_first_user_is_admin()")
    # Return the first admin user's ID
    for user in MOCK_WARMASTERS.values():
        if user.get('is_admin') == 1:
            return user['telegram_id']
    # If no admin found, make first user admin
    first_user = list(MOCK_WARMASTERS.values())[0]
    first_user['is_admin'] = 1
    return first_user['telegram_id']

# Additional functions that might be missing
async def get_cell_id_by_battle_id(battle_id):
    print(f"🧪 Mock: get_cell_id_by_battle_id({battle_id})")
    return random.randint(1, 100)

async def get_next_hexes_filtered_by_patron(cell_id, alliance):
    print(f"🧪 Mock: get_next_hexes_filtered_by_patron({cell_id}, {alliance})")
    return [{'id': i, 'state': f'Hex-{i}'} for i in range(cell_id+1, cell_id+4)]

async def get_nicknamane(telegram_id):
    print(f"🧪 Mock: get_nicknamane({telegram_id})")
    user = await get_user_by_telegram_id(telegram_id)
    return user.get('nickname', 'TestUser') if user else 'TestUser'

async def get_number_of_safe_next_cells(cell_id):
    print(f"🧪 Mock: get_number_of_safe_next_cells({cell_id})")
    return random.randint(1, 3)

async def get_opponent_telegram_id(battle_id, current_user_telegram_id):
    print(f"🧪 Mock: get_opponent_telegram_id({battle_id}, {current_user_telegram_id})")
    # Return different test user
    if current_user_telegram_id == '325313837':
        return '123456789'
    return '325313837'

async def get_active_battle_id_for_mission(mission_id, user_telegram_id):
    """Mock реализация для получения активного battle_id по mission_id и пользователю."""
    print(f"🧪 Mock: get_active_battle_id_for_mission({mission_id}, {user_telegram_id})")
    # Для тестов возвращаем фиксированный battle_id
    return mission_id  # Простая эмуляция

async def get_rules_of_mission(number_of_mission):
    print(f"🧪 Mock: get_rules_of_mission({number_of_mission})")
    return 'wh40k'

async def get_state(cell_id):
    """
    Mock реализация для получения состояния гекса.
    Возвращает кортеж с одним элементом: (state,)
    """
    print(f"🧪 Mock: get_state({cell_id})")
    states = ['Лес', 'Поле', 'Город', 'Горы', 'Болото']
    return (random.choice(states),)

async def add_battle_result(mission_id, counts1, counts2):
    print(f"🧪 Mock: add_battle_result({mission_id}, {counts1}, {counts2})")
    return True

print("🧪 Mock SQLite Helper fully initialized")

# ==================== Feature Flags Functions ====================

# In-memory feature flags storage for testing
_feature_flags = {
    'common_resource': {'enabled': False, 'description': 'Alliance resource mechanics'}
}

async def is_feature_enabled(flag_name: str) -> bool:
    """
    Mock: Check if a feature flag is enabled.
    
    Args:
        flag_name: Name of the feature flag to check
        
    Returns:
        True if feature is enabled, False otherwise.
        Returns True by default if flag doesn't exist (fail-safe).
    """
    print(f"🧪 Mock: is_feature_enabled({flag_name})")
    flag = _feature_flags.get(flag_name, {})
    return flag.get('enabled', True)


async def toggle_feature_flag(flag_name: str) -> bool:
    """
    Mock: Toggle a feature flag between enabled and disabled.
    
    Args:
        flag_name: Name of the feature flag to toggle
        
    Returns:
        New state of the flag (True=enabled, False=disabled)
    """
    print(f"🧪 Mock: toggle_feature_flag({flag_name})")
    if flag_name not in _feature_flags:
        _feature_flags[flag_name] = {'enabled': True, 'description': flag_name}
    
    current_state = _feature_flags[flag_name]['enabled']
    new_state = not current_state
    _feature_flags[flag_name]['enabled'] = new_state
    
    return new_state


async def get_all_feature_flags() -> list:
    """
    Mock: Get all feature flags with their current status.
    
    Returns:
        List of tuples: [(flag_name, enabled, description), ...]
    """
    print("🧪 Mock: get_all_feature_flags()")
    return [
        (flag_name, int(flag['enabled']), flag['description'])
        for flag_name, flag in _feature_flags.items()
    ]
