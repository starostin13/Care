"""Helper functions for interacting with the SQLite database asynchronously
using aiosqlite.

Enhanced with detailed debug logging for alliance/opponent resolution.
"""

import datetime
import aiosqlite
import os
import random
import logging
from typing import List, Dict, Optional
from models import Mission, Battle, MissionDetails, Warmaster, Alliance, MapCell

logger = logging.getLogger(__name__)

# Use environment variable for database path, fallback to default
DATABASE_PATH = os.environ.get('DATABASE_PATH', 
    r"C:\Users\al-gerasimov\source\repos\Care\CareBot\CareBot\db\database")


async def add_battle_participant(battle_id, participant):
    async with aiosqlite.connect(DATABASE_PATH) as db:
        await db.execute('''
            INSERT INTO battle_attenders(battle_id, attender_id)
            VALUES(?, ?)
        ''', (battle_id, participant))
        await db.commit()


async def add_battle(mission_id):
    """Create a new battle record with mission_id.
    
    Args:
        mission_id: The mission ID
    
    Returns:
        Tuple with battle ID
    """
    async with aiosqlite.connect(DATABASE_PATH) as db:
        await db.execute('''
            INSERT INTO battles(mission_id) VALUES(?)
        ''', (mission_id,))
        await db.commit()
        async with db.execute('SELECT last_insert_rowid()') as cursor:
            return await cursor.fetchone()


async def get_mission_id_for_battle(battle_id):
    """Get the mission_id for a battle record.
    
    Args:
        battle_id: The ID of the battle
        
    Returns:
        int: Mission ID if found, None otherwise
    """
    async with aiosqlite.connect(DATABASE_PATH) as db:
        async with db.execute('''
            SELECT mission_id FROM battles WHERE id = ?
        ''', (battle_id,)) as cursor:
            result = await cursor.fetchone()
            return result[0] if result else None


async def add_to_story(cell_id, text):
    async with aiosqlite.connect(DATABASE_PATH) as db:
        await db.execute('''
            INSERT OR IGNORE INTO map_story(hex_id, content)
            VALUES(?,?)
        ''', (cell_id, text))
        await db.commit()

async def get_cell_history(cell_id):
    async with aiosqlite.connect(DATABASE_PATH) as db:
        async with db.execute('''
            SELECT content
            FROM map_story
            WHERE hex_id=?
        ''', (cell_id,)) as cursor:
            return await cursor.fetchall()

async def set_cell_patron(cell_id, winner_alliance_id):
    async with aiosqlite.connect(DATABASE_PATH) as db:
        await db.execute('''
            UPDATE map SET patron=? WHERE id=?
        ''', (winner_alliance_id, cell_id))
        await db.commit()


async def get_cell_id_by_battle_id(battle_id: int):
    async with aiosqlite.connect(DATABASE_PATH) as db:
        async with db.execute('''
            SELECT mission_stack.cell
            FROM battles
            JOIN mission_stack ON battles.mission_id = mission_stack.id
            WHERE battles.id = ?
        ''', (battle_id,)) as cursor:
            result = await cursor.fetchone()
            return result[0] if result else None

async def get_next_hexes_filtered_by_patron(cell_id, alliance):
    async with aiosqlite.connect(DATABASE_PATH) as db:
        async with db.execute('''
            SELECT e.right_hexagon AS neighbor_id
            FROM edges e
            JOIN map m ON e.right_hexagon = m.id
            WHERE e.left_hexagon = ?
              AND m.patron = ?
            UNION
            SELECT e.left_hexagon AS neighbor_id
            FROM edges e
            JOIN map m ON e.left_hexagon = m.id
            WHERE e.right_hexagon = ?
              AND m.patron = ?
        ''', (cell_id, alliance, cell_id, alliance)) as cursor:
            return await cursor.fetchall()

async def get_nicknamane(telegram_id):
        async with aiosqlite.connect(DATABASE_PATH) as db:
            async with db.execute('SELECT nickname FROM warmasters WHERE telegram_id=?', (telegram_id,)) as cursor:
                result = await cursor.fetchone()
                return result[0] if result else None

async def get_number_of_safe_next_cells(cell_id):
    async with aiosqlite.connect(DATABASE_PATH) as db:
        async with db.execute('''
            SELECT COUNT(*) AS same_patron_neighbors
            FROM edges e
            JOIN map m1 ON (e.left_hexagon = m1.id OR e.right_hexagon = m1.id)
            JOIN map m2 ON (
                (e.left_hexagon = m2.id OR e.right_hexagon = m2.id)
                AND m2.id != m1.id
            )
            WHERE m1.id = ?
              AND m2.patron = m1.patron;
        ''', (cell_id,)) as cursor:
            result = await cursor.fetchone()
            return result[0] if result else 0

async def get_opponent_telegram_id(battle_id, current_user_telegram_id):
    logger.info(
        "get_opponent_telegram_id(battle_id=%s, current_user=%s [type=%s])",
        battle_id, current_user_telegram_id, type(current_user_telegram_id))
    async with aiosqlite.connect(DATABASE_PATH) as db:
        # First try the new battle_attenders table
        async with db.execute('''
            SELECT attender_id
            FROM battle_attenders
            WHERE battle_id = ?
            AND attender_id != ?
        ''', (battle_id, current_user_telegram_id)) as cursor:
            result = await cursor.fetchone()
            logger.info("battle_attenders lookup result: %s", result)
            if result:
                logger.info("Opponent resolved via battle_attenders: %s", result)
                return result
        
        # Fallback to old battles table structure for legacy battles
        async with db.execute('''
            SELECT fstplayer, sndplayer
            FROM battles
            WHERE id = ?
        ''', (battle_id,)) as cursor:
            battle_result = await cursor.fetchone()
            logger.info("legacy battles lookup result: %s", battle_result)
            if battle_result and battle_result[0] and battle_result[1]:
                # If current user is fstplayer, return sndplayer, and vice versa
                if str(battle_result[0]) == str(current_user_telegram_id):
                    logger.info("Opponent resolved via legacy (sndplayer): %s", battle_result[1])
                    return (battle_result[1],)
                elif str(battle_result[1]) == str(current_user_telegram_id):
                    logger.info("Opponent resolved via legacy (fstplayer): %s", battle_result[0])
                    return (battle_result[0],)
            else:
                logger.warning(
                    "Could not resolve opponent from legacy battles for battle_id=%s",
                    battle_id)
        
        logger.error(
            "Opponent telegram id could not be determined for battle_id=%s, user=%s",
            battle_id, current_user_telegram_id)
        return None


