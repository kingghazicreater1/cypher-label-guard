import sqlite3
import json

c = sqlite3.connect("cypher_label_guard.db")
r = c.execute("SELECT job_number, name, criteria_json, annotations_json, lineage_hash, trace_id, image_url FROM job_records WHERE job_number='470474'").fetchone()
if r:
    print("Job:", r[0])
    print("Name:", r[1])
    print("Image URL len:", len(r[6]) if r[6] else 0)
    print("Image URL sample:", r[6][:100] if r[6] else None)
    crit = json.loads(r[2]) if r[2] else []
    print("Criteria count:", len(crit))
