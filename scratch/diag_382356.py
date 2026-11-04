import sys
sys.path.insert(0, ".")
import base64
import numpy as np
import cv2
import json
from starlette.testclient import TestClient
from api.server import app

client = TestClient(app)

img = np.full((400, 600, 3), 240, dtype=np.uint8)
cv2.rectangle(img, (50, 100), (350, 300), (80, 80, 80), -1)
cv2.rectangle(img, (70, 120), (330, 260), (30, 30, 30), -1)
cv2.circle(img, (450, 200), 50, (30, 30, 210), -1)
cv2.rectangle(img, (380, 270), (430, 370), (20, 20, 20), -1)
cv2.circle(img, (500, 320), 25, (25, 25, 25), -1)

_, buf = cv2.imencode(".jpg", img)
b64_str = base64.b64encode(buf.tobytes()).decode("utf-8")
uri = f"data:image/jpeg;base64,{b64_str}"

payload = {
    "text": "Visual payload: desk_setup_with_laptop_apple_phone.jpg (85.0 KB)",
    "modality": "IMAGE",
    "depth_tier": "Standard",
    "image_data": uri,
    "criteria": [
        {"name": "products in image", "type": "Free Text", "range": "Open item list"},
        {"name": "their colors", "type": "Free Text", "range": "Open color description"},
        {"name": "estimated price", "type": "Free Text", "range": "Open price estimate"},
    ]
}

resp = client.post("/api/v2/infer", json=payload)
data = resp.json()["data"]
print("CRITERIA RESULTS:")
print(json.dumps(data["criteria_results"], indent=2))
