#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Обновленное серверное приложение с поддержкой синхронизации и печати
"""

from flask import Flask, render_template, jsonify
from datetime import datetime
import asyncio
import os

# Импортируем наши модули
from mission_engine import MissionGenerator, MissionStorage, MissionPrinter
from sync_api import setup_sync_api
import sqllite_helper

# Создаем Flask приложение
app = Flask(__name__)

# Инициализируем компоненты
mission_generator = MissionGenerator()
mission_storage = MissionStorage("server_missions.json")
mission_printer = MissionPrinter()

# Настраиваем API синхронизации
sync_api = setup_sync_api(app)

@app.route('/')
@app.route('/home')
def home():
    """Главная страница"""
    return render_template(
        'index.html',
        title='Crusade Care Bot',
        year=datetime.now().year,
    )

@app.route('/map')
def map_view():
    """Страница карты для Telegram Mini App"""
    return render_template(
        'map.html',
        title='Crusade Map',
        year=datetime.now().year,
    )

@app.route('/missions')
def missions_view():
    """Страница управления миссиями"""
    try:
        missions = mission_storage.get_active_missions()
        return render_template(
            'missions.html',
            title='Mission Management',
            missions=missions,
            year=datetime.now().year,
        )
    except Exception as e:
        return f"Error loading missions: {e}", 500

@app.route('/print-station')
def print_station():
    """Станция печати миссий"""
    return render_template(
        'print_station.html',
        title='Mission Print Station',
        year=datetime.now().year,
    )

@app.route('/api/map-data')
def get_map_data():
    """API для получения данных карты"""
    async def fetch_map_data():
        return await sqllite_helper.get_all_map_cells()
    
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        map_data = loop.run_until_complete(fetch_map_data())
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

@app.route('/api/hex-info/<int:hex_id>')
def get_hex_info(hex_id):
    """API для получения информации о hex"""
    async def fetch_hex_info():
        # Получаем информацию о hex
        try:
            cell_info = await sqllite_helper.get_cell_info(hex_id)
            history = await sqllite_helper.get_cell_histrory(hex_id)
            
            # Получаем имя альянса-патрона
            patron_name = None
            if cell_info and len(cell_info) > 3 and cell_info[3]:  # patron field
                try:
                    patron_info = await sqllite_helper.get_alliance_name(cell_info[3])
                    patron_name = patron_info[0] if patron_info else None
                except:
                    patron_name = f"Alliance {cell_info[3]}"
            
            return {
                'cell_info': cell_info,
                'history': [h[0] for h in history] if history else [],
                'patron_name': patron_name
            }
        except Exception as e:
            return {'error': str(e)}
    
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        hex_data = loop.run_until_complete(fetch_hex_info())
        loop.close()
        
        return jsonify(hex_data)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/print-mission/<mission_id>', methods=['POST'])
def print_mission_api(mission_id):
    """API для печати миссии"""
    try:
        mission = mission_storage.get_mission(mission_id)
        if not mission:
            return jsonify({'error': 'Mission not found'}), 404
        
        # Получаем игроков (здесь упрощенная версия)
        players = []  # Должно получать из БД
        
        success = mission_printer.print_mission(mission, players)
        
        if success:
            return jsonify({'status': 'success', 'message': 'Mission printed'})
        else:
            return jsonify({'error': 'Failed to print mission'}), 500
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    print("🚀 Starting Crusade Server with sync support...")
    print("📱 Mobile devices can sync at: http://[your-ip]:5000/api/sync")
    print("🗺️ Telegram Mini App at: http://[your-ip]:5000/map")
    print("🖨️ Print station at: http://[your-ip]:5000/print-station")
    
    app.run(host='0.0.0.0', port=5000, debug=True)
