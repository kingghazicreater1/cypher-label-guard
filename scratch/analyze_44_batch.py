import sqlite3
import json

conn = sqlite3.connect('cypher_label_guard.db')
c = conn.cursor()

# Get the most recent batch of jobs
rows = c.execute('''
    SELECT id, job_number, name, status, consensus_label, created_at, criteria_json
    FROM job_records
    ORDER BY created_at DESC
    LIMIT 50
''').fetchall()

print(f"Total retrieved: {len(rows)}")

# Find timestamps
timestamps = {}
for r in rows:
    ts = str(r[5])[:16]
    timestamps[ts] = timestamps.get(ts, 0) + 1

print("Timestamp clusters:", timestamps)

# Inspect the latest batch cluster
latest_ts = max(timestamps.keys())
batch_jobs = [r for r in rows if str(r[5]).startswith(latest_ts)]
print(f"\nAnalyzing latest batch ({len(batch_jobs)} items at {latest_ts}):")

for i, job in enumerate(reversed(batch_jobs)):
    j_id, j_num, j_name, j_status, j_decision, j_created, j_crit = job
    print(f"\n--- [{i+1}] Job #{j_num} | Status: {j_status} | Decision: {j_decision} ---")
    print(f"File: {j_name[:50]}")
    try:
        crit_data = json.loads(j_crit) if j_crit else []
        for crit in crit_data:
            name = crit.get("name", "")
            val = crit.get("value", "")
            conf = crit.get("confidence", 0)
            print(f"  * {name:<35}: {val} ({conf}%)")
    except Exception as e:
        print(f"  Error parsing criteria: {e}")