async def get_active_battle_id_for_mission(mission_id, user_telegram_id):
    """Get the active battle_id for a mission where user participates.
    
    Args:
        mission_id: The ID of the mission
        user_telegram_id: Telegram ID of the user
        
    Returns:
        int: Battle ID if found, None otherwise
    """
    async with aiosqlite.connect(DATABASE_PATH) as db:
        # First try to find battle with participants in battle_attenders
        async with db.execute('''
            SELECT b.id FROM battles b
            INNER JOIN battle_attenders ba ON b.id = ba.battle_id
            WHERE b.mission_id = ? AND ba.attender_id = ?
            ORDER BY b.id DESC
            LIMIT 1
        ''', (mission_id, user_telegram_id)) as cursor:
            result = await cursor.fetchone()
            if result:
                return result[0]
        
        # Fallback: find latest battle for this mission (for legacy support)
        async with db.execute('''
            SELECT id FROM battles
            WHERE mission_id = ?
            ORDER BY id DESC
            LIMIT 1
        ''', (mission_id,)) as cursor:
            result = await cursor.fetchone()
            return result[0] if result else None


async def get_rules_of_mission(number_of_mission):
    async with aiosqlite.connect(DATABASE_PATH) as db:
        async with db.execute('''
            SELECT rules
            FROM schedule
            WHERE id = ?
        ''', (number_of_mission,)) as cursor:
            result = await cursor.fetchone()
            return result[0] if result else None


async def get_state(cell_id):
    async with aiosqlite.connect(DATABASE_PATH) as db:
        async with db.execute('''
            SELECT state
            FROM map
            WHERE id = ?
        ''', (cell_id,)) as cursor:
            result = await cursor.fetchone()
            return result[0] if result else None

# NOTE: get_mission_details is implemented later with logging and COALESCE.


async def add_battle_result(mission_id, counts1, counts2):
    """Save battle result scores.
    
    Args:
        mission_id: The mission ID
        counts1: First player score (fstplayer score)
        counts2: Second player score (sndplayer score)
    """
    async with aiosqlite.connect(DATABASE_PATH) as db:
        await db.execute('''
            UPDATE battles
            SET fstplayer = ?, sndplayer = ?
            WHERE mission_id = ?
        ''', (counts1, counts2, mission_id))
        await db.commit()


async def add_warmaster(telegram_id):
    async with aiosqlite.connect(DATABASE_PATH) as db:
        await db.execute('''
            INSERT OR IGNORE INTO warmasters(telegram_id) VALUES(?)
        ''', (telegram_id,))
        await db.commit()


async def destroy_warehouse(cell_id):
    async with aiosqlite.connect(DATABASE_PATH) as db:
        await db.execute('''
            UPDATE map SET has_warehouse=0 WHERE id=?
        ''', (cell_id,))
        await db.commit()

async def get_event_participants(eventId):
    async with aiosqlite.connect(DATABASE_PATH) as db:
        async with db.execute('''
            SELECT user_telegram 
            FROM schedule 
            WHERE date = (SELECT date FROM schedule WHERE id = ?) 
            AND rules = (SELECT rules FROM schedule WHERE id = ?)
        ''', (eventId, eventId)) as cursor:
            return await cursor.fetchall()


async def get_faction_of_warmaster(user_telegram_id):
    async with aiosqlite.connect(DATABASE_PATH) as db:
         async with db.execute('''
            SELECT faction
            FROM warmasters
            WHERE telegram_id=?
        ''', (str(user_telegram_id),)) as cursor:
            return await cursor.fetchone()

async def unlock_expired_missions():
    """Unlock all missions with past dates that are still locked.
    
    This function updates all missions where:
    - locked = 1 (mission is locked)
    - created_date is before today (mission is from a past date)
    - created_date is NULL (old missions without date - also unlocked for safety)
    
    Returns:
        int: Number of missions unlocked
    """
    async with aiosqlite.connect(DATABASE_PATH) as db:
        today = datetime.date.today().isoformat()
        cursor = await db.execute('''
            UPDATE mission_stack 
            SET locked=0 
            WHERE locked=1 AND (created_date < ? OR created_date IS NULL)
        ''', (today,))
        await db.commit()
        return cursor.rowcount


async def get_mission(rules) -> Optional[Mission]:
    """Get an unlocked mission by rules.
    
    Args:
        rules: Mission ruleset (killteam, wh40k, etc.)
    
    Returns:
        Mission object or None if no mission found
    """
    # Unlock any expired missions before fetching
    await unlock_expired_missions()
    
    async with aiosqlite.connect(DATABASE_PATH) as db:
        async with db.execute('''
            SELECT id, deploy, rules, cell, mission_description, winner_bonus, locked, created_date
            FROM mission_stack
            WHERE locked=0 AND rules=?
        ''', (rules,)) as cursor:
            row = await cursor.fetchone()
            return Mission.from_db_row(row)

async def get_schedule_by_user(user_telegram, date=None):
    async with aiosqlite.connect(DATABASE_PATH) as db:
        query = 'SELECT * FROM schedule WHERE user_telegram=?'
        params = [user_telegram]
        if date:
            query += ' AND date=?'
            params.append(date)
        async with db.execute(query, params) as cursor:
            return await cursor.fetchall()

async def get_schedule_with_warmasters(user_telegram, date=None):
    """Get schedule with opponent info including their telegram_id.
    
    Returns: List of tuples (schedule_id, rules, opponent_nickname, opponent_telegram_id)
    """
    async with aiosqlite.connect(DATABASE_PATH) as db:
        async with db.execute('''
            SELECT schedule.id, schedule.rules, warmasters.nickname, warmasters.telegram_id
            FROM schedule 
            JOIN warmasters ON schedule.user_telegram=warmasters.telegram_id 
            AND schedule.user_telegram<>? 
            AND schedule.date=?
        ''', (user_telegram, date)) as cursor:
            return await cursor.fetchall()


