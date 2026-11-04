import urllib.request
import json

payload = {
    "text": "Severe defect in medical device batch: cracked insulin seal leaking fluid.",
    "modality": "TEXT",
    "depth_tier": "Standard",
    "tenant_id": "health_audit_org"
}

req = urllib.request.Request(
    "http://127.0.0.1:8000/api/v2/infer",
    data=json.dumps(payload).encode("utf-8"),
    headers={"Content-Type": "application/json"}
)

with urllib.request.urlopen(req, timeout=15) as resp:
    res = json.loads(resp.read().decode())
    print("Response Root Keys:", list(res.keys()))
    print("Trace ID:", res.get("trace_id"))
    print("Execution Time:", res.get("execution_time_seconds"), "s")
    print("Features Executed Count:", len(res.get("features_executed", [])))
    
    # Check parliamentary / consensus decision fields
    for k, v in res.items():
        if k not in ["features_executed", "trace_id", "execution_time_seconds"]:
            if isinstance(v, dict):
                print(f"\n[{k}] (dict):", list(v.keys()))
                for sub_k, sub_v in v.items():
                    if not isinstance(sub_v, (dict, list)) or len(str(sub_v)) < 120:
                        print(f"  - {sub_k}: {sub_v}")
            elif isinstance(v, list):
                print(f"\n[{k}] (list of {len(v)} items)")
            else:
                print(f"[{k}]: {v}")
