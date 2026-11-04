import httpx
import json
import sys

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

text = (
    "On 18 June 2024, at 09:14 AM, Horizon Bank customer service sent an urgent email from the address alerts@secure-update-portal.com to Mr. Samuel Ade. "
    "The email claimed that a suspicious login attempt was detected on 17 June 2024 at 02:45 AM from Lagos, Nigeria. "
    "The message stated that an unauthorized transfer of ₦450,000 had been blocked, but threatened that the account would be permanently frozen within 24 hours "
    "unless Mr. Ade verified his identity by clicking a link. Mr. Ade was instructed to pay a ₦15,000 security fee to reverse the block. "
    "The email was signed by Mr. David Okon, Head of Security, but Mr. Ade ignored it and reported the message to the real Horizon Bank fraud team at 11:00 AM."
)

criteria = [
    {"name": "PERSON", "type": "Free Text"},
    {"name": "ORGANIZATION", "type": "Free Text"},
    {"name": "DATE", "type": "Free Text"},
    {"name": "TIME", "type": "Free Text"},
    {"name": "MONEY", "type": "Free Text"},
    {"name": "POLICY/THREAT", "type": "Free Text"},
    {"name": "EVENT", "type": "Free Text"}
]

payload = {
    "text": text,
    "depth": "Standard",
    "criteria": criteria
}

try:
    r = httpx.post("http://127.0.0.1:8000/api/v2/infer", json=payload, timeout=40.0)
    print("Status:", r.status_code)
    if r.status_code == 200:
        data = r.json()
        print(f"Overall confidence: {data.get('overall_criteria_confidence')}%")
        for c in data.get("criteria_results", []):
            print(f"=== {c.get('name')} ===")
            print("Value:", c.get("value"))
            print("Confidence:", c.get("confidence"))
            print("Agreement:", c.get("agreement"))
    else:
        print("Error:", r.text)
except Exception as e:
    print("Exception:", e)
