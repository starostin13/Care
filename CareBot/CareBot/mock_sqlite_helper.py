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
    1: {'id': 1, 'name': 'Crimson Legion', 'color': 'red'},
    2: {'id': 2, 'name': 'Shadow Pact', 'color': 'black'},
    3: {'id': 3, 'name': 'Iron Brotherhood', 'color': 'gray'},
    4: {'id': 4, 'name': 'Storm Guard', 'color': 'blue'},
    5: {'id': 5, 'name': 'Void Seekers', 'color': 'purple'}
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
    return MOCK_ALLIANCES.get(alliance_id, MOCK_ALLIANCES[1])

async def get_all_alliances():
    print("🧪 Mock: get_all_alliances()")
    return list(MOCK_ALLIANCES.values())

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
async def save_mission(mission_data):
    print(f"🧪 Mock: save_mission({mission_data})")
    mission_id = len(MOCK_MISSIONS) + 1
    MOCK_MISSIONS[mission_id] = {**mission_data, 'id': mission_id}
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
        'access_denied': 'Доступ запрещен (тест)'
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
    return random.randint(5, 20)

# Complete function implementations for all sqllite_helper functions
async def add_warmaster(telegram_id):
    print(f"🧪 Mock: add_warmaster({telegram_id})")
    return True

async def destroy_warehouse(cell_id):
    print(f"🧪 Mock: destroy_warehouse({cell_id})")
    return True

async def get_event_participants(eventId):
    print(f"🧪 Mock: get_event_participants({eventId})")
    return [1, 2]  # Mock participant IDs

async def get_faction_of_warmaster(user_telegram_id):
    print(f"🧪 Mock: get_faction_of_warmaster({user_telegram_id})")
    user = await get_user_by_telegram_id(user_telegram_id)
    return user.get('faction', 'Империум') if user else 'Империум'

async def get_mission(rules):
    print(f"🧪 Mock: get_mission({rules})")
    return {
        'id': random.randint(1, 100),
        'name': f'Mock {rules} Mission',
        'description': f'Test mission for {rules}',
        'rules': rules
    }

async def get_schedule_by_user(user_telegram, date=None):
    print(f"🧪 Mock: get_schedule_by_user({user_telegram}, {date})")
    return []

async def get_schedule_with_warmasters(user_telegram, date=None):
    print(f"🧪 Mock: get_schedule_with_warmasters({user_telegram}, {date})")
    return []

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

async def get_warmasters_opponents(against_alliance, rule, date):
    print(f"🧪 Mock: get_warmasters_opponents({against_alliance}, {rule}, {date})")
    return [w for w in MOCK_WARMASTERS.values() if w['alliance'] != against_alliance]

async def get_alliance_of_warmaster(telegram_user_id):
    print(f"🧪 Mock: get_alliance_of_warmaster({telegram_user_id})")
    user = await get_user_by_telegram_id(telegram_user_id)
    return user.get('alliance') if user else 1

async def insert_to_schedule(date, rules, user_telegram):
    print(f"🧪 Mock: insert_to_schedule({date}, {rules}, {user_telegram})")
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
    return True

async def decrease_common_resource(alliance_id, amount=1):
    print(f"🧪 Mock: decrease_common_resource({alliance_id}, {amount})")
    return True

async def create_warehouse(cell_id):
    print(f"🧪 Mock: create_warehouse({cell_id})")
    return True

async def has_warehouse_in_hex(cell_id):
    print(f"🧪 Mock: has_warehouse_in_hex({cell_id})")
    return random.choice([True, False])

async def get_hexes_by_alliance(alliance_id):
    print(f"🧪 Mock: get_hexes_by_alliance({alliance_id})")
    return [{'id': i, 'state': f'Test-{i}'} for i in range(1, 4)]

async def get_warehouse_count_by_alliance(alliance_id):
    print(f"🧪 Mock: get_warehouse_count_by_alliance({alliance_id})")
    return random.randint(1, 5)

async def get_mission_id_by_battle_id(battle_id):
    print(f"🧪 Mock: get_mission_id_by_battle_id({battle_id})")
    return battle_id  # Simple mapping for mock

async def get_mission_details(mission_id):
    print(f"🧪 Mock: get_mission_details({mission_id})")
    return {
        'id': mission_id,
        'name': 'Mock Mission',
        'description': 'Test mission details',
        'rules': 'wh40k'
    }

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
    return list(MOCK_WARMASTERS.values())

async def get_alliance_player_count(alliance_id):
    print(f"🧪 Mock: get_alliance_player_count({alliance_id})")
    count = len([w for w in MOCK_WARMASTERS.values() if w['alliance'] == alliance_id])
    return count

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

async def get_rules_of_mission(number_of_mission):
    print(f"🧪 Mock: get_rules_of_mission({number_of_mission})")
    return 'wh40k'

async def get_state(cell_id):
    print(f"🧪 Mock: get_state({cell_id})")
    states = ['Лес', 'Поле', 'Город', 'Горы', 'Болото']
    return random.choice(states)

async def add_battle_result(mission_id, counts1, counts2):
    print(f"🧪 Mock: add_battle_result({mission_id}, {counts1}, {counts2})")
    return True

print("🧪 Mock SQLite Helper fully initialized")