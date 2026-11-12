import sys, json, statistics
sys.path.insert(0, r"c:\Users\Friends\Desktop\AV GUARDIAN")

with open(r'c:\Users\Friends\Desktop\AV GUARDIAN\scratch\grand_beta_100_detailed_results.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

total = len(data)
statuses = {}
for r in data:
    s = r.get('status','UNKNOWN')
    statuses[s] = statuses.get(s,0) + 1

latencies = [r['latency_s'] for r in data if r.get('latency_s')]
bbox_quality = {}
for r in data:
    bq = r.get('bbox_quality', 'NONE')
    bbox_quality[bq] = bbox_quality.get(bq,0)+1

missed = [r for r in data if not r.get('detected_primary') or r.get('detected_primary') in ('None', None, '')]
zero_boxes = [r for r in data if r.get('bbox_count',0)==0]
coarse = [r for r in data if r.get('bbox_quality','')=='COARSE_FULL_FRAME']
humans = [r for r in data if r.get('detected_human')]
edible = [r for r in data if r.get('detected_edible')]
living = [r for r in data if r.get('detected_living')]

confs = []
for r in data:
    for bb in r.get('bounding_boxes',[]):
        c = bb.get('confidence')
        if c: confs.append(float(c))

print(f'Total: {total}')
print(f'Statuses: {statuses}')
print(f'Latency avg: {statistics.mean(latencies):.2f}s min: {min(latencies):.2f}s max: {max(latencies):.2f}s p50: {sorted(latencies)[49]:.2f}s p90: {sorted(latencies)[89]:.2f}s')
print(f'BBox quality: {bbox_quality}')
print(f'Zero-box images: {len(zero_boxes)}')
print(f'Zero-box IDs & subjects:')
for r in zero_boxes:
    print(f'  #{r["id"]:03d}: {r.get("detected_primary","?")} | status={r.get("status")} | latency={r.get("latency_s")}s')
print(f'Coarse boxes: {len(coarse)}')
for r in coarse:
    print(f'  #{r["id"]:03d}: {r.get("detected_primary","?")}')
print(f'Missed detections: {len(missed)}')
for r in missed:
    print(f'  #{r["id"]:03d}: primary={r.get("detected_primary")} objects={r.get("detected_objects")} status={r.get("status")}')
print(f'Human detected: {len(humans)} images')
print(f'  IDs: {[r["id"] for r in humans]}')
print(f'Edible: {len(edible)}, Living: {len(living)}')
total_boxes = sum(r.get('bbox_count',0) for r in data)
print(f'Total boxes: {total_boxes}, avg: {total_boxes/total:.2f}')
if confs:
    print(f'Confidence avg: {statistics.mean(confs):.1f}%, min: {min(confs):.1f}%, max: {max(confs):.1f}%, p50: {sorted(confs)[len(confs)//2]:.1f}%')

print()
print('=== ALL DETECTIONS ===')
for r in data:
    print(f'#{r["id"]:03d} [{r.get("status","?")}] primary="{r.get("detected_primary","")}" boxes={r.get("bbox_count",0)} ({r.get("bbox_quality","?")}) lat={r.get("latency_s",0):.1f}s')
