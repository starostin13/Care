#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Sync API для синхронизации с мобильным приложением
"""

from flask import Flask, request, jsonify
from datetime import datetime
import json
import asyncio
import threading

# Импортируем наши модули
import sqllite_helper
from mission_engine import Mission, MissionStorage

class SyncAPI:
    """API для синхронизации с мобильными устройствами"""
    
    def __init__(self, app: Flask):
        self.app = app
        self.mission_storage = MissionStorage("server_missions.json")
        self.setup_routes()
    
    def setup_routes(self):
        """Настройка маршрутов API"""
        
        @self.app.route('/api/ping')
        def ping():
            """Проверка доступности сервера"""
            return jsonify({"status": "ok", "timestamp": datetime.now().isoformat()})
        
        @self.app.route('/api/sync', methods=['POST'])
        def sync_data():
            """Синхронизация данных от мобильного устройства"""
            try:
                data = request.get_json()
                action = data.get('action')
                payload = data.get('data')
                
                if action == 'mission_created':
                    # Получили новую миссию от мобильного устройства
                    mission = Mission.from_dict(payload)
                    self.mission_storage.add_mission(mission)
                    
                    # Добавляем в базу данных сервера
                    asyncio.run(self._save_mission_to_db(mission))
                    
                    return jsonify({"status": "success", "message": "Mission synced"})
                
                elif action == 'mission_completed':
                    # Миссия завершена
                    mission_id = payload.get('mission_id')
                    result = payload.get('result')
                    winner_id = payload.get('winner_id')
                    
                    self.mission_storage.complete_mission(mission_id, result, winner_id)
                    
                    # Обновляем базу данных
                    asyncio.run(self._complete_mission_in_db(mission_id, result, winner_id))
                    
                    return jsonify({"status": "success", "message": "Mission completed"})
                
                else:
                    return jsonify({"status": "error", "message": "Unknown action"}), 400
                    
            except Exception as e:
                return jsonify({"status": "error", "message": str(e)}), 500
        
        @self.app.route('/api/map-data')
        def get_map_data():
            """Получение данных карты для синхронизации"""
            try:
                # Получаем данные карты асинхронно
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                map_data = loop.run_until_complete(sqllite_helper.get_all_map_cells())
                loop.close()
                
                # Преобразуем данные в нужный формат
                formatted_data = []
                for cell in map_data:
                    formatted_data.append({
                        'id': cell[0],
                        'planet_id': cell[1],
                        'state': cell[2],
                        'patron': cell[3],
                        'has_warehouse': bool(cell[4]) if len(cell) > 4 else False
                    })
                
                return jsonify(formatted_data)
                
            except Exception as e:
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/api/players')
        def get_players():
            """Получение списка игроков"""
            try:
                # Здесь должна быть функция получения игроков из БД
                # Пока возвращаем тестовые данные
                players = [
                    {
                        "id": "1",
                        "name": "Test Player 1",
                        "faction": "space_marines",
                        "alliance_id": "alliance_1"
                    },
                    {
                        "id": "2", 
                        "name": "Test Player 2",
                        "faction": "chaos",
                        "alliance_id": "alliance_2"
                    }
                ]
                return jsonify(players)
                
            except Exception as e:
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/api/missions')
        def get_missions():
            """Получение списка миссий"""
            try:
                missions = self.mission_storage.get_active_missions()
                missions_data = [mission.to_dict() for mission in missions]
                return jsonify(missions_data)
                
            except Exception as e:
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/api/mission/<mission_id>')
        def get_mission(mission_id):
            """Получение конкретной миссии"""
            try:
                mission = self.mission_storage.get_mission(mission_id)
                if mission:
                    return jsonify(mission.to_dict())
                else:
                    return jsonify({'error': 'Mission not found'}), 404
                    
            except Exception as e:
                return jsonify({'error': str(e)}), 500
    
    async def _save_mission_to_db(self, mission: Mission):
        """Сохранение миссии в базу данных сервера"""
        try:
            # Здесь должна быть функция сохранения миссии в основную БД
            # Пока просто логируем
            print(f"Mission {mission.id} saved to server database")
            
        except Exception as e:
            print(f"Error saving mission to DB: {e}")
    
    async def _complete_mission_in_db(self, mission_id: str, result: str, winner_id: str):
        """Завершение миссии в базе данных"""
        try:
            # Здесь должна быть логика обновления карты на основе результатов миссии
            print(f"Mission {mission_id} completed with result: {result}, winner: {winner_id}")
            
        except Exception as e:
            print(f"Error completing mission in DB: {e}")

# Функция для интеграции с существующим Flask приложением
def setup_sync_api(app: Flask):
    """Настройка API синхронизации"""
    sync_api = SyncAPI(app)
    return sync_api
