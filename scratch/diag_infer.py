import sys
sys.path.insert(0, ".")
import base64
import os
import json
from starlette.testclient import TestClient
from api.server import app

client = TestClient(app)

pix_path = r"c:\Users\Friends\Desktop\PixabayImages\g8c640dc012a1b79f15c2d05099cb41f1af0227fdb7c9933f0f96524aea1f510c1a6b6377de9d83b4fa3791fddb1c696d49ed647b345c75a1a969e1cfb4efb207_1280.jpg"
with open(pix_path, "rb") as f:
    b64_str = base64.b64encode(f.read()).decode("utf-8")
uri = f"data:image/jpeg;base64,{b64_str}"

payload = {
    "text": "Visual payload: coffee_pot_and_cookies_set.jpg (115.0 KB)",
    "modality": "IMAGE",
    "depth_tier": "Standard",
    "image_data": uri,
    "criteria": [
        {"name": "product name", "type": "Free Text", "range": "Open item name"},
        {"name": "color", "type": "Free Text", "range": "Open color description"},
        {"name": "quality description", "type": "Free Text", "range": "Physical surface condition"},
    ]
}

resp = client.post("/api/v2/infer", json=payload)
print("STATUS:", resp.status_code)
data = resp.json()["data"]
print("CRITERIA RESULTS:")
print(json.dumps(data["criteria_results"], indent=2))
