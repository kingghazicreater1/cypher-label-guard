import httpx, json

payload = {
    "text": "a donkey reading books",
    "criteria": [
        {"name": "animal in sentence", "type": "Free Text", "range": ""},
        {"name": "type of sentence", "type": "Free Text", "range": ""},
        {"name": "what donkey is reading", "type": "Free Text", "range": ""},
    ]
}

r = httpx.post("http://127.0.0.1:8000/api/v2/infer", json=payload, timeout=30.0)
print("STATUS:", r.status_code)
data = r.json()
crit = data.get("criteria_results", [])
print(f"Total Criteria Results: {len(crit)}")
print(f"Overall Confidence: {data.get('overall_criteria_confidence')}%")
print("\n--- RESULTS RETURNED BY API ---")
for c in crit:
    name = c["name"]
    val = c["value"]
    agree = c["agreement"]
    conf = c["confidence"]
    print(f"  {name:<28} -> {val:<18} (Conf: {conf}%, Agreement: {agree})")
