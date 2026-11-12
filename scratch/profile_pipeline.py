import sys, os, base64, time, json
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from starlette.testclient import TestClient
from api.server import app
from db.database import init_db
from tests.clerk_test_utils import ClerkTestAuth

init_db()
client = TestClient(app)
clerk = ClerkTestAuth(admin_emails="profiler@enterprise.test").start()
uid, uemail = clerk.new_identity("profiler@enterprise.test")
token = clerk.token(uid, uemail)
headers = clerk.headers(token)

with open("scratch/selected_100_manifest.json", "r") as f:
    manifest = json.load(f)

img_path = manifest[0]["path"]
with open(img_path, "rb") as f:
    b64 = base64.b64encode(f.read()).decode("utf-8")

payload = {
    "text": "Inspect this specimen.",
    "modality": "VISION",
    "image_data": f"data:image/jpeg;base64,{b64}",
    "depth_tier": "Standard",
    "criteria": [
        {"name": "Visual Subject", "type": "Free Text", "range": ""},
        {"name": "Human Present", "type": "Binary", "range": "Yes / No"},
        {"name": "Defect or Damage", "type": "Binary", "range": "Pass / Fail"}
    ]
}

resp = client.post("/api/v2/infer", json=payload, headers=headers)
if resp.status_code == 200:
    data = resp.json()
    trace_id = data.get("trace_id")
    print(f"Status 200, Trace: {trace_id}")
    prove_resp = client.get(f"/api/v2/prove-it/{trace_id}", headers=headers)
    if prove_resp.status_code == 200:
        dossier = prove_resp.json()
        print("Total duration ms:", dossier.get("execution_summary", {}).get("total_duration_ms"))
        steps = dossier.get("lineage_trail", [])
        print(f"Total lineage steps: {len(steps)}")
        for s in steps:
            p = s.get("payload", {})
            if isinstance(p, dict) and "elapsed_ms" in p:
                print(f"  {s.get('step')}: {p.get('elapsed_ms'):.1f} ms")
clerk.stop()
