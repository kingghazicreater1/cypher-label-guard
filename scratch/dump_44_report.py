import sqlite3
import json

conn = sqlite3.connect('cypher_label_guard.db')
c = conn.cursor()

rows = c.execute('''
    SELECT job_number, name, status, consensus_label, criteria_json
    FROM job_records
    WHERE created_at LIKE '2026-10-24 01:56%'
    ORDER BY id ASC
''').fetchall()

print(f"Total jobs: {len(rows)}")

full_report = []

for idx, r in enumerate(rows):
    j_num, name, status, decision, c_json = r
    crits = json.loads(c_json) if c_json else []
    
    # Extract primary subject
    prim = ""
    for c_item in crits:
        if "primary subject" in c_item.get("name", "").lower():
            prim = c_item.get("value", "")
            break
            
    full_report.append({
        "index": idx + 1,
        "job_num": j_num,
        "filename": name,
        "decision": decision,
        "primary_subject": prim,
        "criteria": {c_item.get("name"): c_item.get("value") for c_item in crits}
    })

with open("scratch/full_44_report.json", "w", encoding="utf-8") as f:
    json.dump(full_report, f, indent=2)

print("Saved full report to scratch/full_44_report.json")
