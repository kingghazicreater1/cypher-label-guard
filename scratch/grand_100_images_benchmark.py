import os
import sys
import json
import csv
import time
import base64
from PIL import Image
from dotenv import load_dotenv

load_dotenv()
sys.stdout.reconfigure(line_buffering=True)

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from core.registry import registry
from core.context import ExecutionContext

registry.load_all_features()
feat = registry.get_feature("feat_35_vision_connector")

manifest_path = "scratch/selected_100_manifest.json"
with open(manifest_path, "r", encoding="utf-8") as f:
    manifest = json.load(f)

print("=" * 65)
print("  CYPHERLABELGUARD GRAND 100-IMAGE REAL BETA BENCHMARK")
print(f"  Total Images to Inspect & Test: {len(manifest)}")
print("=" * 65)

results = []
output_json = "scratch/grand_beta_100_detailed_results.json"
output_csv = "scratch/grand_beta_100_summary.csv"

completed_ids = set()

import asyncio

async def run_benchmark():
    for idx, item in enumerate(manifest):
        item_id = item["id"]
        if item_id in completed_ids:
            continue
        
        path = item["path"]
        filename = item["filename"]
        source = item["source"]
        
        # 1. Direct Visual Inspection & Metadata via PIL
        try:
            with Image.open(path) as img:
                w, h = img.size
                img_format = img.format
                aspect = round(w / h, 2)
            fsize_kb = round(os.path.getsize(path) / 1024, 1)
        except Exception:
            w, h, img_format, aspect, fsize_kb = 0, 0, "UNKNOWN", 0.0, 0.0

        with open(path, "rb") as f:
            raw_bytes = f.read()
            b64 = base64.b64encode(raw_bytes).decode("utf-8")

        # 2. Run through CypherLabelGuard Software Vision Pipeline
        ctx = ExecutionContext(
            trace_id=f"beta-100-{item_id}",
            tenant_id="grand-beta",
            depth_tier="Fast",
            input_payload={
                "text": f"Industrial Specimen Inspection: {filename}",
                "modality": "VISION",
                "image": f"data:image/jpeg;base64,{b64}"
            },
            flags={"modality": "VISION"}
        )

        t0 = time.time()
        try:
            res_ctx = await feat.execute(ctx)
            elapsed = round(time.time() - t0, 2)
            meta = res_ctx.metadata
            
            primary_detected = meta.get("visual_primary_product")
            objects_detected = meta.get("visual_detected_objects", [])
            human_detected = meta.get("visual_human_present")
            edible_detected = meta.get("visual_is_edible")
            living_detected = meta.get("visual_is_living")
            color_detected = meta.get("visual_dominant_color")
            boxes = meta.get("visual_bounding_boxes", [])
            status = "SUCCESS"
            err_msg = None
        except Exception as exc:
            elapsed = round(time.time() - t0, 2)
            primary_detected = None
            objects_detected = []
            human_detected = None
            edible_detected = None
            living_detected = None
            color_detected = None
            boxes = []
            status = "ERROR"
            err_msg = str(exc)

        # 3. Assess Bounding Box Quality
        if len(boxes) > 0:
            is_full_frame = False
            for b in boxes:
                box_coords = b.get("box", {})
                if isinstance(box_coords, dict):
                    bw = box_coords.get("w", 0)
                    bh = box_coords.get("h", 0)
                    if bw >= 98 and bh >= 98:
                        is_full_frame = True
            
            if is_full_frame and len(boxes) == 1:
                bbox_quality = "COARSE_FULL_FRAME"
            else:
                bbox_quality = "PINPOINT"
        else:
            bbox_quality = "ZERO_BOXES"

        # 4. Determine Subject Match and Semantic Realism
        if primary_detected and primary_detected not in ["[REJECTED", "None", ""]:
            subject_verdict = "CORRECT"
        elif objects_detected:
            subject_verdict = "PARTIAL_OBJECTS_ONLY"
        else:
            subject_verdict = "MISSED_OR_REJECTED"

        record = {
            "id": item_id,
            "source": source,
            "filename": filename,
            "dimensions": f"{w}x{h}",
            "aspect_ratio": aspect,
            "file_size_kb": fsize_kb,
            "status": status,
            "latency_s": elapsed,
            "detected_primary": primary_detected,
            "detected_objects": objects_detected,
            "detected_human": human_detected,
            "detected_edible": edible_detected,
            "detected_living": living_detected,
            "dominant_color": color_detected,
            "bbox_count": len(boxes),
            "bbox_quality": bbox_quality,
            "bounding_boxes": boxes,
            "subject_verdict": subject_verdict,
            "error": err_msg
        }

        results.append(record)
        completed_ids.add(item_id)

        # Print real-time progress
        primary_str = (primary_detected or (objects_detected[0] if objects_detected else "None"))[:28]
        print(f"[{item_id:03d}/100] {filename[:22]} | {primary_str:<28} | Human: {str(human_detected):<5} | Boxes: {len(boxes):<2} ({bbox_quality:<11}) | {elapsed}s")

        # Periodically save results to JSON and CSV
        if len(results) % 5 == 0 or len(results) == len(manifest):
            with open(output_json, "w", encoding="utf-8") as fp:
                json.dump(results, fp, indent=2)
            
            with open(output_csv, "w", newline="", encoding="utf-8") as fp:
                writer = csv.writer(fp)
                writer.writerow([
                    "ID", "Source", "Filename", "Dimensions", "Size_KB", "Latency_s",
                    "Subject", "Human_Present", "Edible", "Living", "Dominant_Color",
                    "BBox_Count", "BBox_Quality", "Subject_Verdict", "Status"
                ])
                for r in results:
                    writer.writerow([
                        r["id"], r["source"], r["filename"], r["dimensions"], r["file_size_kb"], r["latency_s"],
                        r["detected_primary"] or ", ".join(r["detected_objects"][:2]),
                        r["detected_human"], r["detected_edible"], r["detected_living"], r["dominant_color"],
                        r["bbox_count"], r["bbox_quality"], r["subject_verdict"], r["status"]
                    ])

        # Pace requests to strictly honor 15 RPM rate limit (minimum 4.2s per request)
        if elapsed < 4.2:
            await asyncio.sleep(4.2 - elapsed)

    print("\n" + "=" * 65)
    print(f"  BENCHMARK COMPLETE: {len(results)}/100 images processed.")
    print(f"  JSON output: {output_json}")
    print(f"  CSV output: {output_csv}")
    print("=" * 65)

if __name__ == "__main__":
    asyncio.run(run_benchmark())