async def get_user_bookings_for_dates(user_telegram, dates: List[str]) -> Dict[str, str]:
    """Get user's bookings for a list of dates.
    
    Args:
        user_telegram: User's telegram ID
        dates: List of date strings in format YYYY-MM-DD
        
    Returns:
        Dictionary mapping date to rule name for dates where user has bookings
        Example: {'2024-04-27': 'killteam', '2024-04-28': 'wh40k'}
    """
    if not dates:
        return {}
    
    async with aiosqlite.connect(DATABASE_PATH) as db:
        # Create placeholders for the IN clause
        placeholders = ','.join('?' * len(dates))
        async with db.execute(f'''
            SELECT date, rules
            FROM schedule
            WHERE user_telegram = ? AND date IN ({placeholders})
        ''', (user_telegram, *dates)) as cursor:
            results = await cursor.fetchall()
            return {date: rule for date, rule in results}


async def get_settings(telegram_user_id):
    async with aiosqlite.connect(DATABASE_PATH) as db:
        async with db.execute('''
            SELECT nickname, registered_as, language, notifications_enabled FROM warmasters 
            WHERE telegram_id=?
        ''', (telegram_user_id,)) as cursor:
            return await cursor.fetchone()


async def get_warehouses_of_warmaster(telegram_user_id):
    async with aiosqlite.connect(DATABASE_PATH) as db:
        async with db.execute('''
            SELECT id
            FROM map
            WHERE patron = (
                SELECT alliance FROM warmasters WHERE telegram_id = ?
            )
            AND has_warehouse = 1
        ''', (telegram_user_id,)) as cursor:
            return await cursor.fetchall()


async def get_players_for_game(rule, date):
    """Get all players registered for a specific game by rule and date"""
    async with aiosqlite.connect(DATABASE_PATH) as db:
        async with db.execute('''
            SELECT DISTINCT warmasters.telegram_id, warmasters.nickname, warmasters.notifications_enabled
            FROM warmasters
            JOIN schedule ON warmasters.telegram_id = schedule.user_telegram
            WHERE schedule.rules=?
            AND schedule.date=?
        ''', (rule, str(datetime.datetime.strptime(date, "%c").strftime("%Y-%m-%d")))
        ) as cursor:
            return await cursor.fetchall()


async def get_weekly_rule_participant_count(rule: str, week_number: int) -> int:
    """Get count of unique participants for a rule in a specific week.
    
    Args:
        rule: Rule name (e.g., 'killteam', 'wh40k')
        week_number: ISO week number (1-53)
        
    Returns:
        Count of distinct users registered for the rule in that week
    """
    async with aiosqlite.connect(DATABASE_PATH) as db:
        async with db.execute('''
            SELECT COUNT(DISTINCT user_telegram)
            FROM schedule
            WHERE rules = ? AND date_week = ?
        ''', (rule, week_number)) as cursor:
            result = await cursor.fetchone()
            return result[0] if result else 0


async def get_daily_rule_participant_count(rule: str, date: str) -> int:
    """Get count of unique participants for a rule on a specific date.
    
    Args:
        rule: Rule name (e.g., 'killteam', 'wh40k')
        date: Date string in format YYYY-MM-DD
        
    Returns:
        Count of distinct users registered for the rule on that date
    """
    async with aiosqlite.connect(DATABASE_PATH) as db:
        async with db.execute('''
            SELECT COUNT(DISTINCT user_telegram)
            FROM schedule
            WHERE rules = ? AND date = ?
        ''', (rule, date)) as cursor:
            result = await cursor.fetchone()
            return result[0] if result else 0


async def get_weekly_rule_participant_counts(rules: List[str], week_number: int) -> Dict[str, int]:
    """Get counts of unique participants for multiple rules in a specific week.
    
    Batches all rule queries into a single database query for improved performance.
    Only counts dates that are today or in the future.
    
    Args:
        rules: List of rule keys (e.g., ['killteam', 'wh40k', 'combatpatrol'])
        week_number: ISO week number (1-53)
        
    Returns:
        Dictionary mapping rule names to participant counts
        
    Raises:
        ValueError: If rules list is empty
    """
    if not rules:
        raise ValueError("Rules list cannot be empty")
    
    today = datetime.datetime.now().strftime('%Y-%m-%d')
    
    async with aiosqlite.connect(DATABASE_PATH) as db:
        async with db.execute('''
            SELECT rules, COUNT(DISTINCT user_telegram) as count
            FROM schedule
            WHERE rules IN ({}) AND date_week = ? AND date >= ?
            GROUP BY rules
        '''.format(','.join('?' * len(rules))), (*rules, week_number, today)) as cursor:
            results = await cursor.fetchall()
            # Create dictionary with all rules initialized to 0
            counts = {rule: 0 for rule in rules}
            # Update with actual counts from database
            for rule, count in results:
                counts[rule] = count
            return counts


async def get_warmasters_opponents(against_alliance, rule, date):
    async with aiosqlite.connect(DATABASE_PATH) as db:
        async with db.execute('''
            SELECT DISTINCT warmasters.nickname, warmasters.registered_as
            FROM warmasters
            JOIN schedule ON warmasters.telegram_id = schedule.user_telegram
            WHERE warmasters.alliance <> ?
            AND schedule.rules = ?
            AND schedule.date = ?
        ''', (against_alliance[0], rule, 
              str(datetime.datetime.strptime(date, "%c").strftime("%Y-%m-%d")))
        ) as cursor:
            return await cursor.fetchall()


async def get_alliance_of_warmaster(telegram_user_id):
    logger.info(
        "get_alliance_of_warmaster(telegram_id=%s [type=%s])",
        telegram_user_id, type(telegram_user_id))
    async with aiosqlite.connect(DATABASE_PATH) as db:
        async with db.execute('''
            SELECT alliance FROM warmasters WHERE telegram_id=?
        ''', (telegram_user_id,)) as cursor:
            row = await cursor.fetchone()
            logger.info("Alliance lookup result for %s: %s", telegram_user_id, row)
            if row is None:
                logger.error("Alliance not found for telegram_id=%s", telegram_user_id)
            return row


