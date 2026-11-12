import os, sys, json, base64, time
from dotenv import load_dotenv
load_dotenv()

os.environ["ALLOW_GUEST_INFERENCE"] = "true"
sys.path.insert(0, r"c:\Users\Friends\Desktop\AV GUARDIAN")

from starlette.testclient import TestClient
from api.server import app

client = TestClient(app)

with open(r"c:\Users\Friends\Desktop\AV GUARDIAN\scratch\fresh10_list.json") as f:
    items = json.load(f)

first = items[0]
with open(first["path"], "rb") as f:
    b64 = base64.b64encode(f.read()).decode("utf-8")

payload = {
    "text": "Industrial Specimen: " + first["filename"][:30],
    "modality": "IMAGE",
    "depth_tier": "Standard",
    "image_data": f"data:image/jpeg;base64,{b64}",
    "criteria": [
        {"name": "Product Name", "type": "Free Text", "range": "Primary item name"},
        {"name": "Category", "type": "Enum", "range": "Food, Beauty, Fashion, Automotive, Electronics, Eyewear, Nature, Other"},
        {"name": "Color", "type": "Free Text", "range": "Dominant color"},
        {"name": "Human Present", "type": "Boolean", "range": "Yes / No"}
    ]
}

t0 = time.time()
resp = client.post("/api/v2/infer", json=payload)
dur = round(time.time() - t0, 2)

if resp.status_code == 200:
    res = resp.json()
    print("SUCCESS in", dur, "s")
    print("Annotations:", json.dumps(res.get("annotations"), indent=2))
    print("Consensus:", json.dumps(res.get("data", {}).get("consensus"), indent=2))
