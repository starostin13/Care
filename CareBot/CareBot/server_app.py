#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Обновленное серверное приложение с поддержкой синхронизации и печати
"""

from flask import Flask, render_template, jsonify, redirect, url_for, request, flash
from datetime import datetime
import asyncio
import os
import random

# Импортируем наши модули
from .mission_engine import MissionGenerator, MissionStorage, MissionPrinter
from .sync_api import setup_sync_api
from . import sqllite_helper
from . import auth
from . import mission_helper

# Создаем Flask приложение
app = Flask(__name__)

# Configure secret key for sessions (required by Flask-Login)
app.secret_key = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'
app.config['SESSION_COOKIE_SECURE'] = os.environ.get('SESSION_COOKIE_SECURE', 'false').lower() == 'true'
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

@app.route('/manifest.json')
def manifest():
    """PWA Web App Manifest"""
    try:
        with open('CareBot/static/manifest.json', 'r') as f:
            import json
            manifest_data = json.load(f)
        return jsonify(manifest_data), 200, {'Content-Type': 'application/manifest+json'}
    except Exception as e:
        return jsonify({'error': str(e)}), 500

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


@app.route('/admin/enter-result')
@auth.admin_required
def admin_enter_result():
    """Admin page for entering battle results"""
    from flask_login import current_user
    
    return render_template(
        'admin_result_entry.html',
        title='Ввод результата битвы',
        year=datetime.now().year,
        user=current_user
    )


@app.route('/admin/submit-result', methods=['POST'])
@auth.admin_required
def admin_submit_result():
    """Handle admin battle result submission"""
    from flask_login import current_user
    
    try:
        battle_id = request.form.get('battle_id')
        player1_score = int(request.form.get('player1_score'))
        player2_score = int(request.form.get('player2_score'))
        
        if not battle_id:
            flash('Выберите бой', 'error')
            return redirect(url_for('admin_enter_result'))
        
        # Submit the result
        result = asyncio.run(
            sqllite_helper.submit_admin_battle_result(
                int(battle_id),
                player1_score, 
                player2_score,
                current_user.warmaster_id
            )
        )
        
        if result['status'] == 'success':
            flash(f'Результат успешно сохранен: {player1_score} - {player2_score}', 'success')
        else:
            flash(f'Ошибка: {result["message"]}', 'error')
        
        return redirect(url_for('admin_enter_result'))
        
    except Exception as e:
        flash(f'Ошибка при сохранении результата: {str(e)}', 'error')
        return redirect(url_for('admin_enter_result'))


@app.route('/admin/create-mission')
@auth.admin_required
def admin_create_mission():
    """Admin page for creating missions"""
    from flask_login import current_user
    
    return render_template(
        'admin_create_mission.html',
        title='Создание миссии',
        year=datetime.now().year,
        user=current_user
    )


@app.route('/admin/submit-mission', methods=['POST'])
@auth.admin_required
def admin_submit_mission():
    """Handle admin mission creation"""
    from flask_login import current_user
    
    try:
        rules = request.form.get('rules')
        player1_telegram_id = request.form.get('player1_telegram_id')
        player2_telegram_id = request.form.get('player2_telegram_id')
        hex_id_raw = request.form.get('hex_id')
        
        if not rules or not player1_telegram_id or not player2_telegram_id:
            flash('Заполните все обязательные поля', 'error')
            return redirect(url_for('admin_create_mission'))
        
        if player1_telegram_id == player2_telegram_id:
            flash('Игроки должны быть разными', 'error')
            return redirect(url_for('admin_create_mission'))
        
        hex_id = int(hex_id_raw) if hex_id_raw else None
        
        # Generate mission template
        mission_tuple = mission_helper.generate_new_one(rules)
        
        # Determine hex if not provided
        if hex_id is None:
            attacker_alliance = asyncio.run(
                sqllite_helper.get_alliance_of_warmaster(player1_telegram_id)
            )
            defender_alliance = asyncio.run(
                sqllite_helper.get_alliance_of_warmaster(player2_telegram_id)
            )
            
            if attacker_alliance and defender_alliance:
                attacker_alliance_id = attacker_alliance[0]
                defender_alliance_id = defender_alliance[0]
                
                adjacent_hexes = asyncio.run(
                    sqllite_helper.get_adjacent_hexes_between_alliances(
                        attacker_alliance_id, defender_alliance_id
                    )
                )
                adjacent_list = list(adjacent_hexes) if adjacent_hexes else []
                if adjacent_list:
                    hex_id = random.choice(adjacent_list)[0]
                else:
                    defender_hexes = asyncio.run(
                        sqllite_helper.get_hexes_by_alliance(defender_alliance_id)
                    )
                    defender_list = list(defender_hexes) if defender_hexes else []
                    if defender_list:
                        hex_id = random.choice(defender_list)[0]
            
        if hex_id is None:
            flash('Не удалось определить гекс. Укажите гекс вручную.', 'error')
            return redirect(url_for('admin_create_mission'))
        
        # Build mission data with chosen hex
        mission_data = (
            mission_tuple[0],
            mission_tuple[1],
            hex_id,
            mission_tuple[3],
            mission_tuple[4] if len(mission_tuple) > 4 else None,
            mission_tuple[5] if len(mission_tuple) > 5 else None,
            mission_tuple[6] if len(mission_tuple) > 6 else None
        )
        
        # Save mission and get ID
        mission_id = asyncio.run(sqllite_helper.save_mission_and_get_id(mission_data))
        if not mission_id:
            flash('Ошибка создания миссии', 'error')
            return redirect(url_for('admin_create_mission'))
        
        # Lock mission and start battle
        asyncio.run(sqllite_helper.lock_mission(mission_id))
        battle_id = asyncio.run(
            mission_helper.start_battle(mission_id, player1_telegram_id, player2_telegram_id)
        )
        
        flash(f'Миссия #{mission_id} создана, бой #{battle_id}', 'success')
        return redirect(url_for('admin_enter_result'))
    
    except Exception as e:
        flash(f'Ошибка при создании миссии: {str(e)}', 'error')
        return redirect(url_for('admin_create_mission'))


# ============================================================================
# API ROUTES
# ============================================================================

@app.route('/api/admin/active-missions')
@auth.admin_required
def api_get_active_missions():
    """API endpoint to get active missions for admin panel"""
    try:
        battles = asyncio.run(sqllite_helper.get_active_battles_for_admin())
        
        return jsonify({
            'status': 'success',
            'missions': battles
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500


@app.route('/api/admin/warmasters')
@auth.admin_required
def api_get_warmasters():
    """API endpoint to get warmasters for admin dropdowns"""
    try:
        warmasters = asyncio.run(sqllite_helper.get_warmasters_for_admin())
        data = [
            {
                'telegram_id': row[0],
                'display_name': row[1],
                'alliance': row[2]
            }
            for row in warmasters
        ]
        return jsonify({'status': 'success', 'warmasters': data})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500


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