async def insert_to_schedule(date, rules, user_telegram):
    weekNumber = date.isocalendar()[1]
    async with aiosqlite.connect(DATABASE_PATH) as db:
        # Удаляем записи всех пользователей, где разница в неделях больше 1
        await db.execute(
            'DELETE FROM schedule WHERE ABS(date_week - ?) > 1',
            (weekNumber,))
        await db.execute('INSERT INTO schedule (date, rules, user_telegram, date_week) VALUES (?, ?, ?, ?)', (str(date.date()), rules, user_telegram, weekNumber))
        await db.commit()

async def has_route_to_warehouse(start_id, patron):
    async with aiosqlite.connect(DATABASE_PATH) as db:
        async with db.execute("""
            WITH RECURSIVE connected_hexes(id) AS (
                SELECT id FROM map WHERE id = ? AND patron = ?

                UNION

                SELECT
                    CASE
                        WHEN e.left_hexagon = c.id THEN e.right_hexagon
                        ELSE e.left_hexagon
                    END
                FROM edges e
                JOIN connected_hexes c ON e.left_hexagon = c.id
                    OR e.right_hexagon = c.id
                JOIN map m_next ON (
                    (e.left_hexagon = m_next.id OR e.right_hexagon = m_next.id)
                    AND m_next.id != c.id
                )
                WHERE m_next.patron = ?
            )
            SELECT EXISTS (
                SELECT 1
                FROM connected_hexes ch
                JOIN map m ON ch.id = m.id
                WHERE m.has_warehouse = 1
                  AND m.patron = ?
            )
        """, (start_id, patron, patron, patron)) as cursor:
            return await cursor.fetchone()


async def is_warmaster_registered(user_telegram_id):
    return True

async def is_hex_patroned_by(cell_id, participant_telegram):
    async with aiosqlite.connect(DATABASE_PATH) as db:
        async with db.execute(
            '''
            SELECT 1
            FROM map
            JOIN warmasters ON warmasters.alliance = map.patron
            WHERE map.id = ? AND warmasters.telegram_id = ?
            ''',
            (cell_id, participant_telegram)
        ) as cursor:
            return await cursor.fetchone() is not None


async def lock_mission(mission_id):
    async with aiosqlite.connect(DATABASE_PATH) as db:
        await db.execute('''
            UPDATE mission_stack SET locked=1 WHERE id=?
        ''', (mission_id,))
        await db.commit()


async def set_mission_score_submitted(mission_id):
    """Set mission locked status to 2 when battle score is submitted.
    
    Args:
        mission_id: The ID of the mission to update
        
    Returns:
        bool: True if the update was successful, False otherwise
    """
    async with aiosqlite.connect(DATABASE_PATH) as db:
        cursor = await db.execute('''
            UPDATE mission_stack SET locked=2 WHERE id=?
        ''', (mission_id,))
        await db.commit()
        return cursor.rowcount > 0


async def register_warmaster(user_telegram_id, phone):
    async with aiosqlite.connect(DATABASE_PATH) as db:
        await db.execute('''
            UPDATE warmasters SET registered_as=? WHERE telegram_id=?
        ''', (phone, user_telegram_id))
        await db.commit()


async def save_mission(mission):
    async with aiosqlite.connect(DATABASE_PATH) as db:
        today = datetime.date.today().isoformat()
        await db.execute('''
            INSERT INTO mission_stack(deploy, rules, cell,
                                     mission_description, winner_bonus, locked, created_date)
            VALUES(?, ?, ?, ?, ?, 0, ?)
        ''', (mission[0], mission[1], mission[2], mission[3], mission[4] if len(mission) > 4 else None, today))
        await db.commit()


async def set_nickname(user_telegram_id, nickname):
    async with aiosqlite.connect(DATABASE_PATH) as db:
        await db.execute('''
            UPDATE warmasters SET nickname=? WHERE telegram_id=?
        ''', (nickname, user_telegram_id))
        await db.commit()


async def set_language(user_telegram_id, language):
    async with aiosqlite.connect(DATABASE_PATH) as db:
        # First, try to update existing record
        cursor = await db.execute('''
            UPDATE warmasters SET language=? WHERE telegram_id=?
        ''', (language, user_telegram_id))
        
        # If no rows were affected, insert new record
        if cursor.rowcount == 0:
            await db.execute('''
                INSERT OR IGNORE INTO warmasters (telegram_id, language) 
                VALUES (?, ?)
            ''', (user_telegram_id, language))
        
        await db.commit()


async def toggle_notifications(user_telegram_id):
    async with aiosqlite.connect(DATABASE_PATH) as db:
        async with db.execute('''
            SELECT notifications_enabled FROM warmasters WHERE telegram_id=?
        ''', (user_telegram_id,)) as cursor:
            result = await cursor.fetchone()
            current_value = result[0] if result else 1
        
        new_value = 0 if current_value == 1 else 1
        await db.execute('''
            UPDATE warmasters SET notifications_enabled=? WHERE telegram_id=?
        ''', (new_value, user_telegram_id))
        await db.commit()
        return new_value

async def _update_alliance_resource(alliance_id, change_amount):
    """Helper function to update alliance resources.
    
    Args:
        alliance_id: The ID of the alliance
        change_amount: Positive to increase, negative to decrease
        
    Returns:
        The new resource value
    """
    async with aiosqlite.connect(DATABASE_PATH) as db:
        # Get the current resource value
        async with db.execute('''
            SELECT common_resource FROM alliances WHERE id = ?
        ''', (alliance_id,)) as cursor:
            result = await cursor.fetchone()
            current_value = result[0] if result else 0
        
        # Calculate new value (ensure it doesn't go below 0)
        new_value = max(0, current_value + change_amount)
        
        # Update the database
        await db.execute('''
            UPDATE alliances SET common_resource = ? WHERE id = ?
        ''', (new_value, alliance_id))
        await db.commit()
        
        return new_value

async def increase_common_resource(alliance_id, amount=1):
    """Increase the common resource of an alliance.
    
    Args:
        alliance_id: The ID of the alliance
        amount: The amount to increase (default: 1)
        
    Returns:
        The new resource value
    """
    return await _update_alliance_resource(alliance_id, amount)

