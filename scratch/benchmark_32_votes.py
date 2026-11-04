import sys
import time
import requests
import statistics

if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

BASE_URL = "http://127.0.0.1:8000"

# 1. Login
login_payload = {"email": "ghazi@cypherlabelguard.ai", "password": "GuardianPass2026!"}
res = requests.post(f"{BASE_URL}/api/v2/auth/login", json=login_payload)
token = res.json()["token"]
headers = {"Authorization": f"Bearer {token}"}

latencies = []
print("Measuring 25 full pipeline Deep Mode (32 votes) runs...")

for i in range(25):
    payload = {
        "text": f"Benchmark sample #{i}: Multi-modal telemetry stream evaluating forensic integrity under heavy load.",
        "depth_tier": "Deep",
        "subspace_method": "majority",
    }
    t0 = time.perf_counter()
    r = requests.post(f"{BASE_URL}/api/v2/infer", json=payload, headers=headers)
    t1 = time.perf_counter()
    assert r.status_code == 200, f"Error: {r.text}"
    elapsed_ms = (t1 - t0) * 1000.0
    latencies.append(elapsed_ms)
    print(f"Run {i+1:02d}: {elapsed_ms:.2f} ms (Votes: {len(r.json()['parliament_grid'])})")

latencies.sort()
n = len(latencies)
p50 = statistics.median(latencies)
p95 = latencies[int(0.95 * n)]
p99 = latencies[int(0.99 * n)]
avg = statistics.mean(latencies)

print("\n" + "=" * 50)
print(f"BENCHMARK RESULTS (25 Real Pipeline Passes):")
print(f"Min:  {min(latencies):.2f} ms")
print(f"p50:  {p50:.2f} ms")
print(f"Avg:  {avg:.2f} ms")
print(f"p95:  {p95:.2f} ms")
print(f"p99:  {p99:.2f} ms")
print(f"Max:  {max(latencies):.2f} ms")
print("=" * 50)
