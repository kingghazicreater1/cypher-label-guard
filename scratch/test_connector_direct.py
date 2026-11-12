import os
import sys
import json
import base64
import time
from PIL import Image

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from core.registry import registry
from core.context import ExecutionContext

registry.load_all_features()
feat = registry.get_feature("feat_35_vision_connector")

with open("scratch/selected_100_manifest.json", "r") as f:
    manifest = json.load(f)

print(f"Testing direct VisionConnector on first 3 images:")

import asyncio

async def test():
    for item in manifest[:3]:
        path = item["path"]
        with open(path, "rb") as f:
            raw_bytes = f.read()
            b64 = base64.b64encode(raw_bytes).decode("utf-8")
        
        ctx = ExecutionContext(
            trace_id=f"direct-test-{item['id']}",
            tenant_id="test",
            depth_tier="Fast",
            input_payload={
                "text": f"Analyze specimen {item['filename']}",
                "modality": "VISION",
                "image": f"data:image/jpeg;base64,{b64}"
            },
            flags={"modality": "VISION"}
        )
        
        t0 = time.time()
        res_ctx = await feat.execute(ctx)
        elapsed = round(time.time() - t0, 2)
        
        meta = res_ctx.metadata
        boxes = meta.get("visual_bounding_boxes", [])
        primary = meta.get("visual_primary_product")
        objs = meta.get("visual_detected_objects", [])
        color = meta.get("visual_dominant_color")
        human = meta.get("visual_human_present")
        
        print(f"\n[Image #{item['id']}: {item['filename'][:30]}...] ({elapsed}s)")
        print(f"  Primary: {primary}")
        print(f"  Objects: {objs}")
        print(f"  Dominant Color: {color}")
        print(f"  Human Present: {human}")
        print(f"  Boxes ({len(boxes)}):")
        for b in boxes:
            print(f"    - {b.get('label')}: {b.get('box')} (conf: {b.get('confidence')}%)")

asyncio.run(test())
