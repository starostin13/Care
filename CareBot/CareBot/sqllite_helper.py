import datetime
import aiosqlite
from xmlrpc.client import DateTime

DATABASE_PATH = r"C:\Users\al-gerasimov\source\repos\Care\CareBot\CareBot\db\database"

async def add_battle_participant(battle_id, participant):
    async with aiosqlite.connect(DATABASE_PATH) as db:
        await db.execute('INSERT INTO battle_attenders(battle_id, attender_id) VALUES(?, ?)', (battle_id, participant))
        await db.commit()

async def add_battle(mission_id):
    async with aiosqlite.connect(DATABASE_PATH) as db:
        await db.execute('INSERT INTO battles(mission_id) VALUES(?)', (mission_id,))
        await db.commit()
        async with db.execute('SELECT last_insert_rowid()') as cursor:
            return await cursor.fetchone()

async def add_to_story(cell_id, text):
    async with aiosqlite.connect(DATABASE_PATH) as db:
        await db.execute('INSERT OR IGNORE INTO map_story(hex_id, content) VALUES(?,?)', (cell_id, text))
        await db.commit()

async def set_cell_patron(cell_id, winner_alliance_id):
    async with aiosqlite.connect(DATABASE_PATH) as db:
        await db.execute('UPDATE map SET patron=? WHERE id=?', (winner_alliance_id, cell_id))
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

async def get_opponent_telegram_id(battle_id, current_user_telegram_id):
    async with aiosqlite.connect(DATABASE_PATH) as db:
        async with db.execute('''
            SELECT attender_id 
            FROM battle_attenders 
            WHERE battle_id = ? 
            AND attender_id != ?
        ''', (battle_id, current_user_telegram_id)) as cursor:
            return await cursor.fetchone()

async def add_battle_result(mission_id, counts1, counts2):
    async with aiosqlite.connect(DATABASE_PATH) as db:
        await db.execute('INSERT INTO battles(mission_id, fstplayer, sndplayer) VALUES(?, ?, ?)', (mission_id, counts1, counts2))
        await db.commit()

async def add_warmaster(telegram_id):
    async with aiosqlite.connect(DATABASE_PATH) as db:
        await db.execute('INSERT OR IGNORE INTO warmasters(telegram_id) VALUES(?)', (telegram_id,))
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
            WHERE telegram_id = ?
        ''', (str(user_telegram_id),)) as cursor:
              return await cursor.fetchone()

async def get_mission():
    async with aiosqlite.connect(DATABASE_PATH) as db:
        async with db.execute('SELECT * FROM mission_stack') as cursor:
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
        async with db.execute('SELECT nickname, registered_as FROM warmasters WHERE telegram_id=?', (telegram_user_id,)) as cursor:
            return await cursor.fetchone()

async def get_warmasters_opponents(against_alliance, rule, date):
    async with aiosqlite.connect(DATABASE_PATH) as db:
        async with db.execute('''
            SELECT DISTINCT nickname, registered_as 
            FROM warmasters 
            JOIN schedule ON warmasters.alliance<>? 
            WHERE rules=? 
            AND date=?
        ''', (against_alliance[0], rule, str(datetime.datetime.strptime(date, "%c").strftime("%Y-%m-%d")))) as cursor:
            return await cursor.fetchall()

async def get_alliance_of_warmaster(telegram_user_id):
    async with aiosqlite.connect(DATABASE_PATH) as db:
        async with db.execute('SELECT alliance FROM warmasters WHERE telegram_id=?', (telegram_user_id,)) as cursor:
            return await cursor.fetchone()

async def insert_to_schedule(date, rules, user_telegram):
    weekNumber = date.isocalendar()[1]
    async with aiosqlite.connect(DATABASE_PATH) as db:
        await db.execute('DELETE FROM schedule WHERE date_week<>?', (weekNumber,))
        await db.execute('INSERT INTO schedule (date, rules, user_telegram, date_week) VALUES (?, ?, ?, ?)', (str(date.date()), rules, user_telegram, weekNumber))
        await db.commit()

async def is_warmaster_registered(user_telegram_id):
    return True

async def lock_mission(mission_id):
    async with aiosqlite.connect(DATABASE_PATH) as db:
        await db.execute('UPDATE mission_stack SET locked=1 WHERE id=?', (mission_id,))
        await db.commit()

async def register_warmaster(user_telegram_id, phone):
    async with aiosqlite.connect(DATABASE_PATH) as db:
        await db.execute('UPDATE warmasters SET registered_as=? WHERE telegram_id=?', (phone, user_telegram_id))
        await db.commit()

async def set_nickname(user_telegram_id, nickname):
    async with aiosqlite.connect(DATABASE_PATH) as db:
        await db.execute('UPDATE warmasters SET nickname=? WHERE telegram_id=?', (nickname, user_telegram_id))
        await db.commit()
