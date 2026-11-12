import sqlite3
import os

db_path = 'cypher_label_guard.db'
if os.path.exists(db_path):
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    c.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = [r[0] for r in c.fetchall()]
    print('Tables in SQLite:', tables)
    for t in tables:
        c.execute(f"PRAGMA table_info({t});")
        cols = [r[1] for r in c.fetchall()]
        print(f"  {t}: {cols}")
        c.execute(f"SELECT COUNT(*) FROM {t};")
        cnt = c.fetchone()[0]
        print(f"    row count: {cnt}")
else:
    print('Database file not found:', db_path)
