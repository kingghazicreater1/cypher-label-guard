import sqlite3
import json

conn = sqlite3.connect("cypher_label_guard.db")
c = conn.cursor()
row = c.execute("SELECT id, job_number, criteria_json, annotations_json FROM job_records WHERE job_number='470474' OR id LIKE '%470474%'").fetchone()
print("Criteria JSON:")
print(row[2])
print("\nAnnotations JSON:")
print(row[3])
