import sys
sys.path.insert(0, ".")
import os
import asyncio
from dotenv import load_dotenv
load_dotenv()

from core.context import ExecutionContext
from features.cat_f_multimodal.feat_35_vision_connector.feature import VisionConnectorFeature

async def run():
    feat = VisionConnectorFeature({"id": "feat_35_vision_connector"})
    pix_path = r"c:\Users\Friends\Desktop\PixabayImages\g8c640dc012a1b79f15c2d05099cb41f1af0227fdb7c9933f0f96524aea1f510c1a6b6377de9d83b4fa3791fddb1c696d49ed647b345c75a1a969e1cfb4efb207_1280.jpg"
    import base64
    with open(pix_path, "rb") as f:
        b64 = base64.b64encode(f.read()).decode("utf-8")
    uri = f"data:image/jpeg;base64,{b64}"
    ctx = ExecutionContext(
        trace_id="test-vision-feat35",
        input_payload={"text": "Visual payload: coffee.jpg", "image": uri},
        flags={"modality": "IMAGE"}
    )
    res = await feat.execute(ctx)
    print("STATUS:", res.metadata.get("vision_connector_status"))
    print("VISUAL PRIMARY:", res.metadata.get("visual_primary_product"))
    print("VISUAL OBJECTS:", res.metadata.get("visual_detected_objects"))
    print("VISUAL COLORS:", res.metadata.get("visual_item_colors"))

asyncio.run(run())
