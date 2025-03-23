import datetime
import sqlite3
from xmlrpc.client import DateTime

conn = sqlite3.connect(r"C:\Users\al-gerasimov\source\repos\Care\CareBot\CareBot\db\database", check_same_thread=False)
cursor = conn.cursor()

def add_battle_participant(battle_id, participant):
    cursor.execute('INSERT INTO battle_attenders(battle_id, attender_id) VALUES(?, ?)', (battle_id, participant))
    conn.commit()

def add_battle(mission_id):
    cursor.execute('INSERT INTO battles(mission_id) VALUES(?)', (mission_id,))
    conn.commit()
    cursor.execute('SELECT last_insert_rowid()')
    return cursor.fetchone()

def set_cell_patron(cell_id, winner_alliance_id):
    cursor.execute('UPDATE map SET patron=? WHERE id=?', (winner_alliance_id, cell_id))
    conn.commit()

def get_cell_id_by_battle_id(battle_id):
    cursor.execute('SELECT mission_id FROM battles WHERE id=?', (battle_id,))
    mission_id = cursor.fetchone()
    cursor.execute('SELECT cell FROM mission_stack WHERE id=?', (mission_id,))
    return cursor.fetchone()

def get_opponent_telegram_id(battle_id, current_user_telegram_id):
    cursor.execute('''
        SELECT attender_id 
        FROM battle_attenders 
        WHERE battle_id = ? 
        AND attender_id != (
            SELECT id 
            FROM warmasters 
            WHERE telegram_id = ?
        )
    ''', (battle_id, current_user_telegram_id))
    return cursor.fetchone()

def add_battle_result(mission_id, counts1, counts2):
    cursor.execute('INSERT INTO battles(mission_id, fstplayer, sndplayer) VALUES(?, ?, ?)', (mission_id, counts1, counts2))
    conn.commit()

def add_warmaster(telegram_id):
    cursor.execute('INSERT OR IGNORE INTO warmasters(telegram_id) VALUES(?)', (telegram_id,))
    conn.commit()

def get_event_participants(eventId):
    cursor.execute('''
        SELECT user_telegram 
        FROM schedule 
        WHERE date = (SELECT date FROM schedule WHERE id = ?) 
        AND rules = (SELECT rules FROM schedule WHERE id = ?)
    ''', (eventId, eventId))
    return cursor.fetchall()

def get_mission():
    cursor.execute('SELECT * FROM mission_stack')
    return cursor.fetchone()

def get_schedule_by_user(user_telegram, date=None):
    query = 'SELECT * FROM schedule WHERE user_telegram=?'
    params = [user_telegram]
    if date:
        query += ' AND date=?'
        params.append(date)
    cursor.execute(query, params)
    return cursor.fetchall()

def get_schedule_with_warmasters(user_telegram, date=None):
    cursor.execute('''
        SELECT schedule.id, schedule.rules, warmasters.nickname 
        FROM schedule 
        JOIN warmasters ON schedule.user_telegram=warmasters.telegram_id 
        AND schedule.user_telegram<>? 
        AND schedule.date=?
    ''', (user_telegram, date))
    return cursor.fetchall()

def get_settings(telegram_user_id):
    cursor.execute('SELECT nickname, registered_as FROM warmasters WHERE telegram_id=?', (telegram_user_id,))
    return cursor.fetchone()

def get_warmasters_opponents(against_alliance, rule, date):
    cursor.execute('''
        SELECT DISTINCT nickname, registered_as 
        FROM warmasters 
        JOIN schedule ON warmasters.alliance<>? 
        WHERE rules=? 
        AND date=?
    ''', (against_alliance[0], rule, str(datetime.datetime.strptime(date, "%c").strftime("%Y-%m-%d"))))
    return cursor.fetchall()

def get_alliance_of_warmaster(telegram_user_id):
    cursor.execute('SELECT alliance FROM warmasters WHERE telegram_id=?', (telegram_user_id,))
    return cursor.fetchone()

def insert_to_schedule(date, rules, user_telegram):
    weekNumber = date.isocalendar()[1]
    cursor.execute('DELETE FROM schedule WHERE date_week<>?', (weekNumber,))
    cursor.execute('INSERT INTO schedule (date, rules, user_telegram, date_week) VALUES (?, ?, ?, ?)', (str(date.date()), rules, user_telegram, weekNumber))
    conn.commit()

def is_warmaster_registered(user_telegram_id):
    return True

def lock_mission(mission_id):
    cursor.execute('UPDATE mission_stack SET locked=1 WHERE id=?', (mission_id,))
    conn.commit()

def register_warmaster(user_telegram_id, phone):
    cursor.execute('UPDATE warmasters SET registered_as=? WHERE telegram_id=?', (phone, user_telegram_id))
    conn.commit()

def set_nickname(user_telegram_id, nickname):
    cursor.execute('UPDATE warmasters SET nickname=? WHERE telegram_id=?', (nickname, user_telegram_id))
    conn.commit()
