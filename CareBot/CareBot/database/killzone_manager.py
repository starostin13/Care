import random

# Killzone типы и соответствующие им states гексов
KILLZONES = {
    "BHETA-DECIMA": ["черта города", "токсичная зона", "разрушенные руины", "останки корабля"],
    "GALLOWDARK": ["черта города", "разрушенные руины", "останки корабля"],
    "VOLKUS": ["черта города", "разрушенные руины"],
}

def get_available_killzones_for_state(hex_state):
    """Получает доступные killzone для данного state гекса"""
    available_killzones = []
    
    # Если state не None, проверяем совпадения
    if hex_state is not None:
        for killzone_type, states in KILLZONES.items():
            if hex_state in states:
                available_killzones.append(killzone_type)
    
    # NON-SPECIFIC доступен всегда (в том числе когда hex_state is None)
    available_killzones.append("NON-SPECIFIC")
    
    return available_killzones

def select_random_killzone(hex_state):
    """Случайно выбирает killzone для данного state гекса"""
    available_killzones = get_available_killzones_for_state(hex_state)
    return random.choice(available_killzones)

def get_killzone_for_mission(hex_state):
    """Основная функция для получения killzone для миссии"""
    return select_random_killzone(hex_state)
