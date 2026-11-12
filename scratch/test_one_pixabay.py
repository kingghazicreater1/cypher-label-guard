import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import base64
from starlette.testclient import TestClient
from api.server import app
from db.database import init_db
from tests.clerk_test_utils import ClerkTestAuth

init_db()
client = TestClient(app)
clerk = ClerkTestAuth(admin_emails="tester@enterprise.test").start()
uid, uemail = clerk.new_identity("tester@enterprise.test")
token = clerk.token(uid, uemail)
headers = clerk.headers(token)

img_folder = r"C:\Users\Friends\Desktop\PixabayImages"
images = [f for f in os.listdir(img_folder) if f.lower().endswith(('.jpg', '.jpeg', '.png', '.webp'))]
first_img_path = os.path.join(img_folder, images[0])
print(f"Testing on image: {images[0]} (Path: {first_img_path})")

with open(first_img_path, "rb") as f:
    b64 = base64.b64encode(f.read()).decode("utf-8")

data_url = f"data:image/jpeg;base64,{b64}"

payload = {
    "text": "Inspect this specimen image.",
    "modality": "VISION",
    "image_data": data_url,
    "depth_tier": "Fast",
    "criteria": [
        {"name": "Visual Subject", "type": "Free Text", "range": ""},
        {"name": "Damage or Defect", "type": "Binary", "range": "Pass / Fail"},
        {"name": "Human Present", "type": "Binary", "range": "Yes / No"}
    ]
}

resp = client.post("/api/v2/infer", json=payload, headers=headers)
print(f"Status Code: {resp.status_code}")
data = resp.json()
print("Consensus Label:", data.get("consensus_label"))
print("Affirmative Votes:", data.get("affirmative_votes"))
print("Confidence:", data.get("overall_criteria_confidence"))
print("Criteria Results:", data.get("criteria_results"))
print("Annotations:", data.get("annotations"))
clerk.stop()
