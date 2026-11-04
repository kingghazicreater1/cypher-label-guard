import urllib.request
import json
import time

payload = {
    "text": "Severe defect in medical device batch: cracked insulin seal leaking fluid.",
    "modality": "TEXT",
    "depth_tier": "Fast",
    "tenant_id": "health_audit_org"
}

req = urllib.request.Request(
    "http://127.0.0.1:8000/api/v2/infer",
    data=json.dumps(payload).encode("utf-8"),
    headers={"Content-Type": "application/json"}
)

t0 = time.time()
print("[*] Sending Fast inference request to http://127.0.0.1:8000/api/v2/infer...")
try:
    with urllib.request.urlopen(req, timeout=40) as resp:
        res = json.loads(resp.read().decode())
        dt = time.time() - t0
        print(f"[OK] Response received in {dt:.2f}s (HTTP {resp.status})")
        print("Trace ID:", res.get("trace_id"))
        print("Modality:", res.get("modality"))
        print("Consensus Label:", res.get("consensus_label") or (res.get("output") or {}).get("primary_label"))
        print("Root Keys:", list(res.keys()))
        if "output" in res:
            print("Output object:", res["output"])
except Exception as e:
    print(f"[ERR] Failed: {e}")
