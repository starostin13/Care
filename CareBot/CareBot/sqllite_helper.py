import datetime
import sqlite3
from xmlrpc.client import DateTime

conn = sqlite3.connect(r"C:\Users\al-gerasimov\source\repos\Care\CareBot\CareBot\db\database", check_same_thread=False)
cursor = conn.cursor()

def insert_to_schedule(date: DateTime, rules: str, user_telegram: str):
	weekNumber = 0
	#result = cursor.execute('DELETE FROM schedule WHERE date_week<>?', weekNumber)
	
	cursor.execute('INSERT INTO schedule (date, rules, user_telegram, date_week) VALUES (?, ?, ?, ?)', (str(date), rules, user_telegram, weekNumber))
	conn.commit()
	
def get_schedule_by_user(user_telegram: str):
	result = cursor.execute('SELECT * FROM schedule WHERE user_telegram={}'.format(user_telegram))
	return result.fetchall()

def get_warmasters_opponents(against_alliance, rule, week_day):
	select = f'SELECT DISTINCT user_telegram FROM schedule JOIN warmasters ON warmasters.alliance<>"{against_alliance[0]}" WHERE rules="{rule}" AND date="{week_day}"'
	result = cursor.execute(select)
	return result.fetchall()

def get_alliance_of_warmaster(telegram_user_id):
	result = cursor.execute(f'SELECT alliance FROM warmasters WHERE telegram_id={telegram_user_id}')
	return result.fetchone()

async def add_warmaster(telegram_id):
	cursor.execute(f'INSERT OR IGNORE INTO warmasters(telegram_id) VALUES({telegram_id})')
	conn.commit()

	