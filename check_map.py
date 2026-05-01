import sqlite3
conn = sqlite3.connect("/app/CareBot/carebot.db")
cur = conn.cursor()
count = cur.execute("SELECT COUNT(*) FROM map").fetchone()[0]
print("Total map hexes:", count)
rows = cur.execute("SELECT id, state, patron FROM map ORDER BY id LIMIT 10").fetchall()
for r in rows:
    print(r)
conn.close()
