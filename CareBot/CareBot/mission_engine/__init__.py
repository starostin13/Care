#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Mission Engine - общий модуль для генерации миссий
Используется как серверным приложением, так и мобильным приложением
"""

import json
import random
import uuid
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from typing import List, Dict, Optional, Tuple
from enum import Enum

class MissionType(Enum):
    KILL_TEAM = "killteam"
    BOARDING_ACTION = "boardingaction"
    WH40K = "wh40k"
    COMBAT_PATROL = "combatpatrol"
    BATTLEFLEET = "battlefleet"

class Faction(Enum):
    SPACE_MARINES = "space_marines"
    CHAOS = "chaos"
    ORKS = "orks"
    ELDAR = "eldar"
    TYRANIDS = "tyranids"
    IMPERIAL_GUARD = "imperial_guard"
    NECRONS = "necrons"
    TAU = "tau"

@dataclass
class Player:
    """Игрок"""
    id: str
    name: str
    faction: Faction
    alliance_id: str
    telegram_id: Optional[str] = None
    phone: Optional[str] = None
    
@dataclass
class MapHex:
    """Клетка карты"""
    id: int
    planet_id: int
    state: str
    patron_alliance: Optional[str] = None
    has_warehouse: bool = False
    coordinates: Tuple[int, int] = (0, 0)

@dataclass
class Mission:
    """Миссия"""
    id: str
    short_id: str  # Короткий ID для ввода в телеграме (например, M001)
    mission_type: MissionType
    title: str
    description: str
    hex_id: int
    participants: List[str]  # player IDs
    created_at: datetime
    scheduled_for: Optional[datetime] = None
    completed: bool = False
    result: Optional[str] = None
    winner_id: Optional[str] = None
    # Поля для отслеживания администраторского ввода
    admin_entered: bool = False  # True если результат введен администратором
    entered_by: Optional[str] = None  # ID warmaster который ввел результат
    confirmation_required: bool = True  # False если подтверждение не требуется
    
    def to_dict(self) -> Dict:
        """Конвертация в словарь для JSON"""
        data = asdict(self)
        data['mission_type'] = self.mission_type.value
        data['created_at'] = self.created_at.isoformat()
        if self.scheduled_for:
            data['scheduled_for'] = self.scheduled_for.isoformat()
        return data
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'Mission':
        """Создание из словаря"""
        data['mission_type'] = MissionType(data['mission_type'])
        data['created_at'] = datetime.fromisoformat(data['created_at'])
        if data.get('scheduled_for'):
            data['scheduled_for'] = datetime.fromisoformat(data['scheduled_for'])
        return cls(**data)
    
    def format_for_print(self) -> str:
        """Форматирование миссии для печати"""
        lines = []
        lines.append("=" * 50)
        lines.append(f"🎯 МИССИЯ: {self.title}")
        lines.append(f"🆔 ID: {self.short_id}")  # Короткий ID на видном месте
        lines.append("=" * 50)
        lines.append("")
        lines.append(f"📍 Локация: Hex {self.hex_id}")
        lines.append(f"🎮 Тип: {self.mission_type.value}")
        lines.append(f"📅 Создана: {self.created_at.strftime('%Y-%m-%d %H:%M')}")
        if self.scheduled_for:
            lines.append(f"⏰ Запланирована на: {self.scheduled_for.strftime('%Y-%m-%d %H:%M')}")
        lines.append("")
        lines.append("📜 ОПИСАНИЕ:")
        lines.append(self.description)
        lines.append("")
        lines.append("👥 УЧАСТНИКИ:")
        for i, participant in enumerate(self.participants, 1):
            lines.append(f"  {i}. {participant}")
        lines.append("")
        lines.append("=" * 50)
        lines.append(f"💡 Для ввода результата используйте команду в Telegram:")
        lines.append(f"   /result {self.short_id} [ваши_очки] [очки_противника]")
        lines.append("")
        lines.append(f"📞 Пример: /result {self.short_id} 15 8")
        lines.append("=" * 50)
        
        return "\n".join(lines)

class MissionGenerator:
    """Генератор миссий"""
    
    def __init__(self):
        self.mission_templates = self._load_mission_templates()
    
    def _load_mission_templates(self) -> Dict[MissionType, List[Dict]]:
        """Загрузка шаблонов миссий"""
        return {
            MissionType.KILL_TEAM: [
                {
                    "title": "Infiltration",
                    "description": "Secure the intelligence data from the enemy facility.",
                    "objectives": ["Reach the center", "Hold for 2 turns", "Extract safely"],
                    "special_rules": ["Stealth deployment", "Limited visibility"]
                },
                {
                    "title": "Sabotage",
                    "description": "Destroy the enemy communications array.",
                    "objectives": ["Locate the array", "Plant explosives", "Defend until detonation"],
                    "special_rules": ["Timed objectives", "Reinforcements"]
                },
                {
                    "title": "Rescue Mission",
                    "description": "Extract the captured operative from enemy territory.",
                    "objectives": ["Locate prisoner", "Eliminate guards", "Escape to extraction point"],
                    "special_rules": ["Prisoner is wounded", "Alarm system"]
                }
            ],
            MissionType.WH40K: [
                {
                    "title": "Planetary Assault",
                    "description": "Establish a beachhead on the enemy-held planet.",
                    "objectives": ["Control 3 objectives", "Eliminate enemy leadership", "Hold territory"],
                    "special_rules": ["Dawn of War", "Deep Strike allowed"]
                },
                {
                    "title": "Supply Line",
                    "description": "Secure the vital supply convoy route.",
                    "objectives": ["Escort convoy", "Eliminate ambushes", "Reach destination"],
                    "special_rules": ["Moving objectives", "Ambush deployment"]
                }
            ],
            MissionType.BOARDING_ACTION: [
                {
                    "title": "Ship Takeover",
                    "description": "Board and capture the enemy vessel.",
                    "objectives": ["Breach hull", "Control bridge", "Secure engine room"],
                    "special_rules": ["Confined spaces", "Explosive decompression risk"]
                }
            ],
            MissionType.COMBAT_PATROL: [
                {
                    "title": "Reconnaissance",
                    "description": "Scout enemy positions and report back.",
                    "objectives": ["Identify targets", "Avoid detection", "Return with intel"],
                    "special_rules": ["Stealth mission", "No heavy weapons"]
                }
            ],
            MissionType.BATTLEFLEET: [
                {
                    "title": "Fleet Engagement",
                    "description": "Destroy or disable the enemy fleet.",
                    "objectives": ["Sink flagship", "Control space lane", "Minimize losses"],
                    "special_rules": ["3D movement", "Torpedo salvos"]
                }
            ]
        }
    
    def generate_mission(self, 
                        mission_type: MissionType, 
                        participants: List[Player], 
                        target_hex: MapHex,
                        scheduled_time: Optional[datetime] = None) -> Mission:
        """Генерация новой миссии"""
        
        # Выбираем случайный шаблон для типа миссии
        templates = self.mission_templates.get(mission_type, [])
        if not templates:
            raise ValueError(f"No templates found for mission type: {mission_type}")
        
        template = random.choice(templates)
        
        # Создаем уникальный ID миссии
        mission_id = str(uuid.uuid4())
        
        # Создаем короткий ID для ввода в телеграме
        short_id = self._generate_short_id()
        
        # Генерируем описание с учетом участников и локации
        description = self._customize_description(template, participants, target_hex, short_id)
        
        # Создаем миссию
        mission = Mission(
            id=mission_id,
            short_id=short_id,
            mission_type=mission_type,
            title=template["title"],
            description=description,
            hex_id=target_hex.id,
            participants=[p.id for p in participants],
            created_at=datetime.now(),
            scheduled_for=scheduled_time
        )
        
        return mission
    
    def _generate_short_id(self) -> str:
        """Генерация короткого ID для миссии (например, M001, M002, ...)"""
        import time
        # Используем timestamp для уникальности
        timestamp_suffix = str(int(time.time()))[-3:]  # Последние 3 цифры timestamp
        return f"M{timestamp_suffix}"
    
    def _customize_description(self, template: Dict, participants: List[Player], target_hex: MapHex, short_id: str) -> str:
        """Кастомизация описания миссии"""
        base_description = template["description"]
        
        # Добавляем Mission ID в начале
        mission_header = f"🎯 MISSION {short_id}"
        
        # Добавляем информацию о локации
        location_info = f"\n\nLocation: Hex {target_hex.id}"
        if target_hex.has_warehouse:
            location_info += " (Strategic Warehouse Present)"
        
        # Добавляем информацию об участниках
        participant_info = f"\nParticipants: {', '.join([p.name for p in participants])}"
        
        # Добавляем цели
        objectives_info = "\n\nObjectives:\n"
        for i, obj in enumerate(template.get("objectives", []), 1):
            objectives_info += f"{i}. {obj}\n"
        
        # Добавляем специальные правила
        special_rules = template.get("special_rules", [])
        if special_rules:
            rules_info = "\nSpecial Rules:\n"
            for rule in special_rules:
                rules_info += f"• {rule}\n"
        else:
            rules_info = ""
        
        # Добавляем инструкции для ввода результатов
        result_instructions = f"\n\n📱 TO REPORT RESULTS:\nSend to Telegram Bot: /result {short_id} [your_score] [opponent_score]\nExample: /result {short_id} 15 8"
        
        return mission_header + "\n" + base_description + location_info + participant_info + objectives_info + rules_info + result_instructions

class MissionPrinter:
    """Класс для печати миссий"""
    
    def __init__(self, printer_name: Optional[str] = None):
        self.printer_name = printer_name
    
    def format_mission_for_print(self, mission: Mission, players: List[Player]) -> str:
        """Форматирование миссии для печати"""
        
        # Заголовок
        output = "=" * 60 + "\n"
        output += f"CRUSADE MISSION: {mission.title.upper()}\n"
        output += f"MISSION ID: {mission.short_id}\n"
        output += "=" * 60 + "\n\n"
        
        # Основная информация
        output += f"Type: {mission.mission_type.value.upper()}\n"
        output += f"Hex: {mission.hex_id}\n"
        output += f"Created: {mission.created_at.strftime('%Y-%m-%d %H:%M')}\n"
        
        if mission.scheduled_for:
            output += f"Scheduled: {mission.scheduled_for.strftime('%Y-%m-%d %H:%M')}\n"
        
        output += "\n" + "-" * 60 + "\n"
        
        # Участники
        output += "PARTICIPANTS:\n"
        for player in players:
            if player.id in mission.participants:
                output += f"• {player.name} ({player.faction.value})\n"
        
        output += "\n" + "-" * 60 + "\n"
        
        # Описание миссии
        output += "MISSION BRIEFING:\n"
        output += mission.description + "\n"
        
        output += "\n" + "-" * 60 + "\n"
        
        # Поле для результатов
        output += "BATTLE RESULTS:\n\n"
        output += "Winner: ________________\n\n"
        output += "Score: _____ vs _____\n\n"
        output += "Notes:\n"
        output += "_" * 50 + "\n" * 3
        
        output += "\n" + "=" * 60 + "\n"
        output += f"Generated by Crusade Mission Engine v1.0\n"
        output += "=" * 60 + "\n"
        
        return output
    
    def print_mission(self, mission: Mission, players: List[Player]) -> bool:
        """Печать миссии"""
        try:
            formatted_text = self.format_mission_for_print(mission, players)
            
            # Сохраняем в файл для печати
            filename = f"mission_{mission.id[:8]}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(formatted_text)
            
            # Попытка печати (зависит от ОС)
            import os
            import platform
            
            if platform.system() == "Windows":
                # Windows - отправляем на принтер по умолчанию
                os.system(f'notepad /p "{filename}"')
            elif platform.system() == "Linux":
                # Linux - используем lp
                os.system(f'lp "{filename}"')
            elif platform.system() == "Darwin":
                # macOS - используем lpr
                os.system(f'lpr "{filename}"')
            
            return True
            
        except Exception as e:
            print(f"Error printing mission: {e}")
            return False

class MissionStorage:
    """Класс для хранения миссий (может работать с файлами или БД)"""
    
    def __init__(self, storage_path: str = "missions.json"):
        self.storage_path = storage_path
        self.missions: List[Mission] = []
        self.load_missions()
    
    def load_missions(self):
        """Загрузка миссий из файла"""
        try:
            with open(self.storage_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                # Поддерживаем старый формат (просто список) и новый (объект с missions)
                if isinstance(data, list):
                    self.missions = [Mission.from_dict(m) for m in data]
                else:
                    self.missions = [Mission.from_dict(m) for m in data.get('missions', [])]
        except FileNotFoundError:
            self.missions = []
        except Exception as e:
            print(f"Error loading missions: {e}")
            self.missions = []
    
    def save_missions(self):
        """Сохранение миссий в файл"""
        try:
            with open(self.storage_path, 'w', encoding='utf-8') as f:
                data = {
                    'missions': [m.to_dict() for m in self.missions],
                    'last_id': len(self.missions)
                }
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Error saving missions: {e}")
    
    def add_mission(self, mission: Mission):
        """Добавление миссии"""
        self.missions.append(mission)
        self.save_missions()
    
    def save_mission(self, mission: Mission):
        """Сохранение одной миссии (алиас для add_mission)"""
        self.add_mission(mission)
    
    def get_mission(self, mission_id: str) -> Optional[Mission]:
        """Получение миссии по ID"""
        for mission in self.missions:
            if mission.id == mission_id:
                return mission
        return None
    
    def get_mission_by_short_id(self, short_id: str) -> Optional[Mission]:
        """Получение миссии по короткому ID"""
        for mission in self.missions:
            if mission.short_id.upper() == short_id.upper():
                return mission
        return None
    
    def get_missions_for_hex(self, hex_id: int) -> List[Mission]:
        """Получение миссий для определенного hex"""
        return [m for m in self.missions if m.hex_id == hex_id]
    
    def get_active_missions(self) -> List[Mission]:
        """Получение активных (незавершенных) миссий"""
        return [m for m in self.missions if not m.completed]
    
    def complete_mission(self, mission_id: str, result: str, winner_id: str):
        """Завершение миссии"""
        mission = self.get_mission(mission_id)
        if mission:
            mission.completed = True
            mission.result = result
            mission.winner_id = winner_id
            self.save_missions()
    
    def complete_mission_by_short_id(self, short_id: str, result: str, winner_id: str) -> bool:
        """Завершение миссии по короткому ID"""
        mission = self.get_mission_by_short_id(short_id)
        if mission:
            mission.completed = True
            mission.result = result
            mission.winner_id = winner_id
            self.save_missions()
            return True
        return False

# Пример использования
if __name__ == "__main__":
    # Создаем генератор миссий
    generator = MissionGenerator()
    
    # Создаем тестовых игроков
    players = [
        Player("1", "John", Faction.SPACE_MARINES, "alliance_1"),
        Player("2", "Alex", Faction.CHAOS, "alliance_2")
    ]
    
    # Создаем тестовый hex
    target_hex = MapHex(1, 1, "contested", has_warehouse=True)
    
    # Генерируем миссию
    mission = generator.generate_mission(
        MissionType.KILL_TEAM, 
        players, 
        target_hex,
        datetime.now() + timedelta(hours=2)
    )
    
    print("Generated mission:")
    print(f"Title: {mission.title}")
    print(f"Description: {mission.description}")
    
    # Печатаем миссию
    printer = MissionPrinter()
    print("\n" + "="*60)
    print(printer.format_mission_for_print(mission, players))
