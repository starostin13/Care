"""Helper functions for interacting with the SQLite database asynchronously
using aiosqlite."""

import datetime
import aiosqlite

DATABASE_PATH = (r"C:\Users\al-gerasimov\source\repos\Care\CareBot\CareBot"
                 r"\db\database")


async def add_battle_participant(battle_id, participant):
    async with aiosqlite.connect(DATABASE_PATH) as db:
        await db.execute('''
            INSERT INTO battle_attenders(battle_id, attender_id)
            VALUES(?, ?)
        ''', (battle_id, participant))
        await db.commit()


async def add_battle(mission_id):
    async with aiosqlite.connect(DATABASE_PATH) as db:
        await db.execute('''
            INSERT INTO battles(mission_id) VALUES(?)
        ''', (mission_id,))
        await db.commit()
        async with db.execute('SELECT last_insert_rowid()') as cursor:
            return await cursor.fetchone()


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
    async with aiosqlite.connect(DATABASE_PATH) as db:
        async with db.execute('''
            SELECT attender_id
            FROM battle_attenders
            WHERE battle_id = ?
            AND attender_id != ?
        ''', (battle_id, current_user_telegram_id)) as cursor:
            return await cursor.fetchone()


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


async def add_battle_result(mission_id, counts1, counts2):
    async with aiosqlite.connect(DATABASE_PATH) as db:
        await db.execute('''
            INSERT INTO battles(mission_id, fstplayer, sndplayer)
            VALUES(?, ?, ?)
        ''', (mission_id, counts1, counts2))
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

async def get_mission(rules):
    async with aiosqlite.connect(DATABASE_PATH) as db:
        async with db.execute('''
            SELECT * FROM mission_stack
            WHERE locked=0 AND rules=?
        ''', (rules,)) as cursor:
            return await cursor.fetchone()

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
    async with aiosqlite.connect(DATABASE_PATH) as db:
        async with db.execute('''
            SELECT schedule.id, schedule.rules, warmasters.nickname 
            FROM schedule 
            JOIN warmasters ON schedule.user_telegram=warmasters.telegram_id 
            AND schedule.user_telegram<>? 
            AND schedule.date=?
        ''', (user_telegram, date)) as cursor:
            return await cursor.fetchall()


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


async def get_warmasters_opponents(against_alliance, rule, date):
    async with aiosqlite.connect(DATABASE_PATH) as db:
        async with db.execute('''
            SELECT DISTINCT nickname, registered_as
            FROM warmasters
            JOIN schedule ON warmasters.alliance<>?
            WHERE rules=?
            AND date=?
        ''', (against_alliance[0], rule, 
              str(datetime.datetime.strptime(date, "%c").strftime("%Y-%m-%d")))
        ) as cursor:
            return await cursor.fetchall()


async def get_alliance_of_warmaster(telegram_user_id):
    async with aiosqlite.connect(DATABASE_PATH) as db:
        async with db.execute('''
            SELECT alliance FROM warmasters WHERE telegram_id=?
        ''', (telegram_user_id,)) as cursor:
            return await cursor.fetchone()


async def insert_to_schedule(date, rules, user_telegram):
    weekNumber = date.isocalendar()[1]
    async with aiosqlite.connect(DATABASE_PATH) as db:
        await db.execute('DELETE FROM schedule WHERE date_week<>?', (weekNumber,))
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


async def register_warmaster(user_telegram_id, phone):
    async with aiosqlite.connect(DATABASE_PATH) as db:
        await db.execute('''
            UPDATE warmasters SET registered_as=? WHERE telegram_id=?
        ''', (phone, user_telegram_id))
        await db.commit()


async def save_mission(mission):
    async with aiosqlite.connect(DATABASE_PATH) as db:
        await db.execute('''
            INSERT INTO mission_stack(deploy, rules, cell,
                                     mission_description, locked)
            VALUES(?, ?, ?, ?, 1)
        ''', (mission[0], mission[1], mission[2], mission[3]))
        await db.commit()


async def set_nickname(user_telegram_id, nickname):
    async with aiosqlite.connect(DATABASE_PATH) as db:
        await db.execute('''
            UPDATE warmasters SET nickname=? WHERE telegram_id=?
        ''', (nickname, user_telegram_id))
        await db.commit()


async def set_language(user_telegram_id, language):
    async with aiosqlite.connect(DATABASE_PATH) as db:
        await db.execute('''
            UPDATE warmasters SET language=? WHERE telegram_id=?
        ''', (language, user_telegram_id))
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


async def get_warehouse_count_by_alliance(alliance_id):
    """Получает количество складов, контролируемых указанным альянсом."""
    async with aiosqlite.connect(DATABASE_PATH) as db:
        async with db.execute('''
            SELECT COUNT(*) FROM map
            WHERE patron=? AND has_warehouse=1
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


async def get_mission_details(mission_id):
    """Get mission details by mission ID."""
    async with aiosqlite.connect(DATABASE_PATH) as db:
        async with db.execute('''
            SELECT deploy, rules, cell, mission_description
            FROM mission_stack WHERE id = ?
        ''', (mission_id,)) as cursor:
            return await cursor.fetchone()


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
