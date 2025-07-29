#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Offline Mobile App - работает без интернета, синхронизируется по Wi-Fi
Использует Kivy для создания мобильного интерфейса
"""

import json
import os
import sqlite3
import requests
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import threading
import time

# Импортируем общий движок миссий
import sys
sys.path.append('..')
from mission_engine import MissionGenerator, Mission, Player, MapHex, MissionStorage, MissionPrinter, MissionType, Faction

try:
    from kivy.app import App
    from kivy.uix.boxlayout import BoxLayout
    from kivy.uix.button import Button
    from kivy.uix.label import Label
    from kivy.uix.textinput import TextInput
    from kivy.uix.spinner import Spinner
    from kivy.uix.popup import Popup
    from kivy.uix.gridlayout import GridLayout
    from kivy.uix.scrollview import ScrollView
    from kivy.clock import Clock
    KIVY_AVAILABLE = True
except ImportError:
    KIVY_AVAILABLE = False
    print("Kivy not available. Install with: pip install kivy")

class OfflineDataManager:
    """Менеджер офлайн данных"""
    
    def __init__(self, db_path: str = "offline_crusade.db"):
        self.db_path = db_path
        self.init_database()
        self.mission_storage = MissionStorage("offline_missions.json")
        self.sync_url = "http://192.168.1.100:5000"  # IP сервера в локальной сети
        
    def init_database(self):
        """Инициализация локальной базы данных"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Таблица игроков
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS players (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            faction TEXT NOT NULL,
            alliance_id TEXT NOT NULL,
            telegram_id TEXT,
            phone TEXT,
            last_sync DATETIME
        )
        ''')
        
        # Таблица карты
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS map_hexes (
            id INTEGER PRIMARY KEY,
            planet_id INTEGER,
            state TEXT,
            patron_alliance TEXT,
            has_warehouse BOOLEAN,
            coordinates_x INTEGER,
            coordinates_y INTEGER,
            last_sync DATETIME
        )
        ''')
        
        # Таблица синхронизации
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS sync_queue (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            action TEXT NOT NULL,
            data TEXT NOT NULL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            synced BOOLEAN DEFAULT FALSE
        )
        ''')
        
        conn.commit()
        conn.close()
    
    def add_player(self, player: Player):
        """Добавление игрока в локальную БД"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
        INSERT OR REPLACE INTO players 
        (id, name, faction, alliance_id, telegram_id, phone, last_sync)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (player.id, player.name, player.faction.value, player.alliance_id, 
              player.telegram_id, player.phone, datetime.now()))
        
        conn.commit()
        conn.close()
    
    def get_players(self) -> List[Player]:
        """Получение всех игроков"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM players')
        rows = cursor.fetchall()
        
        players = []
        for row in rows:
            player = Player(
                id=row[0],
                name=row[1], 
                faction=Faction(row[2]),
                alliance_id=row[3],
                telegram_id=row[4],
                phone=row[5]
            )
            players.append(player)
        
        conn.close()
        return players
    
    def add_to_sync_queue(self, action: str, data: Dict):
        """Добавление действия в очередь синхронизации"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
        INSERT INTO sync_queue (action, data)
        VALUES (?, ?)
        ''', (action, json.dumps(data)))
        
        conn.commit()
        conn.close()
    
    def sync_with_server(self) -> bool:
        """Синхронизация с сервером по Wi-Fi"""
        try:
            # Проверяем подключение к серверу
            response = requests.get(f"{self.sync_url}/api/ping", timeout=5)
            if response.status_code != 200:
                return False
            
            # Отправляем данные из очереди синхронизации
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('SELECT * FROM sync_queue WHERE synced = FALSE')
            sync_items = cursor.fetchall()
            
            for item in sync_items:
                item_id, action, data, created_at, synced = item
                
                try:
                    response = requests.post(
                        f"{self.sync_url}/api/sync",
                        json={"action": action, "data": json.loads(data)},
                        timeout=10
                    )
                    
                    if response.status_code == 200:
                        cursor.execute('UPDATE sync_queue SET synced = TRUE WHERE id = ?', (item_id,))
                
                except Exception as e:
                    print(f"Failed to sync item {item_id}: {e}")
            
            # Получаем обновления с сервера
            response = requests.get(f"{self.sync_url}/api/map-data", timeout=10)
            if response.status_code == 200:
                map_data = response.json()
                self._update_local_map(map_data)
            
            conn.commit()
            conn.close()
            return True
            
        except Exception as e:
            print(f"Sync failed: {e}")
            return False
    
    def _update_local_map(self, map_data: List[Dict]):
        """Обновление локальной карты"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        for hex_data in map_data:
            cursor.execute('''
            INSERT OR REPLACE INTO map_hexes 
            (id, planet_id, state, patron_alliance, has_warehouse, last_sync)
            VALUES (?, ?, ?, ?, ?, ?)
            ''', (hex_data['id'], hex_data.get('planet_id'), hex_data.get('state'),
                  hex_data.get('patron'), hex_data.get('has_warehouse', False),
                  datetime.now()))
        
        conn.commit()
        conn.close()

class CrusadeMobileApp(App if KIVY_AVAILABLE else object):
    """Мобильное приложение Crusade"""
    
    def __init__(self):
        if KIVY_AVAILABLE:
            super().__init__()
        self.data_manager = OfflineDataManager()
        self.mission_generator = MissionGenerator()
        self.mission_printer = MissionPrinter()
        self.current_mission = None
        
        # Запускаем фоновую синхронизацию
        self.start_background_sync()
    
    def build(self):
        """Построение интерфейса"""
        if not KIVY_AVAILABLE:
            return None
            
        main_layout = BoxLayout(orientation='vertical', padding=10, spacing=10)
        
        # Заголовок
        title = Label(text='Crusade Mission Generator', size_hint_y=None, height=50, 
                     font_size=20, bold=True)
        main_layout.add_widget(title)
        
        # Статус синхронизации
        self.sync_status = Label(text='Sync Status: Checking...', size_hint_y=None, height=30)
        main_layout.add_widget(self.sync_status)
        
        # Кнопки основных действий
        button_layout = GridLayout(cols=2, size_hint_y=None, height=200, spacing=10)
        
        generate_btn = Button(text='Generate Mission', font_size=16)
        generate_btn.bind(on_press=self.show_mission_generator)
        button_layout.add_widget(generate_btn)
        
        print_btn = Button(text='Print Mission', font_size=16)
        print_btn.bind(on_press=self.print_current_mission)
        button_layout.add_widget(print_btn)
        
        players_btn = Button(text='Manage Players', font_size=16)
        players_btn.bind(on_press=self.show_players_manager)
        button_layout.add_widget(players_btn)
        
        sync_btn = Button(text='Manual Sync', font_size=16)
        sync_btn.bind(on_press=self.manual_sync)
        button_layout.add_widget(sync_btn)
        
        main_layout.add_widget(button_layout)
        
        # Область для отображения текущей миссии
        self.mission_display = Label(text='No mission generated', text_size=(None, None),
                                   valign='top', halign='left')
        scroll = ScrollView()
        scroll.add_widget(self.mission_display)
        main_layout.add_widget(scroll)
        
        # Запускаем проверку статуса синхронизации
        Clock.schedule_interval(self.update_sync_status, 5)
        
        return main_layout
    
    def show_mission_generator(self, instance):
        """Показать генератор миссий"""
        if not KIVY_AVAILABLE:
            return
            
        content = BoxLayout(orientation='vertical', spacing=10)
        
        # Выбор типа миссии
        mission_type_label = Label(text='Mission Type:', size_hint_y=None, height=30)
        content.add_widget(mission_type_label)
        
        mission_type_spinner = Spinner(
            text='Kill Team',
            values=['Kill Team', 'Warhammer 40k', 'Boarding Action', 'Combat Patrol', 'Battlefleet'],
            size_hint_y=None, height=44
        )
        content.add_widget(mission_type_spinner)
        
        # Выбор игроков
        players_label = Label(text='Select Players:', size_hint_y=None, height=30)
        content.add_widget(players_label)
        
        # Здесь должен быть список игроков с чекбоксами
        # Упрощенная версия - два поля для имен игроков
        player1_input = TextInput(hint_text='Player 1 Name', size_hint_y=None, height=40)
        player2_input = TextInput(hint_text='Player 2 Name', size_hint_y=None, height=40)
        content.add_widget(player1_input)
        content.add_widget(player2_input)
        
        # Hex ID
        hex_label = Label(text='Target Hex ID:', size_hint_y=None, height=30)
        content.add_widget(hex_label)
        
        hex_input = TextInput(hint_text='Hex ID (e.g., 1)', size_hint_y=None, height=40)
        content.add_widget(hex_input)
        
        # Кнопки
        button_layout = BoxLayout(size_hint_y=None, height=50, spacing=10)
        
        generate_btn = Button(text='Generate')
        generate_btn.bind(on_press=lambda x: self.generate_mission(
            mission_type_spinner.text, player1_input.text, player2_input.text, 
            hex_input.text, popup))
        button_layout.add_widget(generate_btn)
        
        cancel_btn = Button(text='Cancel')
        cancel_btn.bind(on_press=lambda x: popup.dismiss())
        button_layout.add_widget(cancel_btn)
        
        content.add_widget(button_layout)
        
        popup = Popup(title='Mission Generator', content=content, size_hint=(0.9, 0.8))
        popup.open()
    
    def generate_mission(self, mission_type_str: str, player1_name: str, player2_name: str, 
                        hex_id_str: str, popup):
        """Генерация миссии"""
        try:
            # Преобразуем тип миссии
            mission_type_map = {
                'Kill Team': MissionType.KILL_TEAM,
                'Warhammer 40k': MissionType.WH40K,
                'Boarding Action': MissionType.BOARDING_ACTION,
                'Combat Patrol': MissionType.COMBAT_PATROL,
                'Battlefleet': MissionType.BATTLEFLEET
            }
            mission_type = mission_type_map.get(mission_type_str, MissionType.KILL_TEAM)
            
            # Создаем игроков
            players = [
                Player(f"player_{int(time.time())}_1", player1_name or "Player 1", 
                      Faction.SPACE_MARINES, "alliance_1"),
                Player(f"player_{int(time.time())}_2", player2_name or "Player 2", 
                      Faction.CHAOS, "alliance_2")
            ]
            
            # Создаем hex
            hex_id = int(hex_id_str) if hex_id_str.isdigit() else 1
            target_hex = MapHex(hex_id, 1, "contested")
            
            # Генерируем миссию
            mission = self.mission_generator.generate_mission(mission_type, players, target_hex)
            self.current_mission = mission
            
            # Сохраняем миссию
            self.data_manager.mission_storage.add_mission(mission)
            
            # Добавляем в очередь синхронизации
            self.data_manager.add_to_sync_queue('mission_created', mission.to_dict())
            
            # Обновляем отображение
            self.update_mission_display(mission, players)
            
            popup.dismiss()
            
        except Exception as e:
            print(f"Error generating mission: {e}")
    
    def update_mission_display(self, mission: Mission, players: List[Player]):
        """Обновление отображения миссии"""
        if KIVY_AVAILABLE and hasattr(self, 'mission_display'):
            formatted_text = self.mission_printer.format_mission_for_print(mission, players)
            self.mission_display.text = formatted_text
            self.mission_display.text_size = (self.mission_display.parent.width - 20, None)
    
    def print_current_mission(self, instance):
        """Печать текущей миссии"""
        if self.current_mission:
            players = self.data_manager.get_players()
            success = self.mission_printer.print_mission(self.current_mission, players)
            
            if KIVY_AVAILABLE:
                status_text = "Mission printed successfully!" if success else "Failed to print mission"
                popup = Popup(title='Print Status', 
                            content=Label(text=status_text),
                            size_hint=(0.6, 0.3))
                popup.open()
        else:
            if KIVY_AVAILABLE:
                popup = Popup(title='Error', 
                            content=Label(text='No mission to print'),
                            size_hint=(0.6, 0.3))
                popup.open()
    
    def show_players_manager(self, instance):
        """Показать менеджер игроков"""
        # Упрощенная версия - просто показываем список игроков
        if KIVY_AVAILABLE:
            players = self.data_manager.get_players()
            players_text = "Current Players:\n\n"
            for player in players:
                players_text += f"• {player.name} ({player.faction.value})\n"
            
            popup = Popup(title='Players Manager', 
                        content=Label(text=players_text),
                        size_hint=(0.8, 0.6))
            popup.open()
    
    def manual_sync(self, instance):
        """Ручная синхронизация"""
        def sync_thread():
            success = self.data_manager.sync_with_server()
            if KIVY_AVAILABLE:
                Clock.schedule_once(lambda dt: self.show_sync_result(success), 0)
        
        threading.Thread(target=sync_thread, daemon=True).start()
    
    def show_sync_result(self, success: bool):
        """Показать результат синхронизации"""
        if KIVY_AVAILABLE:
            status_text = "Sync completed successfully!" if success else "Sync failed - check connection"
            popup = Popup(title='Sync Status', 
                        content=Label(text=status_text),
                        size_hint=(0.6, 0.3))
            popup.open()
    
    def update_sync_status(self, dt):
        """Обновление статуса синхронизации"""
        if KIVY_AVAILABLE and hasattr(self, 'sync_status'):
            # Проверяем подключение
            try:
                response = requests.get(f"{self.data_manager.sync_url}/api/ping", timeout=2)
                if response.status_code == 200:
                    self.sync_status.text = "Sync Status: Connected"
                else:
                    self.sync_status.text = "Sync Status: Server unreachable"
            except:
                self.sync_status.text = "Sync Status: Offline"
    
    def start_background_sync(self):
        """Запуск фоновой синхронизации"""
        def background_sync():
            while True:
                try:
                    self.data_manager.sync_with_server()
                except:
                    pass
                time.sleep(30)  # Синхронизация каждые 30 секунд
        
        sync_thread = threading.Thread(target=background_sync, daemon=True)
        sync_thread.start()

# Консольная версия для тестирования без Kivy
class ConsoleCrusadeApp:
    """Консольная версия приложения"""
    
    def __init__(self):
        self.data_manager = OfflineDataManager()
        self.mission_generator = MissionGenerator()
        self.mission_printer = MissionPrinter()
        self.current_mission = None
    
    def run(self):
        """Запуск консольного интерфейса"""
        print("🚀 Crusade Mission Generator - Console Mode")
        print("=" * 50)
        
        while True:
            print("\nOptions:")
            print("1. Generate Mission")
            print("2. Print Current Mission")
            print("3. View Players")
            print("4. Manual Sync")
            print("5. Exit")
            
            choice = input("\nSelect option (1-5): ").strip()
            
            if choice == "1":
                self.console_generate_mission()
            elif choice == "2":
                self.console_print_mission()
            elif choice == "3":
                self.console_view_players()
            elif choice == "4":
                self.console_sync()
            elif choice == "5":
                print("Goodbye!")
                break
            else:
                print("Invalid choice!")
    
    def console_generate_mission(self):
        """Генерация миссии в консоли"""
        print("\n🎯 Mission Generator")
        print("-" * 30)
        
        # Выбор типа миссии
        mission_types = list(MissionType)
        print("Mission Types:")
        for i, mt in enumerate(mission_types, 1):
            print(f"{i}. {mt.value}")
        
        try:
            choice = int(input("Select mission type (1-5): ")) - 1
            mission_type = mission_types[choice]
        except (ValueError, IndexError):
            mission_type = MissionType.KILL_TEAM
            print("Using default: Kill Team")
        
        # Ввод игроков
        player1_name = input("Player 1 name: ").strip() or "Player 1"
        player2_name = input("Player 2 name: ").strip() or "Player 2"
        
        # Hex ID
        try:
            hex_id = int(input("Target Hex ID: ").strip())
        except ValueError:
            hex_id = 1
            print("Using default hex: 1")
        
        # Создаем данные
        players = [
            Player(f"p1_{int(time.time())}", player1_name, Faction.SPACE_MARINES, "alliance_1"),
            Player(f"p2_{int(time.time())}", player2_name, Faction.CHAOS, "alliance_2")
        ]
        
        target_hex = MapHex(hex_id, 1, "contested")
        
        # Генерируем миссию
        mission = self.mission_generator.generate_mission(mission_type, players, target_hex)
        self.current_mission = mission
        
        # Сохраняем
        self.data_manager.mission_storage.add_mission(mission)
        self.data_manager.add_to_sync_queue('mission_created', mission.to_dict())
        
        print("\n✅ Mission Generated!")
        print(self.mission_printer.format_mission_for_print(mission, players))
    
    def console_print_mission(self):
        """Печать миссии в консоли"""
        if self.current_mission:
            players = self.data_manager.get_players()
            success = self.mission_printer.print_mission(self.current_mission, players)
            print("✅ Mission sent to printer!" if success else "❌ Failed to print")
        else:
            print("❌ No mission to print")
    
    def console_view_players(self):
        """Просмотр игроков в консоли"""
        players = self.data_manager.get_players()
        print(f"\n👥 Players ({len(players)}):")
        for player in players:
            print(f"• {player.name} ({player.faction.value}) - {player.alliance_id}")
    
    def console_sync(self):
        """Синхронизация в консоли"""
        print("\n🔄 Syncing with server...")
        success = self.data_manager.sync_with_server()
        print("✅ Sync completed!" if success else "❌ Sync failed - check connection")

def main():
    """Главная функция"""
    if KIVY_AVAILABLE:
        print("🚀 Starting Kivy mobile app...")
        app = CrusadeMobileApp()
        app.run()
    else:
        print("📱 Kivy not available, starting console mode...")
        app = ConsoleCrusadeApp()
        app.run()

if __name__ == "__main__":
    main()
