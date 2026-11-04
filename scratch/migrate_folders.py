import sqlite3

conn = sqlite3.connect('cypher_label_guard.db')
c = conn.cursor()
c.execute('PRAGMA table_info(job_records)')
cols = [r[1] for r in c.fetchall()]
print('Existing columns:', cols)

if 'folder_name' not in cols:
    print('Adding folder_name column...')
    c.execute("ALTER TABLE job_records ADD COLUMN folder_name TEXT DEFAULT 'General Workspace'")
    conn.commit()
    print('Added folder_name successfully!')
else:
    print('folder_name already exists.')

conn.close()
