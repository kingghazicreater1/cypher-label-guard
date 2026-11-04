import requests
import json

BASE_URL = "http://127.0.0.1:8000"

def test_video_payload_in_image_pipeline_rejected():
    print("[*] Test 1: Submitting Video container to IMAGE pipeline (Job #706533 reproduction)...")
    payload = {
        "text": "Video container payload: WIN_20260830_21_50_59_Pro.mp4 (1.14 MB, H.264/AVC)",
        "modality": "IMAGE",
        "criteria": [
            {"name": "product name", "type": "Free Text", "range": "Open"}
        ]
    }
    r = requests.post(f"{BASE_URL}/api/v2/infer", json=payload)
    print(f"Status: {r.status_code}")
    print(f"Response: {r.text[:120]}...")
    assert r.status_code == 400, f"Expected 400 Bad Request, got {r.status_code}"
    assert "Modality mismatch" in r.text
    print("[PASS] TEST 1 PASSED: Video container rejected in IMAGE pipeline with 400 Bad Request!\n")

def test_image_payload_in_video_pipeline_rejected():
    print("[*] Test 2: Submitting Static Image to VIDEO pipeline...")
    payload = {
        "text": "Visual payload: 22.PNG (60.6 KB)",
        "modality": "VIDEO",
        "criteria": [
            {"name": "product name", "type": "Free Text", "range": "Open"}
        ]
    }
    r = requests.post(f"{BASE_URL}/api/v2/infer", json=payload)
    print(f"Status: {r.status_code}")
    print(f"Response: {r.text[:120]}...")
    assert r.status_code == 400, f"Expected 400 Bad Request, got {r.status_code}"
    assert "Modality mismatch" in r.text
    print("[PASS] TEST 2 PASSED: Static image rejected in VIDEO pipeline with 400 Bad Request!\n")

def test_generic_fallback_rejection_and_deconfidence():
    print("[*] Test 3: Verifying unverified fallback is marked ANOMALY with 0% confidence...")
    payload = {
        "text": "Video container payload: unlabeled_stream.mp4 (5.2 MB, H.264/AVC)",
        "modality": "VIDEO",
        "criteria": [
            {"name": "product name", "type": "Free Text", "range": "Open"}
        ]
    }
    r = requests.post(f"{BASE_URL}/api/v2/infer", json=payload)
    assert r.status_code == 200, f"Expected 200, got {r.status_code}"
    res = r.json()
    crit = res.get("criteria_results", [{}])[0]
    val = crit.get("value")
    conf = crit.get("confidence")
    anom = res.get("anomaly_detected")
    guard = res.get("guard_fired")

    print(f"Criteria Value: '{val}'")
    print(f"Confidence: {conf}%")
    print(f"Anomaly Detected: {anom}")
    print(f"Guard Fired: {guard}")

    assert "[UNVERIFIED" in str(val) or "[REJECTED" in str(val), f"Expected UNVERIFIED/REJECTED, got {val}"
    assert conf == 0.0, f"Expected 0.0% confidence, got {conf}"
    assert anom is True, "Expected anomaly_detected to be True"
    assert guard == "GENERIC_FALLBACK_UNVERIFIED", f"Expected GENERIC_FALLBACK_UNVERIFIED, got {guard}"
    print("[PASS] TEST 3 PASSED: Fallback output trapped as ANOMALY with 0% confidence and revoked QA pass!\n")

if __name__ == "__main__":
    try:
        test_video_payload_in_image_pipeline_rejected()
        test_image_payload_in_video_pipeline_rejected()
        test_generic_fallback_rejection_and_deconfidence()
        print("=======================================================")
        print("[SUCCESS] ALL JOB #706533 REGRESSION TESTS PASSED!")
        print("=======================================================")
    except Exception as e:
        print(f"\n[FAIL] REGRESSION TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
