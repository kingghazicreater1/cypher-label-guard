import json

with open("scratch/grand_beta_100_detailed_results.json", "r", encoding="utf-8") as f:
    data = json.load(f)

total = len(data)
correct_subjects = sum(1 for d in data if d.get("subject_verdict") == "CORRECT")
partial_subjects = sum(1 for d in data if d.get("subject_verdict") == "PARTIAL_OBJECTS_ONLY")
missed_subjects = sum(1 for d in data if d.get("subject_verdict") == "MISSED_OR_REJECTED")

pinpoint_boxes = sum(1 for d in data if d.get("bbox_quality") == "PINPOINT")
coarse_boxes = sum(1 for d in data if d.get("bbox_quality") == "COARSE_FULL_FRAME")
zero_boxes = sum(1 for d in data if d.get("bbox_quality") == "ZERO_BOXES")

total_boxes = sum(d.get("bbox_count", 0) for d in data)
human_true = sum(1 for d in data if d.get("detected_human") is True)
human_false = sum(1 for d in data if d.get("detected_human") is False)

latencies = [d.get("latency_s", 0) for d in data]
avg_latency = round(sum(latencies) / len(latencies), 2)
min_latency = min(latencies)
max_latency = max(latencies)

print("=" * 65)
print("=== GRAND 100-IMAGE BENCHMARK EMPIRICAL METRICS ===")
print("=" * 65)
print(f"Total Images Processed: {total}")
print(f"Subject Detection Accuracy: {correct_subjects}/{total} ({correct_subjects/total*100:.1f}%)")
print(f"Partial (Objects only): {partial_subjects}/{total} ({partial_subjects/total*100:.1f}%)")
print(f"Missed / Failed: {missed_subjects}/{total} ({missed_subjects/total*100:.1f}%)")
print(f"Bounding Box Pinpoint Success Rate: {pinpoint_boxes}/{total} ({pinpoint_boxes/total*100:.1f}%)")
print(f"Coarse / Full Frame Boxes: {coarse_boxes}/{total} ({coarse_boxes/total*100:.1f}%)")
print(f"Zero Bounding Boxes (Missed BBoxes): {zero_boxes}/{total} ({zero_boxes/total*100:.1f}%)")
print(f"Total Bounding Boxes Detected: {total_boxes} (Avg {total_boxes/total:.1f} boxes/image)")
print(f"Human Detected Count: {human_true} Present, {human_false} Absent")
print(f"Latency - Avg: {avg_latency}s | Min: {min_latency}s | Max: {max_latency}s")

print("\n" + "=" * 65)
print("=== FAILURE & ANOMALY EDGE CASES (100% TRANSPARENCY) ===")
print("=" * 65)
for d in data:
    if d.get("bbox_quality") == "ZERO_BOXES" or d.get("subject_verdict") != "CORRECT":
        subj = str(d.get("detected_primary") or d.get("detected_objects"))[:30]
        print(f"Image #{d['id']:03d} ({d['filename'][:28]}): Subject='{subj}', Boxes={d['bbox_count']}, Quality={d['bbox_quality']}")
