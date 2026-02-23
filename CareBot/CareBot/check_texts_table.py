import sqlite3

conn = sqlite3.connect('db/database')
cursor = conn.cursor()

print("Tables in database:")
cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = cursor.fetchall()
for table in tables:
    print(f"  - {table[0]}")

print("\nTexts table structure:")
try:
    cursor.execute("PRAGMA table_info(texts)")
    columns = cursor.fetchall()
    if columns:
        for column in columns:
            print(f"  Column: {column[1]}, Type: {column[2]}")
    else:
        print("  Table 'texts' does not exist")
except Exception as e:
    print(f"  Error: {e}")

conn.close()