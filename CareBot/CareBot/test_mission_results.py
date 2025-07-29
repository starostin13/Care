#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Тестирование системы результатов миссий
"""

import sys
import os
import json
from datetime import datetime

# Добавляем путь к основному проекту
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from mission_engine import MissionGenerator, MissionStorage, Mission, MissionType, Player, MapHex, Faction

def test_mission_creation_and_results():
    """Тест создания миссии и ввода результатов"""
    print("🧪 Тест системы миссий")
    print("=" * 50)
    
    # 1. Создаем генератор миссий
    generator = MissionGenerator()
    storage = MissionStorage("test_missions.json")
    
    print("1. Создание тестовой миссии...")
    
    # 2. Создаем тестовые объекты
    player1 = Player(
        id="player1", 
        name="Alice", 
        faction=Faction.SPACE_MARINES, 
        alliance_id="alliance1", 
        telegram_id="123456"
    )
    player2 = Player(
        id="player2", 
        name="Bob", 
        faction=Faction.CHAOS, 
        alliance_id="alliance2", 
        telegram_id="789012"
    )
    participants = [player1, player2]
    
    target_hex = MapHex(
        id=5,
        planet_id=1,
        state="contested",
        patron_alliance=None,
        has_warehouse=False
    )
    
    # 3. Генерируем миссию
    mission = generator.generate_mission(
        mission_type=MissionType.KILL_TEAM,
        participants=participants,
        target_hex=target_hex
    )
    
    print(f"   ✅ Миссия создана: {mission.short_id}")
    print(f"   📍 Hex: {mission.hex_id}")
    print(f"   🎯 Тип: {mission.mission_type}")
    print(f"   👥 Участники: {mission.participants}")
    print()
    
    # 4. Сохраняем миссию
    storage.save_mission(mission)
    print("2. Миссия сохранена в хранилище")
    print()
    
    # 5. Показываем формат для печати
    print("3. Формат для печати:")
    print("-" * 30)
    print_format = mission.format_for_print()
    print(print_format)
    print("-" * 30)
    print()
    
    # 6. Тестируем поиск по короткому ID
    print("4. Тест поиска по короткому ID...")
    found_mission = storage.get_mission_by_short_id(mission.short_id)
    if found_mission:
        print(f"   ✅ Миссия найдена: {found_mission.title}")
        print(f"   📊 Статус: {'Завершена' if found_mission.completed else 'Активна'}")
    else:
        print("   ❌ Миссия не найдена!")
    print()
    
    # 7. Тестируем завершение миссии
    print("5. Тест завершения миссии...")
    result = "15 - 8"
    winner_id = "player1"
    
    success = storage.complete_mission_by_short_id(mission.short_id, result, winner_id)
    if success:
        print(f"   ✅ Миссия {mission.short_id} завершена")
        print(f"   📊 Результат: {result}")
        print(f"   🏆 Победитель: {winner_id}")
        
        # Проверяем обновленную миссию
        updated_mission = storage.get_mission_by_short_id(mission.short_id)
        if updated_mission and updated_mission.completed:
            print(f"   ✅ Статус обновлен: Завершена")
            print(f"   📅 Время завершения: {updated_mission.completed_at if hasattr(updated_mission, 'completed_at') else 'Не задано'}")
        else:
            print("   ❌ Ошибка обновления статуса")
    else:
        print("   ❌ Ошибка при завершении миссии")
    print()
    
    # 8. Тестируем список активных миссий - создадим дополнительные миссии
    print("6. Создание дополнительных миссий для теста...")
    for i in range(3):
        test_hex = MapHex(
            id=10+i,
            planet_id=1,
            state="contested",
            patron_alliance=None,
            has_warehouse=False
        )
        
        test_participants = [
            Player(
                id=f"player{i+3}", 
                name=f"Player{i+3}", 
                faction=Faction.SPACE_MARINES if i % 2 == 0 else Faction.CHAOS,
                alliance_id=f"alliance{i+3}",
                telegram_id=f"10000{i}"
            ),
            Player(
                id=f"player{i+4}", 
                name=f"Player{i+4}", 
                faction=Faction.NECRONS,
                alliance_id=f"alliance{i+4}",
                telegram_id=f"20000{i}"
            )
        ]
        
        mission_type = MissionType.KILL_TEAM if i % 2 == 0 else MissionType.WH40K
        test_mission = generator.generate_mission(
            mission_type=mission_type,
            participants=test_participants,
            target_hex=test_hex
        )
        storage.save_mission(test_mission)
        print(f"   ✅ Создана миссия {test_mission.short_id} в hex {test_hex.id}")
    print()
    
    # 9. Показываем список активных миссий
    print("7. Список активных миссий:")
    active_missions = storage.get_active_missions()
    if active_missions:
        for mission in active_missions:
            status = "🔴 Завершена" if mission.completed else "🟢 Активна"
            print(f"   • {mission.short_id} - {mission.title} [{status}]")
            print(f"     Hex: {mission.hex_id} | Создана: {mission.created_at.strftime('%H:%M')}")
    else:
        print("   📭 Нет активных миссий")
    print()
    
    # 10. Показываем пример команд для Telegram
    print("8. Примеры команд для Telegram:")
    if active_missions:
        example_mission = active_missions[0]  # Берем первую активную миссию
        print(f"   /result {example_mission.short_id} 20 15  - победа 20:15")
        print(f"   /result {example_mission.short_id} 10 10  - ничья 10:10") 
        print(f"   /result {example_mission.short_id} 8 12   - поражение 8:12")
    else:
        print("   /result M123 20 15  - пример команды")
    print()
    
    # 11. Показываем содержимое файла миссий
    print("9. Содержимое файла миссий:")
    try:
        with open("test_missions.json", 'r', encoding='utf-8') as f:
            missions_data = json.load(f)
            print(f"   📁 Всего миссий в файле: {len(missions_data.get('missions', []))}")
            print(f"   🆔 Последний ID: {missions_data.get('last_id', 0)}")
    except Exception as e:
        print(f"   ❌ Ошибка чтения файла: {e}")
    
    print("=" * 50)
    print("🎉 Тест завершен успешно!")
    
    return active_missions  # Возвращаем для второго теста

def simulate_telegram_commands():
    """Симуляция команд телеграм бота"""
    print("\n🤖 Симуляция команд Telegram бота")
    print("=" * 50)
    
    storage = MissionStorage("test_missions.json")
    
    # Получаем первую активную миссию для теста
    active_missions = storage.get_active_missions()
    if not active_missions:
        print("❌ Нет активных миссий для теста команд")
        return
    
    test_mission = active_missions[0]
    mission_id = test_mission.short_id
    
    print(f"🎯 Тестируем команды с миссией {mission_id}")
    print()
    
    # Симулируем различные варианты команд
    test_commands = [
        f"/result {mission_id} 20 15",  # Победа
        f"/result {mission_id} 10 10",  # Ничья
        f"/result {mission_id} 8 22",   # Поражение
        "/result M999 10 5",            # Несуществующая миссия
        "/result ABC 10 5",             # Неверный формат ID
        "/result M123",                 # Недостаточно аргументов
        "/result M123 abc 5",           # Неверный формат очков
    ]
    
    for i, command in enumerate(test_commands, 1):
        print(f"{i}. Команда: {command}")
        
        # Парсим команду
        parts = command.split()
        if len(parts) < 4:
            print("   ❌ Недостаточно аргументов")
            print(f"   📝 Ответ: Неверный формат команды! Используйте: /result M123 15 8")
        else:
            cmd, cmd_mission_id, score1, score2 = parts[0], parts[1], parts[2], parts[3]
            
            try:
                user_score = int(score1)
                opponent_score = int(score2)
                
                # Проверяем формат ID
                import re
                if not re.match(r'^M\d+$', cmd_mission_id.upper()):
                    print("   ❌ Неверный формат ID миссии")
                    print(f"   📝 Ответ: ID должен быть вида M123, M456 и т.д.")
                else:
                    # Ищем миссию
                    found_mission = storage.get_mission_by_short_id(cmd_mission_id.upper())
                    if not found_mission:
                        print(f"   ❌ Миссия {cmd_mission_id.upper()} не найдена")
                        print(f"   📝 Ответ: Миссия не найдена! Проверьте правильность ID.")
                    else:
                        if found_mission.completed:
                            print(f"   ⚠️ Миссия уже завершена")
                            print(f"   📝 Ответ: Миссия уже завершена! Результат: {found_mission.result}")
                        else:
                            # Определяем победителя
                            if user_score > opponent_score:
                                winner = "Вы"
                            elif opponent_score > user_score:
                                winner = "Противник"
                            else:
                                winner = "Ничья"
                            
                            print(f"   ✅ Команда корректна")
                            print(f"   📊 Результат: {user_score} - {opponent_score}")
                            print(f"   🏆 Победитель: {winner}")
                            print(f"   📝 Ответ: Подтверждение результата миссии {cmd_mission_id.upper()}")
                            
            except ValueError:
                print("   ❌ Очки должны быть числами")
                print("   📝 Ответ: Очки должны быть числами! Пример: /result M123 15 8")
        
        print()
    
    print("=" * 50)
    print("🤖 Симуляция команд завершена!")

if __name__ == "__main__":
    # Запускаем тесты
    active_missions = test_mission_creation_and_results()
    simulate_telegram_commands()
    
    print("\n💡 Для тестирования с реальным ботом:")
    print("1. Запустите handlers.py")
    print("2. Создайте миссию через мобильное приложение")
    print("3. Используйте команды /result, /missions_list, /help_missions в Telegram")