async def decrease_common_resource(alliance_id, amount=1):
    """Decrease the common resource of an alliance.
    
    Args:
        alliance_id: The ID of the alliance
        amount: The amount to decrease (default: 1)
        
    Returns:
        The new resource value
    """
    return await _update_alliance_resource(alliance_id, -amount)

async def create_warehouse(cell_id):
    """Создает склад в указанном гексе."""
    async with aiosqlite.connect(DATABASE_PATH) as db:
        await db.execute('''
            UPDATE map SET has_warehouse=1 WHERE id=?
        ''', (cell_id,))
        await db.commit()


async def has_warehouse_in_hex(cell_id):
    """Проверяет, есть ли склад в указанном гексе."""
    async with aiosqlite.connect(DATABASE_PATH) as db:
        async with db.execute('''
            SELECT has_warehouse FROM map WHERE id=?
        ''', (cell_id,)) as cursor:
            result = await cursor.fetchone()
            return result[0] == 1 if result else False


async def get_hexes_by_alliance(alliance_id):
    """Получает все гексы, контролируемые указанным альянсом."""
    async with aiosqlite.connect(DATABASE_PATH) as db:
        async with db.execute('''
            SELECT id FROM map WHERE patron=?
        ''', (alliance_id,)) as cursor:
            return await cursor.fetchall()


async def get_adjacent_hexes_between_alliances(alliance1_id, alliance2_id):
    """Find hexes of alliance2 that are adjacent to alliance1 hexes.
    
    Returns hexes of alliance2 (defender) that share edges with hexes of alliance1 (attacker).
    
    Args:
        alliance1_id: Attacker alliance ID
        alliance2_id: Defender alliance ID
        
    Returns:
        List of tuples containing defender hex IDs adjacent to attacker hexes
    """
    async with aiosqlite.connect(DATABASE_PATH) as db:
        async with db.execute('''
            SELECT DISTINCT m2.id
            FROM edges e
            JOIN map m1 ON (m1.id = e.left_hexagon OR m1.id = e.right_hexagon)
            JOIN map m2 ON (m2.id = e.left_hexagon OR m2.id = e.right_hexagon)
            WHERE m1.patron = ? 
              AND m2.patron = ? 
              AND m1.id != m2.id
        ''', (alliance1_id, alliance2_id)) as cursor:
            return await cursor.fetchall()


async def update_mission_cell(mission_id, cell_id):
    """Update the cell field for a mission."""
    async with aiosqlite.connect(DATABASE_PATH) as db:
        await db.execute('''
            UPDATE mission_stack SET cell=? WHERE id=?
        ''', (cell_id, mission_id))
        await db.commit()


async def has_adjacent_cell_to_hex(alliance_id, cell_id):
    """Check if an alliance has any cell adjacent to a specific hex.
    
    Args:
        alliance_id: Alliance ID to check
        cell_id: Target cell ID
        
    Returns:
        bool: True if alliance has at least one cell adjacent to the target cell
    """
    async with aiosqlite.connect(DATABASE_PATH) as db:
        async with db.execute('''
            SELECT COUNT(*) FROM (
                SELECT e.right_hexagon AS neighbor_id
                FROM edges e
                JOIN map m ON e.right_hexagon = m.id
                WHERE e.left_hexagon = ?
                  AND m.patron = ?
                UNION
                SELECT e.left_hexagon AS neighbor_id
                FROM edges e
                JOIN map m ON e.left_hexagon = m.id
                WHERE e.right_hexagon = ?
                  AND m.patron = ?
            )
        ''', (cell_id, alliance_id, cell_id, alliance_id)) as cursor:
            result = await cursor.fetchone()
            return result[0] > 0 if result else False


async def get_warehouse_count_by_alliance(alliance_id):
    """Get the number of warehouses owned by an alliance.

    Uses warehouses table if present; falls back to map.has_warehouse.
    """
    async with aiosqlite.connect(DATABASE_PATH) as db:
        try:
            async with db.execute('''
                SELECT COUNT(*) FROM warehouses WHERE alliance_id = ?
            ''', (alliance_id,)) as cursor:
                result = await cursor.fetchone()
                return result[0] if result else 0
        except Exception:
            async with db.execute('''
                SELECT COUNT(*) FROM map WHERE patron=? AND has_warehouse=1
            ''', (alliance_id,)) as cursor:
                result = await cursor.fetchone()
                return result[0] if result else 0


async def get_mission_id_by_battle_id(battle_id):
    """Get the mission ID associated with a battle."""
    async with aiosqlite.connect(DATABASE_PATH) as db:
        async with db.execute('''
            SELECT mission_id FROM battles WHERE id = ?
        ''', (battle_id,)) as cursor:
            result = await cursor.fetchone()
            return result[0] if result else None


async def get_mission_details(mission_id) -> Optional[Mission]:
    """Get mission details by mission ID.

    Args:
        mission_id: The mission ID
    
    Returns:
        Mission object or None if not found
    """
    logger.info("get_mission_details(mission_id=%s)", mission_id)
    async with aiosqlite.connect(DATABASE_PATH) as db:
        async with db.execute('''
            SELECT id, deploy, rules, cell, mission_description, winner_bonus, locked, created_date
            FROM mission_stack WHERE id = ?
        ''', (mission_id,)) as cursor:
            row = await cursor.fetchone()
            mission = Mission.from_db_row(row)
            logger.info("mission_details result: %s", mission)
            return mission


async def get_winner_bonus(mission_id):
    """Get winner bonus for a mission by mission ID (secret until battle ends)."""
    async with aiosqlite.connect(DATABASE_PATH) as db:
        async with db.execute('''
            SELECT winner_bonus FROM mission_stack WHERE id = ?
        ''', (mission_id,)) as cursor:
            result = await cursor.fetchone()
            return result[0] if result else None


async def get_alliance_resources(alliance_id):
    """Get the current resource amount for an alliance.
    
    Args:
        alliance_id: The ID of the alliance
        
    Returns:
        The current resource amount (integer)
    """
    async with aiosqlite.connect(DATABASE_PATH) as db:
        async with db.execute('''
            SELECT common_resource FROM alliances WHERE id = ?
        ''', (alliance_id,)) as cursor:
            result = await cursor.fetchone()
            return result[0] if result else 0


