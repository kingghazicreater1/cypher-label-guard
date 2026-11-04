import sqlite3
import httpx
import json
import sys

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

conn = sqlite3.connect("cypher_label_guard.db")
c = conn.cursor()
row = c.execute("SELECT image_url FROM job_records WHERE job_number='470474'").fetchone()
if not row or not row[0]:
    print("Could not find image_url from Job 470474")
    sys.exit(1)

img_b64 = row[0]

# Clearly specified, unambiguous headings:
clear_criteria = [
    {"name": "brand name", "type": "Free Text"},
    {"name": "product line", "type": "Free Text"},
    {"name": "product type", "type": "Enum", "range": "Cologne / Perfume, Body Wash, Lotion, Shampoo"},
    {"name": "bottle material", "type": "Enum", "range": "Glass, Plastic, Metal, Ceramic"},
    {"name": "countertop surface material", "type": "Free Text"},
    {"name": "primary bottle color", "type": "Free Text"},
    {"name": "cap color", "type": "Free Text"},
    {"name": "cap shape", "type": "Enum", "range": "Round / Spherical, Square, Cylindrical, Flat"},
    {"name": "logo description", "type": "Free Text"},
    {"name": "text printed on bottle", "type": "Free Text"},
    {"name": "target audience", "type": "Enum", "range": "Men, Women, Unisex, Children"},
    {"name": "key visual feature", "type": "Free Text"},
    {"name": "product condition", "type": "Enum", "range": "Pristine, Damaged, Used, Expired"}
]

payload = {
    "text": "Visual payload: g1e081829c9619b666a9a614f04669f8dfd6d91ee9a91f3022586e54147e34cc",
    "image_data": img_b64,
    "modality": "IMAGE",
    "depth": "Standard",
    "criteria": clear_criteria
}

print(f"Submitting {len(clear_criteria)} clear headings to /api/v2/infer...")
try:
    r = httpx.post("http://127.0.0.1:8000/api/v2/infer", json=payload, timeout=45.0)
    print("Status:", r.status_code)
    if r.status_code == 200:
        data = r.json()
        print(f"\n==========================================")
        print(f"OVERALL CONFIDENCE: {data.get('overall_criteria_confidence')}%")
        print(f"==========================================")
        crit_res = data.get("criteria_results") or []
        for c in crit_res:
            print(f"\n[{c.get('name')}] ({c.get('type')})")
            print(f"  Consensus: {c.get('value')}")
            print(f"  Confidence: {c.get('confidence')}% | Agreement: {c.get('agreement')}")
            votes = c.get("votes") or {}
            for voter, val in votes.items():
                print(f"    - {voter}: {val}")
    else:
        print("Error:", r.text[:300])
except Exception as e:
    print("Exception:", e)
