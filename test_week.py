import sqlite3
import os

db_path = 'hospital.db'
if not os.path.exists(db_path):
    print("No database at", db_path)

conn = sqlite3.connect(db_path)
res = conn.execute("SELECT strftime('%Y-%W', '2026-06-17')").fetchone()[0]
print("Week format from SQLite for 2026-06-17:", res)
conn.close()