async def destroy_warehouse_by_alliance(alliance_id):
    """Destroy one warehouse owned by the specified alliance.
    
    Args:
        alliance_id: The ID of the alliance whose warehouse should be destroyed
        
    Returns:
        True if a warehouse was destroyed, False if no warehouse was found
    """
    async with aiosqlite.connect(DATABASE_PATH) as db:
        # Find and delete one warehouse owned by the alliance
        # Assuming there's a warehouses table with cell_id and alliance_id
        async with db.execute('''
            SELECT cell_id FROM warehouses 
            WHERE alliance_id = ? 
            LIMIT 1
        ''', (alliance_id,)) as cursor:
            result = await cursor.fetchone()
            
        if result:
            cell_id = result[0]
            await db.execute('''
                DELETE FROM warehouses 
                WHERE cell_id = ? AND alliance_id = ?
            ''', (cell_id, alliance_id))
            await db.commit()
            return True
        return False


async def get_warehouse_count_by_alliance(alliance_id):
    """Get the number of warehouses owned by an alliance.
    
    Args:
        alliance_id: The ID of the alliance
        
    Returns:
        The number of warehouses owned by the alliance
    """
    async with aiosqlite.connect(DATABASE_PATH) as db:
        async with db.execute('''
            SELECT COUNT(*) FROM warehouses WHERE alliance_id = ?
        ''', (alliance_id,)) as cursor:
            result = await cursor.fetchone()
            return result[0] if result else 0


async def get_text_by_key(key, language='ru'):
    """Get localized text by key and language."""
    async with aiosqlite.connect(DATABASE_PATH) as db:
        async with db.execute('''
            SELECT value FROM texts WHERE key = ? AND language = ?
        ''', (key, language)) as cursor:
            result = await cursor.fetchone()
            return result[0] if result else None


async def add_or_update_text(key, language, value):
    """Add or update a text entry."""
    async with aiosqlite.connect(DATABASE_PATH) as db:
        await db.execute('''
            INSERT OR REPLACE INTO texts (key, language, value)
            VALUES (?, ?, ?)
        ''', (key, language, value))
        await db.commit()


async def get_all_texts_for_language(language='ru'):
    """Get all texts for a specific language."""
    async with aiosqlite.connect(DATABASE_PATH) as db:
        async with db.execute('''
            SELECT key, value FROM texts WHERE language = ?
        ''', (language,)) as cursor:
            return await cursor.fetchall()


async def is_user_admin(user_telegram_id):
    """Check if a user is an admin.
    
    Args:
        user_telegram_id: Telegram user ID
        
    Returns:
        bool: True if user is admin, False otherwise
    """
    async with aiosqlite.connect(DATABASE_PATH) as db:
        async with db.execute('''
            SELECT is_admin FROM warmasters WHERE telegram_id = ?
        ''', (user_telegram_id,)) as cursor:
            result = await cursor.fetchone()
            return result[0] == 1 if result else False


async def make_user_admin(user_telegram_id):
    """Make a user an admin.
    
    Args:
        user_telegram_id: Telegram user ID
    """
    async with aiosqlite.connect(DATABASE_PATH) as db:
        await db.execute('''
            UPDATE warmasters SET is_admin = 1 WHERE telegram_id = ?
        ''', (user_telegram_id,))
        await db.commit()


async def get_warmasters_with_nicknames():
    """Get all warmasters who have set nicknames.
    
    Returns:
        List of tuples: [(telegram_id, nickname, alliance), ...]
    """
    async with aiosqlite.connect(DATABASE_PATH) as db:
        async with db.execute('''
            SELECT telegram_id, nickname, alliance FROM warmasters 
            WHERE nickname IS NOT NULL AND nickname != ''
            ORDER BY nickname
        ''') as cursor:
            return await cursor.fetchall()


async def get_all_alliances():
    """Get all alliances with their IDs and names.
    
    Returns:
        List of tuples: [(id, name), ...]
    """
    async with aiosqlite.connect(DATABASE_PATH) as db:
        async with db.execute('''
            SELECT id, name FROM alliances ORDER BY id
        ''') as cursor:
            return await cursor.fetchall()


async def get_alliance_player_count(alliance_id):
    """Get the number of players in an alliance.
    
    Args:
        alliance_id: Alliance ID
        
    Returns:
        int: Number of players in the alliance
    """
    async with aiosqlite.connect(DATABASE_PATH) as db:
        async with db.execute('''
            SELECT COUNT(*) FROM warmasters WHERE alliance = ?
        ''', (alliance_id,)) as cursor:
            result = await cursor.fetchone()
            return result[0] if result else 0


async def get_alliance_territory_count(alliance_id):
    """Get the number of territories (map cells) controlled by an alliance.
    
    Args:
        alliance_id: Alliance ID
        
    Returns:
        int: Number of territories controlled by the alliance
    """
    async with aiosqlite.connect(DATABASE_PATH) as db:
        async with db.execute('''
            SELECT COUNT(*) FROM map WHERE patron = ?
        ''', (alliance_id,)) as cursor:
            result = await cursor.fetchone()
            return result[0] if result else 0


async def get_dominant_alliance():
    """Get the alliance with the most territories (cells) on the map.
    
    Returns:
        int or None: Alliance ID with most territories, or None if no alliances have territories
    """
    async with aiosqlite.connect(DATABASE_PATH) as db:
        async with db.execute('''
            SELECT patron, COUNT(*) as cell_count
            FROM map
            WHERE patron != 0
            GROUP BY patron
            ORDER BY cell_count DESC
            LIMIT 1
        ''') as cursor:
            result = await cursor.fetchone()
            return result[0] if result else None


async def set_warmaster_alliance(user_telegram_id, alliance_id):
    """Set a warmaster's alliance.
    
    Args:
        user_telegram_id: Telegram user ID
        alliance_id: Alliance ID to assign
    """
    async with aiosqlite.connect(DATABASE_PATH) as db:
        await db.execute('''
            UPDATE warmasters SET alliance = ? WHERE telegram_id = ?
        ''', (alliance_id, user_telegram_id))
        await db.commit()


