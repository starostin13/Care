import sqlite3
from xmlrpc.client import DateTime

conn = sqlite3.connect(r"C:\Users\al-gerasimov\source\repos\Care\CareBot\CareBot\db\database", check_same_thread=False)
cursor = conn.cursor()

def insert_to_schedule(date: DateTime, rules: str, user_telegram: str):
	cursor.execute('INSERT INTO schedule (date, rules, user_telegram) VALUES (?, ?, ?)', (str(date), rules, user_telegram))
	conn.commit()
	
def get_schedule_by_user(user_telegram: str):
	result = cursor.execute('SELECT * FROM schedule WHERE user_telegram={}'.format(user_telegram))
	return result.fetchall

