﻿import datetime
import sqlite3
from xmlrpc.client import DateTime

conn = sqlite3.connect(r"C:\Users\al-gerasimov\source\repos\Care\CareBot\CareBot\db\database", check_same_thread=False)
#conn.row_factory = lambda cursor, row: row[0]
cursor = conn.cursor()

async def add_warmaster(telegram_id):
	cursor.execute(f'INSERT OR IGNORE INTO warmasters(telegram_id) VALUES({telegram_id})')
	conn.commit()
	
def get_schedule_by_user(user_telegram: str):
	result = cursor.execute('SELECT * FROM schedule WHERE user_telegram={}'.format(user_telegram))
	return result.fetchall()

def get_settings(telegram_user_id):
	result = cursor.execute(f'SELECT nickname, registered_as FROM warmasters WHERE telegram_id={telegram_user_id}')
	return result.fetchone()

def get_warmasters_opponents(against_alliance, rule, date):
	select = f'SELECT DISTINCT nickname, registered_as FROM warmasters JOIN schedule ON warmasters.alliance<>"{against_alliance[0]}" WHERE rules="{rule}" AND date="{str(datetime.datetime.strptime(date, "%c"))}"'
	result = cursor.execute(select)
	return result.fetchall()

def get_alliance_of_warmaster(telegram_user_id):
	result = cursor.execute(f'SELECT alliance FROM warmasters WHERE telegram_id={telegram_user_id}')
	return result.fetchone()

def insert_to_schedule(date: DateTime, rules: str, user_telegram: str):
	weekNumber = date.isocalendar()[1]
	result = cursor.execute(f'DELETE FROM schedule WHERE date_week<>{str(weekNumber)}')
	result.fetchall()
	
	cursor.execute('INSERT INTO schedule (date, rules, user_telegram, date_week) VALUES (?, ?, ?, ?)', (str(date), rules, user_telegram, weekNumber))
	conn.commit()
	
def is_warmaster_registered(user_telegram_id):
	return True

def register_warmaster(user_telegram_id, phone):
	cursor.execute(f'UPDATE warmasters SET registered_as="{phone}" WHERE telegram_id={user_telegram_id}')
	conn.commit()

def set_nickname(user_telegram_id, nickname):
	cursor.execute(f'UPDATE warmasters SET nickname="{nickname}" WHERE telegram_id={user_telegram_id}')
	conn.commit()
	
	