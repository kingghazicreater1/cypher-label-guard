import sqlite3
import json

conn = sqlite3.connect('cypher_label_guard.db')
conn.row_factory = sqlite3.Row
c = conn.cursor()

print("=== RECENT LABELING JOBS (Last 5) ===")
c.execute("SELECT * FROM job_records ORDER BY created_at DESC LIMIT 5")
recent_jobs = c.fetchall()
for j in recent_jobs:
    print(f"\nJob #{j['job_number']} (ID: {j['id'][:8]}...) | Name: {j['name']}")
    print(f"  Modality: {j['modality']} | Status: {j['status']} | Progress: {j['progress']}% | Created: {j['created_at']}")
    print(f"  Consensus Label: {j['consensus_label']} | Affirmative Votes: {j['affirmative_votes']}/32")
    print(f"  Labels Count: {j['labels_count']} | Cost: {j['cost']}")
    print(f"  Trace ID: {j['trace_id']} | Lineage Hash: {j['lineage_hash'][:16] if j['lineage_hash'] else 'None'}...")
    if j['annotations_json']:
        try:
            ann = json.loads(j['annotations_json'])
            print(f"  Annotations: {ann}")
        except:
            print(f"  Annotations raw: {j['annotations_json'][:100]}")

print("\n=== CONSENSUS LABEL DISTRIBUTION ===")
c.execute("SELECT consensus_label, count(*) as cnt FROM job_records GROUP BY consensus_label ORDER BY cnt DESC LIMIT 10")
for row in c.fetchall():
    print(f"  Label: {row['consensus_label']} -> {row['cnt']} jobs")

print("\n=== STATUS BREAKDOWN ===")
c.execute("SELECT status, count(*) as cnt FROM job_records GROUP BY status")
for row in c.fetchall():
    print(f"  Status: {row['status']} -> {row['cnt']} jobs")

print("\n=== MODALITY BREAKDOWN ===")
c.execute("SELECT modality, count(*) as cnt FROM job_records GROUP BY modality")
for row in c.fetchall():
    print(f"  Modality: {row['modality']} -> {row['cnt']} jobs")

print("\n=== AUDIT LOGS OVERVIEW ===")
c.execute("SELECT action, count(*) as cnt FROM audit_log_entries GROUP BY action ORDER BY cnt DESC LIMIT 5")
for row in c.fetchall():
    print(f"  Action: {row['action']} -> {row['cnt']} entries")
