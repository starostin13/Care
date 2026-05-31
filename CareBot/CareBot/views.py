"""
Routes and views for the flask application.
"""

import asyncio
import logging
from datetime import datetime
from flask import render_template, jsonify, Response, request
from . import app
from . import map_export_service
from . import sqllite_helper
from . import mission_helper
import os

logger = logging.getLogger(__name__)


def _run_async(coro):
    """Run async code from sync Flask route context."""
    try:
        return asyncio.run(coro)
    except RuntimeError:
        loop = asyncio.new_event_loop()
        try:
            return loop.run_until_complete(coro)
        finally:
            loop.close()


@app.route('/')
@app.route('/home')
def home():
    """Renders the home page."""
    return render_template(
        'index.html',
        title='Home Page',
        year=datetime.now().year,
    )

@app.route('/contact')
def contact():
    """Renders the contact page."""
    return render_template(
        'contact.html',
        title='Contact',
        year=datetime.now().year,
        message='Your contact page.'
    )

@app.route('/about')
def about():
    """Renders the about page."""
    return render_template(
        'about.html',
        title='About',
        year=datetime.now().year,
        message='Your application description page.'
    )

@app.route('/health')
def health():
    """Health check endpoint for monitoring."""
    try:
        # Check if database file exists
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


@app.route('/admin/map_export.png', methods=['GET'])
def export_map_png():
    """Export full planet map as PNG via HTTP for local network access."""
    try:
        png_bytes = _run_async(map_export_service.generate_realistic_map_png())
    except map_export_service.EmptyMapExportError:
        return jsonify({
            'status': 'error',
            'message': 'Карта пуста, экспортировать нечего.',
            'timestamp': datetime.now().isoformat(),
        }), 404
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': 'Не удалось экспортировать карту.',
            'timestamp': datetime.now().isoformat(),
            'error': str(e),
        }), 500

    return Response(png_bytes, mimetype='image/png')


# ============================================================================
# Battles Web UI
# ============================================================================

@app.route('/battles')
def battles():
    """Web UI for managing battle results."""
    active = _run_async(sqllite_helper.get_active_battles_for_web())
    pending = _run_async(sqllite_helper.get_pending_battles_for_web())
    completed = _run_async(sqllite_helper.get_completed_battles_for_web())
    warmasters = _run_async(sqllite_helper.get_warmasters_with_nicknames())
    return render_template(
        'battles.html',
        title='Управление битвами',
        active_battles=active,
        pending_battles=pending,
        completed_battles=completed,
        warmasters=warmasters,
        year=datetime.now().year,
    )


def _api_error(error_code: str, error: str, status_code: int = 400):
    return jsonify({'ok': False, 'error_code': error_code, 'error': error}), status_code


