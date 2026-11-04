import sqlite3
import json

conn = sqlite3.connect('cypher_label_guard.db')
cur = conn.cursor()

# Hourly today
cur.execute('''
    SELECT strftime('%H:00', created_at) as hr, count(*), sum(labels_count) 
    FROM job_records 
    WHERE date(created_at) = (SELECT date(MAX(created_at)) FROM job_records)
    GROUP BY hr ORDER BY hr
''')
print("Hourly today:", cur.fetchall())

# Hourly yesterday
cur.execute('''
    SELECT strftime('%H:00', created_at) as hr, count(*), sum(labels_count) 
    FROM job_records 
    WHERE date(created_at) = date((SELECT date(MAX(created_at)) FROM job_records), '-1 day')
    GROUP BY hr ORDER BY hr
''')
print("Hourly yesterday:", cur.fetchall())
