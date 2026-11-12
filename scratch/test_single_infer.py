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
print("Sending test request to /api/v2/infer for Image 1...")
resp = client.post("/api/v2/infer", json=payload)
dur = round(time.time() - t0, 2)
print(f"Status Code: {resp.status_code} in {dur}s")

if resp.status_code == 200:
    res = resp.json()
    data = res.get("data", {})
    print("Consensus Decision:", data.get("decision"))
    print("Votes:", data.get("votes"))
    print("Overall Criteria Confidence:", data.get("overall_criteria_confidence"))
    print("\nCriteria Results:")
    for c in data.get("criteria_results", []):
        print(f"  - {c.get('name')}: {c.get('value')} (Conf: {c.get('confidence')}%, Anomaly: {c.get('anomaly')})")
    print("\nVisual Metadata:")
    meta = data.get("metadata", {})
    print("  Visual Primary:", meta.get("visual_primary_product"))
    print("  Visual Objects:", meta.get("visual_detected_objects"))
    print("  Bounding Boxes Count:", len(meta.get("visual_bounding_boxes", [])))
else:
    print("Error:", resp.text[:400])
