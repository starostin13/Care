# database.py

import sqlite3
from datetime import datetime

# Establish the database connection globally for reuse
conn = sqlite3.connect(r"C:\Users\al-gerasimov\source\repos\Care\CareBot\CareBot\db\database", check_same_thread=False)
cursor = conn.cursor()

async def execute_query(query, params=()):
    cursor.execute(query, params)
    conn.commit()

def register_warmaster(user_id: int, phone: str):
    """Registers a warmaster in the database with a user ID and phone number."""
    try:
        cursor.execute(
            "INSERT INTO warmasters (telegram_id, alliance, nickname) VALUES (?, ?, ?)",
            (user_id, phone, "New Warmaster")
        )
        conn.commit()
    except sqlite3.IntegrityError as e:
        print(f"Error registering warmaster: {e}")

def insert_to_schedule(date: datetime, rule: str, user_id: int):
    """Inserts a new game schedule entry into the database."""
    try:
        cursor.execute(
            "INSERT INTO schedule (date, rule, user_id) VALUES (?, ?, ?)",
            (date, rule, user_id)
        )
        conn.commit()
    except sqlite3.IntegrityError as e:
        print(f"Error inserting schedule: {e}")

def get_rules_for_user(user_id: int) -> list:
    """Retrieves the rules associated with a user."""
    cursor.execute("SELECT rule FROM user_rules WHERE user_id = ?", (user_id,))
    return [row[0] for row in cursor.fetchall()]

def get_week_schedule(user_id: int) -> list:
    """Retrieves the weekly schedule for the user."""
    cursor.execute(
        "SELECT date, rule FROM schedule WHERE user_id = ? AND date >= ?",
        (user_id, datetime.now())
    )
    return [{"date": row[0], "rule": row[1]} for row in cursor.fetchall()]

def get_event_participants(event_id: int) -> list:
    """Retrieves all participants for a given event ID."""
    cursor.execute(
        "SELECT user_id FROM event_participants WHERE event_id = ?",
        (event_id,)
    )
    return [row[0] for row in cursor.fetchall()]