@app.route('/api/battles/create', methods=['POST'])
def create_battle():
    """Create a new battle from web UI.

    Accepts JSON body with:
      - mission_id (optional int): use an existing mission. If omitted, a new mission is
        auto-generated using the `rules` field.
            - battle_id (optional int): explicit battle ID for recovery scenarios.
      - rules (optional str): required when mission_id is not provided. One of:
        killteam, wh40k, boarding_action, combat_patrol, battlefleet.
      - participant_1_id (int): telegram_id of player 1
      - participant_2_id (int): telegram_id of player 2
    """
    VALID_RULES = {'killteam', 'wh40k', 'boarding_action', 'combat_patrol', 'battlefleet'}

    data = request.get_json(silent=True) or {}
    mission_raw = data.get('mission_id')
    battle_raw = data.get('battle_id')
    rules_raw = data.get('rules', '').strip()
    p1_raw = data.get('participant_1_id')
    p2_raw = data.get('participant_2_id')

    explicit_battle_id = None
    if battle_raw not in (None, ''):
        try:
            explicit_battle_id = int(battle_raw)
        except (ValueError, TypeError):
            return _api_error('invalid_format', 'battle_id должен быть числом')
        if explicit_battle_id <= 0:
            return _api_error('invalid_range', 'battle_id должен быть больше нуля')

    # Determine mode: explicit mission_id or auto-generate from rules
    use_explicit_mission = mission_raw not in (None, '')

    if use_explicit_mission:
        try:
            requested_mission_id = int(mission_raw)
        except (ValueError, TypeError):
            return _api_error('invalid_format', 'mission_id должен быть числом')
        if requested_mission_id <= 0:
            return _api_error('invalid_range', 'mission_id должен быть больше нуля')
    else:
        if not rules_raw:
            return _api_error('missing_fields', 'Укажите mission_id или rules для автогенерации миссии')
        if rules_raw not in VALID_RULES:
            return _api_error('invalid_rules', f'rules должен быть одним из: {", ".join(sorted(VALID_RULES))}')
        requested_mission_id = None

    if p1_raw in (None, '') or p2_raw in (None, ''):
        return _api_error('missing_fields', 'participant_1_id и participant_2_id обязательны')

    try:
        participant_1_id = int(p1_raw)
        participant_2_id = int(p2_raw)
    except (ValueError, TypeError):
        return _api_error('invalid_format', 'participant IDs должны быть числами')

    if participant_1_id <= 0 or participant_2_id <= 0:
        return _api_error('invalid_range', 'participant IDs должны быть больше нуля')

    if participant_1_id == participant_2_id:
        return _api_error('same_participants', 'Участники должны быть разными')

    try:
        async def _create():
            selected_mission_id = requested_mission_id

            if explicit_battle_id is not None:
                if await sqllite_helper.battle_exists(explicit_battle_id):
                    return _api_error(
                        'battle_id_exists',
                        f'Битва с id={explicit_battle_id} уже существует. Укажите другой battle_id.',
                        409,
                    )

            if use_explicit_mission:
                # --- Use existing mission ---
                if selected_mission_id is None:
                    return _api_error('mission_resolve_failed', 'mission_id не определён', 500)

                mission = await sqllite_helper.get_mission_details(selected_mission_id)
                if not mission:
                    return _api_error('mission_not_found', f'Миссия #{selected_mission_id} не найдена', 404)

                if mission.status not in (0, 1):
                    return _api_error(
                        'mission_status_invalid',
                        f'Миссия #{selected_mission_id} в статусе {mission.status}. Создание разрешено только для 0/1.'
                    )

                existing_battle_id = await sqllite_helper.get_battle_id_by_mission_id(selected_mission_id)
                if existing_battle_id:
                    return _api_error(
                        'battle_already_exists',
                        f'Для миссии #{selected_mission_id} уже есть битва #{existing_battle_id}',
                        409
                    )
            else:
                # --- Auto-generate mission from rules ---
                mission_tuple = mission_helper.generate_new_one(rules_raw)
                await sqllite_helper.save_mission(mission_tuple)
                new_mission = await sqllite_helper.get_mission(rules_raw)
                if not new_mission:
                    return _api_error('mission_gen_failed', 'Не удалось создать миссию. Попробуйте ещё раз.', 500)
                selected_mission_id = new_mission.id
                logger.info('Web UI: auto-generated mission %s (rules=%s)', selected_mission_id, rules_raw)

            p1_id = str(participant_1_id)
            p2_id = str(participant_2_id)

            p1_nick = await sqllite_helper.get_nickname_by_telegram_id(p1_id)
            p2_nick = await sqllite_helper.get_nickname_by_telegram_id(p2_id)
            if not p1_nick:
                return _api_error('participant_not_found', f'Участник {participant_1_id} не найден')
            if not p2_nick:
                return _api_error('participant_not_found', f'Участник {participant_2_id} не найден')

            p1_alliance_row = await sqllite_helper.get_alliance_of_warmaster(p1_id)
            p2_alliance_row = await sqllite_helper.get_alliance_of_warmaster(p2_id)

            p1_alliance = p1_alliance_row[0] if p1_alliance_row else None
            p2_alliance = p2_alliance_row[0] if p2_alliance_row else None

            if not p1_alliance:
                return _api_error('participant_no_alliance', f'Участник {participant_1_id} не состоит в альянсе')
            if not p2_alliance:
                return _api_error('participant_no_alliance', f'Участник {participant_2_id} не состоит в альянсе')
            if p1_alliance == p2_alliance:
                return _api_error('same_alliance', 'Участники не могут быть из одного альянса')

            if selected_mission_id is None:
                return _api_error('mission_resolve_failed', 'Не удалось определить mission_id для создания боя', 500)

            await mission_helper.ensure_mission_cell(selected_mission_id, p1_id, p2_id)

            battle_id = await mission_helper.start_battle(
                selected_mission_id,
                p1_id,
                p2_id,
                forced_battle_id=explicit_battle_id,
            )
            # Ensure mission is locked (status=1) — start_battle doesn't change status
            await sqllite_helper.update_mission_status(selected_mission_id, 1)

            logger.info(
                'Web UI: created battle %s for mission %s (rules=%s), p1=%s p2=%s',
                battle_id, selected_mission_id, rules_raw or 'explicit',
                participant_1_id, participant_2_id,
            )
            return jsonify({'ok': True, 'battle_id': battle_id, 'mission_id': selected_mission_id})

        return _run_async(_create())
    except Exception as e:
        logger.error('Web UI create battle error: %s', e, exc_info=True)
        return _api_error('create_failed', str(e), 500)