async def create_alliance(name, initial_resources=0):
    """Create a new alliance.
    
    Args:
        name: Alliance name (max 50 characters)
        initial_resources: Starting resources (default: 0)
        
    Returns:
        int: ID of created alliance or None if name exists
        
    Raises:
        ValueError: If name is invalid
    """
    import html
    import re
    
    # Validate name
    if not name or not isinstance(name, str):
        raise ValueError("Alliance name must be a non-empty string")
    
    # Escape HTML and limit length
    name = html.escape(name.strip())
    if len(name) > 50:
        raise ValueError("Alliance name must be 50 characters or less")
    
    # Check for valid characters (letters, numbers, spaces, basic punctuation)
    if not re.match(r'^[a-zA-Zа-яА-Я0-9\s\-_\.\!\?]+$', name):
        raise ValueError("Alliance name contains invalid characters")
    
    async with aiosqlite.connect(DATABASE_PATH) as db:
        # Check if name already exists
        async with db.execute('''
            SELECT id FROM alliances WHERE name = ?
        ''', (name,)) as cursor:
            if await cursor.fetchone():
                return None  # Name already exists
        
        # Create alliance
        await db.execute('''
            INSERT INTO alliances (name, common_resource) VALUES (?, ?)
        ''', (name, initial_resources))
        await db.commit()
        
        # Return new alliance ID
        async with db.execute('SELECT last_insert_rowid()') as cursor:
            result = await cursor.fetchone()
            return result[0] if result else None


async def get_alliance_by_name(name):
    """Get alliance by name.
    
    Args:
        name: Alliance name
        
    Returns:
        tuple: (id, name, common_resource) or None if not found
    """
    async with aiosqlite.connect(DATABASE_PATH) as db:
        async with db.execute('''
            SELECT id, name, common_resource FROM alliances WHERE name = ?
        ''', (name,)) as cursor:
            return await cursor.fetchone()


async def get_alliance_by_id(alliance_id):
    """Get alliance by ID.
    
    Args:
        alliance_id: Alliance ID
        
    Returns:
        tuple: (id, name, common_resource) or None if not found
    """
    async with aiosqlite.connect(DATABASE_PATH) as db:
        async with db.execute('''
            SELECT id, name, common_resource FROM alliances WHERE id = ?
        ''', (alliance_id,)) as cursor:
            return await cursor.fetchone()


async def update_alliance_name(alliance_id, new_name):
    """Update alliance name.
    
    Args:
        alliance_id: Alliance ID
        new_name: New alliance name (max 50 characters)
        
    Returns:
        bool: True if updated, False if name exists or alliance not found
        
    Raises:
        ValueError: If name is invalid
    """
    import html
    import re
    
    # Validate name
    if not new_name or not isinstance(new_name, str):
        raise ValueError("Alliance name must be a non-empty string")
    
    # Escape HTML and limit length
    new_name = html.escape(new_name.strip())
    if len(new_name) > 50:
        raise ValueError("Alliance name must be 50 characters or less")
    
    # Check for valid characters
    if not re.match(r'^[a-zA-Zа-яА-Я0-9\s\-_\.\!\?]+$', new_name):
        raise ValueError("Alliance name contains invalid characters")
    
    async with aiosqlite.connect(DATABASE_PATH) as db:
        # Check if new name already exists (excluding current alliance)
        async with db.execute('''
            SELECT id FROM alliances WHERE name = ? AND id != ?
        ''', (new_name, alliance_id)) as cursor:
            if await cursor.fetchone():
                return False  # Name already exists
        
        # Check if alliance exists
        async with db.execute('''
            SELECT id FROM alliances WHERE id = ?
        ''', (alliance_id,)) as cursor:
            if not await cursor.fetchone():
                return False  # Alliance not found
        
        # Update name
        await db.execute('''
            UPDATE alliances SET name = ? WHERE id = ?
        ''', (new_name, alliance_id))
        await db.commit()
        return True


async def redistribute_territories_from_alliance(alliance_id):
    """Redistribute territories (map hexes) from alliance to remaining alliances evenly.
    
    Args:
        alliance_id: Alliance ID to redistribute territories from
        
    Returns:
        int: Number of territories redistributed
    """
    async with aiosqlite.connect(DATABASE_PATH) as db:
        # Get territories from the alliance to delete
        async with db.execute('''
            SELECT id FROM map WHERE patron = ?
        ''', (alliance_id,)) as cursor:
            territory_rows = await cursor.fetchall()
            territories_to_redistribute = [row[0] for row in territory_rows]
        
        if not territories_to_redistribute:
            return 0
        
        # Get remaining alliances with their territory counts
        async with db.execute('''
            SELECT a.id, COUNT(m.id) as territory_count
            FROM alliances a
            LEFT JOIN map m ON a.id = m.patron
            WHERE a.id != ?
            GROUP BY a.id
            ORDER BY territory_count ASC, a.id ASC
        ''', (alliance_id,)) as cursor:
            alliance_rows = await cursor.fetchall()
            # Convert to list of tuples for manipulation
            remaining_alliances = [(row[0], row[1]) for row in alliance_rows]
        
        if not remaining_alliances:
            # No other alliances, set territories to no patron (NULL)
            await db.execute('''
                UPDATE map SET patron = NULL WHERE patron = ?
            ''', (alliance_id,))
            await db.commit()
            return len(territories_to_redistribute)
        
        # Build assignment map for batch update
        territory_assignments = []
        for territory_id in territories_to_redistribute:
            # Find alliance with minimum territories (random choice if tie)
            min_count = remaining_alliances[0][1]
            min_alliances = [alliance for alliance in remaining_alliances if alliance[1] == min_count]
            target_alliance = random.choice(min_alliances)
            
            territory_assignments.append((target_alliance[0], territory_id))
            
            # Update counts in tracking list
            for i, alliance in enumerate(remaining_alliances):
                if alliance[0] == target_alliance[0]:
                    remaining_alliances[i] = (alliance[0], alliance[1] + 1)
                    break
            
            # Re-sort by territory count
            remaining_alliances.sort(key=lambda x: (x[1], x[0]))
        
        # Batch update all territories
        await db.executemany('''
            UPDATE map SET patron = ? WHERE id = ?
        ''', territory_assignments)
        
        await db.commit()
        return len(territories_to_redistribute)


