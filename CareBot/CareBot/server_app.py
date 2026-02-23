#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Обновленное серверное приложение с поддержкой синхронизации и печати
"""

from flask import Flask, render_template, jsonify, redirect, url_for
from datetime import datetime
import asyncio
import os

# Импортируем наши модули
from mission_engine import MissionGenerator, MissionStorage, MissionPrinter
from sync_api import setup_sync_api
import sqllite_helper
import auth

# Создаем Flask приложение
app = Flask(__name__)

# Configure secret key for sessions (required by Flask-Login)
app.secret_key = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'
app.config['SESSION_COOKIE_SECURE'] = True  # Require HTTPS for cookies
app.config['SESSION_COOKIE_HTTPONLY'] = True  # Prevent JavaScript access to session cookie
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'  # CSRF protection
app.config['PERMANENT_SESSION_LIFETIME'] = 3600  # 1 hour session timeout

# Initialize Flask-Login
login_manager = auth.init_login_manager(app)

# Register authentication blueprint
app.register_blueprint(auth.auth_bp)

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

@app.route('/contact')
def contact():
    """Страница контактов"""
    return render_template(
        'contact.html',
        title='Contact',
        year=datetime.now().year,
        message='Your contact page.'
    )

@app.route('/about')
def about():
    """Страница о проекте"""
    return render_template(
        'about.html',
        title='About',
        year=datetime.now().year,
        message='Your application description page.'
    )

@app.route('/health')
def health():
    """Health check endpoint для мониторинга"""
    try:
        import os
        db_path = os.environ.get('DATABASE_PATH', '/app/data/game_database.db')
        db_exists = os.path.exists(db_path)
        
        return jsonify({
            'status': 'healthy',
            'timestamp': datetime.now().isoformat(),
            'database': 'available' if db_exists else 'missing',
            'version': '1.0.0'
        }), 200
    except Exception as e:
        return jsonify({
            'status': 'unhealthy',
            'timestamp': datetime.now().isoformat(),
            'error': str(e),
            'version': '1.0.0'
        }), 500

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


# ============================================================================
# ADMIN ROUTES (Protected by @login_required)
# ============================================================================

@app.route('/admin')
@app.route('/admin/dashboard')
@auth.admin_required
def admin_dashboard():
    """Admin dashboard - main admin panel page"""
    from flask_login import current_user
    
    try:
        # Get statistics for dashboard
        active_missions = mission_storage.get_active_missions()
        completed_missions = [m for m in mission_storage.missions if m.completed]
        
        # Get today's missions
        today = datetime.now().date()
        todays_missions = [
            m for m in active_missions 
            if m.created_at.date() == today
        ]
        
        stats = {
            'active_missions': len(active_missions),
            'completed_today': len([m for m in completed_missions if m.created_at.date() == today]),
            'todays_missions': len(todays_missions),
            'total_missions': len(mission_storage.missions)
        }
        
        return render_template(
            'admin_dashboard.html',
            title='Админ-панель',
            year=datetime.now().year,
            user=current_user,
            stats=stats,
            active_missions=active_missions[:10],  # Last 10
        )
    except Exception as e:
        return f"Error loading dashboard: {e}", 500


# ============================================================================
# API ROUTES
# ============================================================================

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
    print("� HTTPS enabled with adhoc SSL certificate")
    print("📱 Mobile devices can sync at: https://[your-ip]:5000/api/sync")
    print("🗺️ Telegram Mini App at: https://[your-ip]:5000/map")
    print("🖨️ Print station at: https://[your-ip]:5000/print-station")
    print("⚠️ Note: You may need to accept the self-signed certificate on first access")
    
    # Use adhoc SSL for development (auto-generates certificate)
    # For production, use: ssl_context=('cert.pem', 'key.pem')
    app.run(host='0.0.0.0', port=5000, debug=True, ssl_context='adhoc')

