import datetime
import sqlite3
from xmlrpc.client import DateTime

conn = sqlite3.connect(r"C:\Users\al-gerasimov\source\repos\Care\CareBot\CareBot\db\database", check_same_thread=False)
cursor = conn.cursor()

async def add_battle_result(mission_id, counts1, counts2):
	cursor.execute(f"INSERT INTO battles(mission_id,fstplayer, sndplayer) VALUES({mission_id}, {counts1}, {counts2})")
	conn.commit()

async def add_warmaster(telegram_id):
	cursor.execute(f'INSERT OR IGNORE INTO warmasters(telegram_id) VALUES({telegram_id})')
	conn.commit()
	
async def get_event_participants(eventId):
	select = f'SELECT user_telegram FROM schedule WHERE date = (SELECT date FROM schedule WHERE id = {eventId}) AND rules = (SELECT rules FROM schedule WHERE id = {eventId})'
	result = cursor.execute(select)

	return result.fetchall()

def get_hexs_on_frontline(attacker, defender):
	# Получаем альянсы атакующего и защищающегося
	alliance_query = """
	SELECT 
		wm1.alliance AS attacker_alliance,
		wm2.alliance AS defender_alliance
	FROM 
		warmasters wm1, warmasters wm2
	WHERE 
		wm1.id = ? AND wm2.id = ?
	"""
    
	cursor.execute(alliance_query, (attacker, defender))
	result = cursor.fetchone()

	if not result:
		return None
    
	attacker_alliance, defender_alliance = result

	# Получаем все гексы защитника
	defender_hexes_query = """
	SELECT id FROM map
	WHERE patron = ?
	"""
    
	cursor.execute(defender_hexes_query, (defender_alliance,))
	defender_hexes = [row[0] for row in cursor.fetchall()]

	# Получаем все гексы атакующего
	attacker_hexes_query = """
	SELECT id FROM map
	WHERE patron = ?
	"""
    
	cursor.execute(attacker_hexes_query, (attacker_alliance,))
	attacker_hexes = [row[0] for row in cursor.fetchall()]

	# Получаем гексы защитника, которые граничат с гексами атакующего
	attacker_hexes_placeholder = ", ".join("?" for _ in attacker_hexes)
	frontline_hexes_query = f"""
	SELECT DISTINCT m.id 
	FROM map m
	JOIN edges e ON (e.left_hexagon = m.id OR e.right_hexagon = m.id)
	WHERE m.patron = ? AND (
		(e.left_hexagon IN ({attacker_hexes_placeholder}) AND e.right_hexagon = m.id) OR
		(e.right_hexagon IN ({attacker_hexes_placeholder}) AND e.left_hexagon = m.id)
	)
	"""

	# Выполняем запрос с использованием ID гексов атакующего как параметры
	cursor.execute(frontline_hexes_query, [defender_alliance] + attacker_hexes + attacker_hexes)
	frontline_hexes = [row[0] for row in cursor.fetchall()]

	# Возвращаем результат
	return frontline_hexes

async def get_mission():
	select = f'SELECT * FROM mission_stack WHERE locked==0'
	result = cursor.execute(select)
	return result.fetchone()

def get_schedule_by_user(user_telegram: str, date=None):
	select = 'SELECT * FROM schedule WHERE user_telegram={}'.format(user_telegram)
	if date:
		select += f' AND date="{date}"'
	result = cursor.execute(select)
	return result.fetchall()

def get_schedule_with_warmasters(user_telegram: str, date=None):
	select = f'SELECT schedule.id, schedule.rules, warmasters.nickname FROM schedule JOIN warmasters ON schedule.user_telegram=warmasters.telegram_id AND schedule.user_telegram<>{user_telegram} AND schedule.date="{date}"'
	result = cursor.execute(select)
	return result.fetchall()

def get_settings(telegram_user_id):
	result = cursor.execute(f'SELECT nickname, registered_as FROM warmasters WHERE telegram_id={telegram_user_id}')
	return result.fetchone()

def get_warmasterid_bytelegramid(telegram_user_id):
	result = cursor.execute(f'SELECT id FROM warmasters WHERE telegram_id={telegram_user_id}')
	return result.fetchone()

def get_warmasterid_ofshedule(scheduleid):
    result = cursor.execute(f'SELECT user_telegram FROM schedule WHERE id={scheduleid}')
    return result.fetchone()

def get_warmasters_opponents(against_alliance, rule, date):
	select = f'SELECT DISTINCT nickname, registered_as FROM warmasters JOIN schedule ON warmasters.alliance<>"{against_alliance[0]}" WHERE rules="{rule}" AND date="{str(datetime.datetime.strptime(date, "%c").strftime("%Y-%m-%d"))}"'
	result = cursor.execute(select)
	return result.fetchall()

def get_alliance_of_warmaster(telegram_user_id):
	result = cursor.execute(f'SELECT alliance FROM warmasters WHERE telegram_id={telegram_user_id}')
	return result.fetchone()

def insert_to_schedule(date: DateTime, rules: str, user_telegram: str):
	weekNumber = date.isocalendar()[1]
	result = cursor.execute(f'DELETE FROM schedule WHERE date_week<>{str(weekNumber)}')
	result.fetchall()

	already_there = cursor.execute(f'SELECT * FROM schedule WHERE date={str(date.date())} AND rules={rules} AND user_telegram={user_telegram} AND date_week={weekNumber}')
	already_there.fetchone()
	
	cursor.execute('INSERT INTO schedule (date, rules, user_telegram, date_week) VALUES (?, ?, ?, ?)', (str(date.date()), rules, user_telegram, weekNumber))
	conn.commit()
	
def is_warmaster_registered(user_telegram_id):
	return True

def lock_mission(mission_id):
	cursor.execute(f'UPDATE mission_stack SET locked=1 WHERE id={mission_id}')
	conn.commit()

def register_warmaster(user_telegram_id, phone):
	cursor.execute(f'UPDATE warmasters SET registered_as="{phone}" WHERE telegram_id={user_telegram_id}')
	conn.commit()

def set_nickname(user_telegram_id, nickname):
	cursor.execute(f'UPDATE warmasters SET nickname="{nickname}" WHERE telegram_id={user_telegram_id}')
	conn.commit()
	
	