"""Real-key paced batch test: 10 human-verified images through the real batch endpoint.

Proves (or disproves) that the auto-pacer lets a batch finish without losing items to HTTP 429.
Run:  python scratch/run_paced_batch_test.py
"""
import base64
import json
import os
import sys
import time

from dotenv import load_dotenv

load_dotenv()
sys.stdout.reconfigure(line_buffering=True)
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from starlette.testclient import TestClient  # noqa: E402

from api.server import app  # noqa: E402
from core.provider_pacer import pacer  # noqa: E402
from tests.clerk_test_utils import ClerkTestAuth  # noqa: E402

IMG_DIR = os.path.join(os.path.dirname(__file__), "..", "verified_10_images")
# Human ground truth (same eyes-on labels as scratch/run_10_images_verified_benchmark.py)
GT = {
    "01_white_eggs.jpg": ("Food", "No"),
    "02_polo_cologne.jpg": ("Beauty", "No"),
    "03_car_tires.jpg": ("Automotive", "No"),
    "04_smartphone_amazon.jpg": ("Electronics", "Yes"),
    "05_woman_gold_necklace.jpg": ("Fashion", "Yes"),
    "06_nike_sneaker.jpg": ("Fashion", "No"),
    "07_brown_eggs.jpg": ("Food", "No"),
    "08_cheese_wheels.jpg": ("Food", "No"),
    "09_pyracantha_berries.jpg": ("Nature", "No"),
    "10_eyeglasses.jpg": ("Eyewear", "No"),
}

files = sorted(f for f in os.listdir(IMG_DIR) if f.endswith(".jpg"))
images = []
for f in files:
    with open(os.path.join(IMG_DIR, f), "rb") as fh:
        images.append({"name": f, "data": "data:image/jpeg;base64," + base64.b64encode(fh.read()).decode()})

criteria = [
    {"name": "Product Name", "type": "Free Text", "range": "Primary item name"},
    {"name": "Category", "type": "Enum", "range": "Food, Beauty, Fashion, Automotive, Electronics, Eyewear, Nature, Other"},
    {"name": "Color", "type": "Free Text", "range": "Dominant color"},
    {"name": "Human Present", "type": "Boolean", "range": "Yes / No"},
]

clerk = ClerkTestAuth(admin_emails="paced-test-admin@example.test").start()
uid, mail = clerk.new_identity()
token = clerk.token(uid, mail, exp=int(time.time()) + 7200)
headers = clerk.headers(token)

print(f"PROVIDER_TIER={os.getenv('PROVIDER_TIER', 'free')}  images={len(images)}  headings={len(criteria)}")
t0 = time.time()
with TestClient(app) as client:
    r = client.post("/api/v2/batch/images/start", headers=headers, json={
        "name": "Paced batch test", "folder_name": "PacerTest", "depth_tier": "Standard",
        "criteria": criteria, "images": images,
    })
    print("start:", r.status_code, {k: v for k, v in r.json().items() if k != "detail"} if r.status_code == 200 else r.text[:300])
    if r.status_code != 200:
        clerk.stop()
        sys.exit(1)
    bid = r.json()["batch_id"]

    last = ""
    s = {}
    while True:
        resp = client.get(f"/api/v2/batch/images/status/{bid}", headers=headers)
        if resp.status_code == 401:
            token = clerk.token(uid, mail, exp=int(time.time()) + 7200)
            headers = clerk.headers(token)
            time.sleep(3)
            continue
        if resp.status_code != 200:
            print(f"[{time.time() - t0:5.0f}s] status HTTP {resp.status_code}: {resp.text[:200]}")
            time.sleep(5)
            continue
        s = resp.json()
        line = f"[{time.time() - t0:5.0f}s] {s.get('progress_message')} | done={s.get('done')} failed={s.get('failed')}"
        if line != last:
            print(line)
            last = line
        if s.get("status") in ("COMPLETED", "FAILED"):
            break
        if time.time() - t0 > 1800:
            print("TIMEOUT")
            break
        time.sleep(8)

clerk.stop()
total_s = round(time.time() - t0, 1)

rows = []
cat_ok = human_ok = 0
for it in s.get("items", []):
    crit = {c.get("name"): c.get("value") for c in (it.get("criteria_results") or [])}
    exp_cat, exp_h = GT.get(it["name"], ("?", "?"))
    c_ok = str(crit.get("Category", "")).lower() == exp_cat.lower()
    h_ok = str(crit.get("Human Present", "")).strip().lower() == exp_h.lower()
    cat_ok += c_ok
    human_ok += h_ok
    rows.append({"image": it["name"], "status": it["status"], "decision": it.get("decision"),
                 "votes": it.get("votes"), "seconds": it.get("seconds"), "values": crit,
                 "expected": {"Category": exp_cat, "Human Present": exp_h},
                 "category_match": c_ok, "human_match": h_ok, "error": it.get("error")})

completed = sum(1 for r_ in rows if r_["status"] == "COMPLETED")
summary = {
    "batch_status": s["status"], "total_seconds": total_s, "completed": completed,
    "failed": s["failed"], "category_match": f"{cat_ok}/{len(rows)}", "human_match": f"{human_ok}/{len(rows)}",
    "pacer": pacer.stats(),
}
print("\n=== SUMMARY ===")
print(json.dumps(summary, indent=2))
for r_ in rows:
    print(f"{r_['image']:<28} {r_['status']:<10} {str(r_['decision']):<22} votes={r_['votes']} "
          f"cat={'OK' if r_['category_match'] else 'X '} human={'OK' if r_['human_match'] else 'X '} "
          f"name={r_['values'].get('Product Name')}")

out = os.path.join(os.path.dirname(__file__), "paced_batch_test_results.json")
with open(out, "w", encoding="utf-8") as fp:
    json.dump({"summary": summary, "rows": rows}, fp, indent=2)
print("saved", out)
