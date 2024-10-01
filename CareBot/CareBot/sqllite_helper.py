import datetime
import sqlite3
from xmlrpc.client import DateTime

conn = sqlite3.connect(r"C:\Users\al-gerasimov\source\repos\Care\CareBot\CareBot\db\database", check_same_thread=False)
#conn.row_factory = lambda cursor, row: row[0]
cursor = conn.cursor()

async def add_warmaster(telegram_id):
	cursor.execute(f'INSERT OR IGNORE INTO warmasters(telegram_id) VALUES({telegram_id})')
	conn.commit()
	
async def get_event_participants(eventId):
	select = f'SELECT user_telegram FROM schedule WHERE date = (SELECT date FROM schedule WHERE id = {eventId}) AND rules = (SELECT rules FROM schedule WHERE id = {eventId})'
	result = cursor.execute(select)

	return result.fetchall()

async def get_mission():
	select = f'SELECT * FROM mission_stack'
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
	
	