@app.route('/api/battles/<int:battle_id>/submit', methods=['POST'])
def submit_battle_result(battle_id):
    """Submit a battle result from the web UI into pending confirmation flow."""
    data = request.get_json(silent=True) or {}
    try:
        p1_score = int(data.get('p1_score', 0))
        p2_score = int(data.get('p2_score', 0))
        submitter_id = str(data.get('submitter_id', ''))
    except (ValueError, TypeError) as e:
        return jsonify({'ok': False, 'error': f'Некорректные данные: {e}'}), 400

    if not submitter_id:
        return jsonify({'ok': False, 'error': 'submitter_id обязателен'}), 400

    try:
        result = _run_async(
            mission_helper.submit_pending_battle_result(
                battle_id,
                submitter_id,
                p1_score,
                p2_score,
            )
        )
        logger.info(
            'Web UI: pending result saved for battle %s by %s (%s:%s)',
            battle_id,
            submitter_id,
            p1_score,
            p2_score,
        )
        return jsonify({'ok': True, 'pending': True, 'mission_id': result['mission_id']})
    except PermissionError as e:
        logger.error('Web UI submit permission error for battle %s: %s', battle_id, e)
        return jsonify({'ok': False, 'error': str(e)}), 403
    except ValueError as e:
        logger.error('Web UI submit validation error for battle %s: %s', battle_id, e)
        return jsonify({'ok': False, 'error': str(e)}), 400
    except Exception as e:
        logger.error('Web UI submit error for battle %s: %s', battle_id, e)
        return jsonify({'ok': False, 'error': str(e)}), 500


@app.route('/api/battles/<int:battle_id>/confirm', methods=['POST'])
def confirm_battle_result(battle_id):
    """Confirm a pending battle result from the web UI."""
    try:
        result = _run_async(
            mission_helper.confirm_pending_battle_result(
                battle_id,
                confirmer_id=None,
                require_participant=False,
                allow_submitter_confirm=True,
            )
        )
        logger.info('Web UI: confirmed pending result for battle %s', battle_id)
        return jsonify({'ok': True, 'mission_id': result['mission_id']})
    except PermissionError as e:
        logger.error('Web UI confirm permission error for battle %s: %s', battle_id, e)
        return jsonify({'ok': False, 'error': str(e)}), 403
    except ValueError as e:
        logger.error('Web UI confirm validation error for battle %s: %s', battle_id, e)
        return jsonify({'ok': False, 'error': str(e)}), 400
    except Exception as e:
        logger.error('Web UI confirm error for battle %s: %s', battle_id, e)
        return jsonify({'ok': False, 'error': str(e)}), 500


@app.route('/api/battles/<int:battle_id>/reject', methods=['POST'])
def reject_battle_result(battle_id):
    """Reject/cancel a pending battle result from the web UI."""
    try:
        result = _run_async(
            mission_helper.reject_pending_battle_result(
                battle_id,
                rejector_id=None,
                require_participant=False,
                allow_submitter_reject=True,
            )
        )
        logger.info('Web UI: rejected pending result for battle %s', battle_id)
        return jsonify({'ok': True, 'mission_id': result['mission_id']})
    except PermissionError as e:
        logger.error('Web UI reject permission error for battle %s: %s', battle_id, e)
        return jsonify({'ok': False, 'error': str(e)}), 403
    except ValueError as e:
        logger.error('Web UI reject validation error for battle %s: %s', battle_id, e)
        return jsonify({'ok': False, 'error': str(e)}), 400
    except Exception as e:
        logger.error('Web UI reject error for battle %s: %s', battle_id, e)
        return jsonify({'ok': False, 'error': str(e)}), 500
