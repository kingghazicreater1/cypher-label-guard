import requests
import base64

pix_path = r"c:\Users\Friends\Desktop\PixabayImages\g8c640dc012a1b79f15c2d05099cb41f1af0227fdb7c9933f0f96524aea1f510c1a6b6377de9d83b4fa3791fddb1c696d49ed647b345c75a1a969e1cfb4efb207_1280.jpg"
with open(pix_path, "rb") as f:
    b64_str = base64.b64encode(f.read()).decode("utf-8")
data_uri = f"data:image/jpeg;base64,{b64_str}"

payload = {
    "text": "Visual payload: coffee_pot_and_cookies_set.jpg (115.0 KB)",
    "modality": "IMAGE",
    "depth_tier": "Standard",
    "image_data": data_uri,
    "criteria": [
        {"name": "product name", "type": "Free Text", "range": "Open item name"},
        {"name": "color", "type": "Free Text", "range": "Open color description"},
        {"name": "quality description", "type": "Free Text", "range": "Physical surface condition"},
    ]
}

resp = requests.post("http://127.0.0.1:8000/api/v2/infer", json=payload, timeout=60)
print("STATUS:", resp.status_code)
data = resp.json()
print("SUCCESS:", data.get("success"))
for c in data.get("data", {}).get("criteria_results", []):
    print(f"CRITERIA: {c['name']} -> {c['value']} ({c.get('confidence', 0)*100:.1f}%) | anomaly: {c.get('anomaly')}")
print("OVERALL DECISION:", data.get("data", {}).get("parliament_decision"))
