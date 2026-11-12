import asyncio
import os
import sys
import json
import base64
import time

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from core.orchestrator import orchestrator
from core.context import ExecutionContext
from db.database import init_db

init_db()

with open("scratch/selected_100_manifest.json", "r") as f:
    manifest = json.load(f)

test_5 = manifest[:5]
print(f"Testing 5 images concurrently with orchestrator.run_pipeline:")
for it in test_5:
    print(f"  #{it['id']}: {it['filename'][:30]}...")

async def run_one(it):
    t0 = time.time()
    with open(it["path"], "rb") as f:
        b64 = base64.b64encode(f.read()).decode("utf-8")
    
    data_url = f"data:image/jpeg;base64,{b64}"
    
    payload = {
        "text": f"Inspect specimen {it['id']}.",
        "modality": "VISION",
        "image_data": data_url,
        "criteria": [
            {"name": "Visual Subject", "type": "Free Text", "range": ""},
            {"name": "Human Present", "type": "Binary", "range": "Yes / No"},
            {"name": "Defect or Damage", "type": "Binary", "range": "Pass / Fail"}
        ]
    }
    
    ctx = ExecutionContext(
        trace_id=f"test-trace-{it['id']}",
        tenant_id="test-tenant",
        depth_tier="Standard",
        input_payload=payload,
        metadata={"execution_plane": "ENTERPRISE"},
        flags={"modality": "VISION"}
    )
    
    final = await orchestrator.run_pipeline(ctx)
    elapsed = round(time.time() - t0, 1)
    
    # Extract criteria results and annotations
    crit = final.metadata.get("criteria_results") or []
    boxes = final.metadata.get("yolo_boxes") or final.metadata.get("annotations") or []
    conf = final.metadata.get("overall_criteria_confidence")
    subj = final.metadata.get("visual_primary_product") or (crit[0].get("value") if crit else "N/A")
    
    print(f"[Done #{it['id']}] in {elapsed}s | Subject: {subj} | Conf: {conf}% | Boxes: {len(boxes)}")
    return {
        "id": it["id"],
        "filename": it["filename"],
        "elapsed": elapsed,
        "subject": subj,
        "confidence": conf,
        "boxes_count": len(boxes),
        "criteria": crit
    }

async def main():
    t_start = time.time()
    results = await asyncio.gather(*[run_one(it) for it in test_5])
    total_elapsed = round(time.time() - t_start, 1)
    print(f"\nAll 5 completed in {total_elapsed}s total (Average: {round(total_elapsed/5, 1)}s per image)!")

if __name__ == "__main__":
    asyncio.run(main())
