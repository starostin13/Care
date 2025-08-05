#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Основной сервер приложения CareBot
Объединяет веб-интерфейс, mini-app и API
"""

import os
import logging
from flask import Flask, jsonify, render_template, request
from datetime import datetime

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_app():
    """Factory function для создания Flask приложения"""
    app = Flask(__name__)
    
    # Конфигурация
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'your-secret-key-here')
    app.config['DEBUG'] = os.getenv('FLASK_DEBUG', 'False').lower() == 'true'
    
    # Инициализация данных миссий
    missions_data = {
        "active_missions": [],
        "available_missions": [
            {"id": 1, "name": "Патрулирование сектора Alpha", "difficulty": "easy", "reward": 100},
            {"id": 2, "name": "Исследование аномалии", "difficulty": "medium", "reward": 200},
            {"id": 3, "name": "Оборона базы", "difficulty": "hard", "reward": 500}
        ],
        "completed_missions": []
    }
    
    # Маршруты
    @app.route('/health')
    def health_check():
        """Health check endpoint для Docker"""
        return jsonify({
            'status': 'healthy',
            'timestamp': datetime.now().isoformat(),
            'service': 'carebot-webapp'
        })
    
    @app.route('/')
    def index():
        """Главная страница"""
        try:
            return render_template('index.html', title='CareBot - Главная')
        except Exception as e:
            logger.error(f"Ошибка при рендере главной страницы: {e}")
            return "<h1>CareBot WebApp</h1><p>Добро пожаловать в систему управления CareBot!</p>"
    
    @app.route('/miniapp')
    def miniapp():
        """Mini App для Telegram"""
        try:
            return render_template('miniapp.html', title='CareBot MiniApp')
        except Exception as e:
            logger.error(f"Ошибка при рендере mini app: {e}")
            return """
            <!DOCTYPE html>
            <html>
            <head>
                <title>CareBot MiniApp</title>
                <meta charset="UTF-8">
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <style>
                    body {
                        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                        margin: 0;
                        padding: 20px;
                        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                        color: white;
                        min-height: 100vh;
                    }
                    .container {
                        max-width: 400px;
                        margin: 0 auto;
                    }
                    h1 {
                        text-align: center;
                        margin-bottom: 30px;
                    }
                    .mission-card {
                        background: rgba(255, 255, 255, 0.1);
                        border-radius: 10px;
                        padding: 15px;
                        margin-bottom: 15px;
                        backdrop-filter: blur(10px);
                        border: 1px solid rgba(255, 255, 255, 0.2);
                    }
                    .mission-name {
                        font-weight: bold;
                        margin-bottom: 5px;
                    }
                    .mission-reward {
                        color: #ffd700;
                    }
                    .loading {
                        text-align: center;
                        opacity: 0.7;
                    }
                </style>
            </head>
            <body>
                <div class="container">
                    <h1>🚀 CareBot MiniApp</h1>
                    <p>Добро пожаловать в Telegram Mini App!</p>
                    <div id="missions">
                        <h2>📋 Доступные миссии:</h2>
                        <div id="mission-list" class="loading">Загрузка миссий...</div>
                    </div>
                </div>
                <script>
                    // Простая загрузка миссий
                    fetch('/api/missions')
                        .then(response => response.json())
                        .then(data => {
                            const list = document.getElementById('mission-list');
                            list.innerHTML = '';
                            list.classList.remove('loading');
                            
                            if (data.available_missions && data.available_missions.length > 0) {
                                data.available_missions.forEach(mission => {
                                    const card = document.createElement('div');
                                    card.className = 'mission-card';
                                    card.innerHTML = `
                                        <div class="mission-name">${mission.name}</div>
                                        <div>Сложность: ${mission.difficulty}</div>
                                        <div class="mission-reward">Награда: ${mission.reward} кредитов</div>
                                    `;
                                    list.appendChild(card);
                                });
                            } else {
                                list.innerHTML = '<div class="mission-card">Миссии пока недоступны</div>';
                            }
                        })
                        .catch(error => {
                            console.error('Error:', error);
                            document.getElementById('mission-list').innerHTML = '<div class="mission-card">Ошибка загрузки миссий</div>';
                        });
                </script>
            </body>
            </html>
            """
    
    @app.route('/map')
    def map_view():
        """Карта игрового мира"""
        return jsonify({
            "message": "Карта пока не реализована",
            "status": "placeholder"
        })
    
    @app.route('/print-station')
    def print_station():
        """Станция печати"""
        return jsonify({
            "message": "Станция печати пока не реализована", 
            "status": "placeholder"
        })
    
    @app.route('/api/missions', methods=['GET'])
    def get_missions():
        """API для получения списка миссий"""
        try:
            return jsonify(missions_data)
        except Exception as e:
            logger.error(f"Ошибка при получении миссий: {e}")
            return jsonify({
                "error": "Не удалось загрузить миссии",
                "details": str(e)
            }), 500
    
    @app.route('/api/missions', methods=['POST'])
    def create_mission():
        """API для создания новой миссии"""
        try:
            data = request.get_json()
            if not data or 'name' not in data:
                return jsonify({"error": "Название миссии обязательно"}), 400
            
            new_mission = {
                "id": len(missions_data["available_missions"]) + 1,
                "name": data["name"],
                "difficulty": data.get("difficulty", "medium"),
                "reward": data.get("reward", 100)
            }
            
            missions_data["available_missions"].append(new_mission)
            
            return jsonify({
                "message": "Миссия создана успешно",
                "mission": new_mission
            }), 201
            
        except Exception as e:
            logger.error(f"Ошибка при создании миссии: {e}")
            return jsonify({
                "error": "Не удалось создать миссию",
                "details": str(e)
            }), 500
    
    @app.route('/api/missions/<int:mission_id>/complete', methods=['POST'])
    def complete_mission(mission_id):
        """API для завершения миссии"""
        try:
            # Найти миссию в доступных
            mission = None
            for i, m in enumerate(missions_data["available_missions"]):
                if m["id"] == mission_id:
                    mission = missions_data["available_missions"].pop(i)
                    break
            
            if not mission:
                return jsonify({"error": "Миссия не найдена"}), 404
            
            # Переместить в завершенные
            mission["completed_at"] = datetime.now().isoformat()
            missions_data["completed_missions"].append(mission)
            
            return jsonify({
                "message": "Миссия завершена успешно",
                "mission": mission,
                "reward": mission["reward"]
            })
            
        except Exception as e:
            logger.error(f"Ошибка при завершении миссии: {e}")
            return jsonify({
                "error": "Не удалось завершить миссию",
                "details": str(e)
            }), 500
    
    @app.errorhandler(404)
    def not_found(error):
        """Обработчик 404 ошибки"""
        return jsonify({"error": "Страница не найдена"}), 404
    
    @app.errorhandler(500)
    def internal_error(error):
        """Обработчик 500 ошибки"""
        return jsonify({"error": "Внутренняя ошибка сервера"}), 500
    
    return app

# Создание приложения
app = create_app()

if __name__ == '__main__':
    # Запуск для разработки
    host = os.getenv('HOST', '0.0.0.0')
    port = int(os.getenv('PORT', 5000))
    
    print(f"🚀 Starting CareBot WebApp on {host}:{port}")
    logger.info(f"CareBot WebApp starting on {host}:{port}")
    
    if os.getenv('FLASK_DEBUG', 'False').lower() == 'true':
        app.run(host=host, port=port, debug=True)
    else:
        app.run(host=host, port=port, debug=False)
