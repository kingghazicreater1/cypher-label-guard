import os
import sys
import json
import base64
import time
import requests
from PIL import Image

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from tests.clerk_test_utils import ClerkTestAuth

API_BASE = "http://127.0.0.1:8000"

# Setup Clerk test authentication
clerk = ClerkTestAuth(admin_emails="beta_tester@enterprise.test").start()
uid, uemail = clerk.new_identity("beta_tester@enterprise.test")
token = clerk.token(uid, uemail)
headers = clerk.headers(token)

folder1 = r"C:\Users\Friends\Desktop\PixabayImages"
folder2 = r"C:\Users\Friends\Desktop\Pixabay1000"

imgs1 = sorted([os.path.join(folder1, f) for f in os.listdir(folder1) if f.lower().endswith(('.jpg', '.jpeg', '.png', '.webp'))])
imgs2 = sorted([os.path.join(folder2, f) for f in os.listdir(folder2) if f.lower().endswith(('.jpg', '.jpeg', '.png', '.webp'))])

test_files = [imgs1[0], imgs2[0]]

print(f"Testing 2 images pilot:")
for i, path in enumerate(test_files):
    t0 = time.time()
    with Image.open(path) as img:
        w, h = img.size
        fmt = img.format
    
    with open(path, "rb") as f:
        b64 = base64.b64encode(f.read()).decode("utf-8")
    
    data_url = f"data:image/jpeg;base64,{b64}"
    
    payload = {
        "text": f"Analyze specimen {os.path.basename(path)}",
        "modality": "VISION",
        "image_data": data_url,
        "depth_tier": "Fast",
        "criteria": [
            {"name": "Visual Subject", "type": "Free Text", "range": ""},
            {"name": "Human Present", "type": "Binary", "range": "Yes / No"},
            {"name": "Defect or Damage", "type": "Binary", "range": "Pass / Fail"}
        ]
    }
    
    resp = requests.post(f"{API_BASE}/api/v2/infer", json=payload, headers=headers, timeout=60)
    dur = round(time.time() - t0, 2)
    print(f"\n--- Image #{i+1}: {os.path.basename(path)} ---")
    print(f"Dimensions: {w}x{h}, Latency: {dur}s, Status: {resp.status_code}")
    if resp.status_code == 200:
        res = resp.json()
        print("Consensus Label:", res.get("consensus_label"))
        print("Confidence:", res.get("overall_criteria_confidence"))
        print("Criteria:", res.get("criteria_results"))
        annotations = res.get("annotations", [])
        print(f"Annotations count: {len(annotations)}")
        for a in annotations[:3]:
            print(f"  Box: {a.get('label')} -> {a.get('box')}")
    else:
        print("Error:", resp.text)

clerk.stop()
