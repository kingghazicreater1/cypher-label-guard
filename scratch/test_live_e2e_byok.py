import os
from dotenv import load_dotenv
load_dotenv()
import httpx
import json

BASE = "http://127.0.0.1:8000"

print("--- 1. Testing GET /api/v2/keys/status ---")
r = httpx.get(f"{BASE}/api/v2/keys/status")
print("Status code:", r.status_code)
status_data = r.json()
print("Configured providers:", status_data.get("configured_providers"))
print("OpenRouter status:", status_data.get("providers", {}).get("openrouter"))

print("\n--- 2. Testing /api/v2/keys/test with custom model 'liquid/lfm-2.5-2.6b:free' ---")
payload_test = {
    "provider": "openrouter",
    "key": os.getenv("OPENROUTER_API_KEY", ""),
    "model_name": "liquid/lfm-2.5-2.6b:free"
}
r = httpx.post(f"{BASE}/api/v2/keys/test", json=payload_test, timeout=15.0)
print("Test Response:", r.status_code, json.dumps(r.json(), indent=2))

print("\n--- 3. Testing /api/v2/keys/update to activate key & desired model ---")
payload_update = {
    "openrouter_key": os.getenv("OPENROUTER_API_KEY", ""),
    "openrouter_model": "liquid/lfm-2.5-2.6b:free"
}
r = httpx.post(f"{BASE}/api/v2/keys/update", json=payload_update)
print("Update Response:", r.status_code, r.json())

print("\n--- 4. Testing Live /api/v2/infer with Dynamic Criteria ---")
infer_payload = {
    "text": "Luxury Italian Leather Handbag in Navy Blue. Flawlessly crafted, no defects detected.",
    "modality": "TEXT",
    "depth_tier": "Standard",
    "criteria": [
        {"name": "Color", "type": "Enum", "range": "Navy Blue, Black, White, Red"},
        {"name": "Defective?", "type": "Boolean", "range": "Yes / No"},
        {"name": "Quality Score", "type": "Scale", "range": "1-10"},
        {"name": "Estimated Price", "type": "Range", "range": "$100 - $1,000"}
    ]
}
r = httpx.post(f"{BASE}/api/v2/infer", json=infer_payload, timeout=60.0)
print("Infer Status:", r.status_code)
if r.status_code == 200:
    res = r.json()
    unified = res.get("data", {})
    decision = unified.get("consensus", {}).get("decision")
    print("Parliament Decision:", decision)
    crit_list = res.get("criteria_results") or res.get("data", {}).get("criteria_results") or []
    print(f"Total Criteria Results ({len(crit_list)}):")
    for crit in crit_list:
        print(f"  * {crit['name']} ({crit['type']}): {crit['value']} (Confidence: {crit['confidence']}%, Agreement: {crit['agreement']})")
        print(f"    Provider Votes: {crit.get('votes')}")
else:
    print("Infer Error:", r.text)