async def redistribute_players_from_alliance(alliance_id):
    """Redistribute players from alliance to remaining alliances evenly.
    
    Args:
        alliance_id: Alliance ID to redistribute players from
        
    Returns:
        int: Number of players redistributed
    """
    async with aiosqlite.connect(DATABASE_PATH) as db:
        # Get players from the alliance to delete
        async with db.execute('''
            SELECT telegram_id FROM warmasters WHERE alliance = ?
        ''', (alliance_id,)) as cursor:
            player_rows = await cursor.fetchall()
            players_to_move = [row[0] for row in player_rows]
        
        if not players_to_move:
            return 0
        
        # Get remaining alliances with their player counts
        async with db.execute('''
            SELECT a.id, COUNT(w.telegram_id) as player_count
            FROM alliances a
            LEFT JOIN warmasters w ON a.id = w.alliance
            WHERE a.id != ?
            GROUP BY a.id
            ORDER BY player_count ASC, a.id ASC
        ''', (alliance_id,)) as cursor:
            alliance_rows = await cursor.fetchall()
            # Convert to list of tuples for manipulation
            remaining_alliances = [(row[0], row[1]) for row in alliance_rows]
        
        if not remaining_alliances:
            # No other alliances, set players to no alliance (0)
            await db.execute('''
                UPDATE warmasters SET alliance = 0 WHERE alliance = ?
            ''', (alliance_id,))
            await db.commit()
            return len(players_to_move)
        
        # Build assignment map for batch update
        player_assignments = []
        for player_id in players_to_move:
            # Find alliance with minimum players (random choice if tie)
            min_count = remaining_alliances[0][1]
            min_alliances = [alliance for alliance in remaining_alliances if alliance[1] == min_count]
            target_alliance = random.choice(min_alliances)
            
            player_assignments.append((target_alliance[0], player_id))
            
            # Update counts in tracking list
            for i, alliance in enumerate(remaining_alliances):
                if alliance[0] == target_alliance[0]:
                    remaining_alliances[i] = (alliance[0], alliance[1] + 1)
                    break
            
            # Re-sort by player count
            remaining_alliances.sort(key=lambda x: (x[1], x[0]))
        
        # Batch update all players
        await db.executemany('''
            UPDATE warmasters SET alliance = ? WHERE telegram_id = ?
        ''', player_assignments)
        
        await db.commit()
        return len(players_to_move)


async def delete_alliance(alliance_id):
    """Delete an alliance and redistribute its players and territories.
    
    Args:
        alliance_id: Alliance ID to delete
        
    Returns:
        dict: {
            'success': bool,
            'players_redistributed': int,
            'territories_redistributed': int,
            'message': str
        }
    """
    async with aiosqlite.connect(DATABASE_PATH) as db:
        # Check if alliance exists
        async with db.execute('''
            SELECT name FROM alliances WHERE id = ?
        ''', (alliance_id,)) as cursor:
            alliance = await cursor.fetchone()
        
        if not alliance:
            return {
                'success': False,
                'players_redistributed': 0,
                'territories_redistributed': 0,
                'message': 'Alliance not found'
            }
        
        alliance_name = alliance[0]
        
        # Check if this is the last alliance
        async with db.execute('SELECT COUNT(*) FROM alliances') as cursor:
            count_result = await cursor.fetchone()
            total_alliances = count_result[0] if count_result else 0
        
        if total_alliances <= 1:
            return {
                'success': False,
                'players_redistributed': 0,
                'territories_redistributed': 0,
                'message': 'Cannot delete the last alliance'
            }
        
        # Redistribute territories first to ensure they go to alliances that currently exist
        territories_moved = await redistribute_territories_from_alliance(alliance_id)
        
        # Redistribute players
        players_moved = await redistribute_players_from_alliance(alliance_id)
        
        # Delete alliance
        await db.execute('''
            DELETE FROM alliances WHERE id = ?
        ''', (alliance_id,))
        
        await db.commit()
        
        return {
            'success': True,
            'players_redistributed': players_moved,
            'territories_redistributed': territories_moved,
            'message': f'Alliance "{alliance_name}" deleted, {players_moved} players and {territories_moved} territories redistributed'
        }


async def check_and_clean_empty_alliances():
    """Check for alliances with 0 members and automatically delete them.
    
    This function finds all alliances that have no members and deletes them,
    redistributing their territories to remaining alliances.
    
    Returns:
        list: List of deletion results for each empty alliance deleted
    """
    async with aiosqlite.connect(DATABASE_PATH) as db:
        # Find alliances with 0 members
        async with db.execute('''
            SELECT a.id, a.name, COUNT(w.telegram_id) as member_count
            FROM alliances a
            LEFT JOIN warmasters w ON a.id = w.alliance
            GROUP BY a.id, a.name
            HAVING member_count = 0
        ''') as cursor:
            empty_alliances = await cursor.fetchall()
    
    results = []
    for alliance_id, alliance_name, _ in empty_alliances:
        result = await delete_alliance(alliance_id)
        results.append({
            'alliance_id': alliance_id,
            'alliance_name': alliance_name,
            'result': result
        })
    
    return results


async def get_active_alliances_count():
    """Get the count of active alliances."""
    async with aiosqlite.connect(DATABASE_PATH) as db:
        async with db.execute('''
            SELECT COUNT(*) FROM alliances
        ''') as cursor:
            result = await cursor.fetchone()
            return result[0] if result else 0


async def clear_alliance_members(alliance_id):
    """Clear alliance membership for all players in the alliance."""
    async with aiosqlite.connect(DATABASE_PATH) as db:
        await db.execute('''
            UPDATE warmasters SET alliance = 0 WHERE alliance = ?
        ''', (alliance_id,))
        await db.commit()


async def get_players_by_alliance(alliance_id):
    """Get all players in a specific alliance."""
    async with aiosqlite.connect(DATABASE_PATH) as db:
        async with db.execute('''
            SELECT telegram_id, nickname, alliance FROM warmasters 
            WHERE alliance = ?
        ''', (alliance_id,)) as cursor:
            return await cursor.fetchall()


async def get_all_players():
    """Get all registered players."""
    async with aiosqlite.connect(DATABASE_PATH) as db:
        async with db.execute('''
            SELECT telegram_id, nickname, alliance FROM warmasters
        ''') as cursor:
            return await cursor.fetchall()

