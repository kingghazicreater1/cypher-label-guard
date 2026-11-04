import json

with open('scratch/full_44_report.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

print(f"Total jobs: {len(data)}")
for d in data:
    idx = d['index']
    job_num = d['job_num']
    prim = d['primary_subject']
    edible = d['criteria'].get('is the main object edible by humans, and is it in its natural or prepared form?', '')
    human = d['criteria'].get('is there a real human, a toy, a statue, or a reflection?', '')
    brand = d['criteria'].get('extract the brand name AND the product model/serial number if visible', '')
    print(f"#{idx:02d} | Job #{job_num} | Edible: {edible:<10} | Human: {human:<18} | Brand: {brand:<15} | Subject: {prim[:60]}")
