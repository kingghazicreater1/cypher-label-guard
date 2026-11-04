import sqlite3
import json

conn = sqlite3.connect('cypher_label_guard.db')
c = conn.cursor()

# Get all 44 jobs
rows = c.execute('''
    SELECT job_number, name, status, consensus_label, criteria_json
    FROM job_records
    WHERE created_at LIKE '2026-10-24 01:56%'
    ORDER BY id ASC
''').fetchall()

print(f"Total jobs in batch: {len(rows)}")

headings_map = {}

for r in rows:
    j_num, name, status, decision, c_json = r
    try:
        crits = json.loads(c_json) if c_json else []
        for c_item in crits:
            h = c_item.get("name")
            val = c_item.get("value")
            conf = c_item.get("confidence")
            if h not in headings_map:
                headings_map[h] = []
            headings_map[h].append((j_num, name[:25], val, conf))
    except Exception as e:
        print(f"Error: {e}")

print(f"\nUnique Headings ({len(headings_map)}):")
for h, vals in headings_map.items():
    print(f"\n=======================================================")
    print(f"HEADING: {h}")
    print(f"Sample values (first 5 of {len(vals)}):")
    for v in vals[:5]:
        print(f"  * Job #{v[0]}: {v[2]} ({v[3]}%)")
