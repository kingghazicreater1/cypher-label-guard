import json
import time
import urllib.request

def test_batch_and_keys():
    print("=" * 60)
    print("TESTING BYOK & BATCH INGESTION (1,000 ITEMS)")
    print("=" * 60)

    # 1. Test Keys Status
    req = urllib.request.urlopen("http://127.0.0.1:8000/api/v2/keys/status")
    k_status = json.loads(req.read().decode())
    print("\n[1] Multi-Model BYOK Status:")
    for prov, info in k_status["providers"].items():
        print(f"  - {info['name']:<18}: {info['model_snapshot']} | Mode: {info['mode']}")

    # 2. Test Key Ping Diagnostic
    test_req = urllib.request.Request(
        "http://127.0.0.1:8000/api/v2/keys/test",
        data=json.dumps({"provider": "all"}).encode(),
        headers={"Content-Type": "application/json"}
    )
    t_resp = json.loads(urllib.request.urlopen(test_req).read().decode())
    print("\n[2] Diagnostic Ping Results:")
    for p, res in t_resp["results"].items():
        print(f"  - {p.upper():<8}: Status: {res['status']} | Latency: {res.get('latency_ms', 0)}ms")

    # 3. Test Sample Dataset Generation (1,000 E-Commerce Products)
    req = urllib.request.urlopen("http://127.0.0.1:8000/api/v2/batch/sample/ecommerce")
    sample_data = json.loads(req.read().decode())
    print(f"\n[3] Generated Sample E-Commerce Catalog: {sample_data['row_count']} rows.")

    # 4. Start Batch Processing with Dynamic Criteria
    # Test with first 15 rows for fast validation
    lines = sample_data["csv_text"].strip().split("\n")
    subset_csv = "\n".join(lines[:16])  # Header + 15 rows

    batch_payload = {
        "name": "1,000 Products Catalog Batch Run",
        "csv_text": subset_csv,
        "target_column": "Product_Description",
        "criteria": [
            {"name": "Color", "type": "Enum", "range": "Red, Blue, Green, Black, White"},
            {"name": "Price Tier", "type": "Enum", "range": "Budget, Mid, Premium"},
            {"name": "Quality", "type": "Scale", "range": "1-10"},
            {"name": "Defective?", "type": "Boolean", "range": "Yes / No"},
            {"name": "Rejection Reason", "type": "Free Text", "range": "Max 200 chars"}
        ],
        "depth_tier": "Fast",
    }

    start_req = urllib.request.Request(
        "http://127.0.0.1:8000/api/v2/batch/start",
        data=json.dumps(batch_payload).encode(),
        headers={"Content-Type": "application/json"}
    )
    batch_resp = json.loads(urllib.request.urlopen(start_req).read().decode())
    batch_id = batch_resp["batch_id"]
    print(f"\n[4] Started Batch #{batch_id}: {batch_resp['message']}")

    # 5. Poll Progress until Complete
    for _ in range(25):
        time.sleep(0.5)
        st_req = urllib.request.urlopen(f"http://127.0.0.1:8000/api/v2/batch/status/{batch_id}")
        st = json.loads(st_req.read().decode())
        print(f"  -> Progress: {st['completed_rows']}/{st['total_rows']} ({st['progress_pct']}%) | Confidence: {st['overall_confidence']}%")
        if st["status"] == "COMPLETED":
            break

    assert st["status"] == "COMPLETED", "Batch did not finish in time"

    # 6. Test CSV Download
    dl_req = urllib.request.urlopen(f"http://127.0.0.1:8000/api/v2/batch/download/{batch_id}")
    csv_out = dl_req.read().decode()
    header_line = csv_out.split("\n")[0]
    print(f"\n[5] Labeled CSV Download Verified ({len(csv_out)} bytes):")
    print(f"  Headers: {header_line}")

    assert "Color" in header_line
    assert "Color_Confidence" in header_line
    assert "Overall_Confidence" in header_line
    assert "Parliament_Decision" in header_line

    print("\n[OK] ALL BATCH AND KEY VALIDATION TESTS PASSED!")

if __name__ == "__main__":
    test_batch_and_keys()
