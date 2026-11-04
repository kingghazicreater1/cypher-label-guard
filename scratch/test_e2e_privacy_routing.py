import requests
import json

BASE_URL = "http://127.0.0.1:8000"

def test_e2e_circular_trap():
    print("[*] E2E Test 1: Submitting PII Audit Task to /api/v2/infer...")
    payload = {
        "text": "Payload: customer_receipt.jpg (100 KB)",
        "modality": "IMAGE",
        "criteria": [
            {"name": "Audit PII and detect credit card", "type": "Free Text", "range": "Open"}
        ]
    }
    r = requests.post(f"{BASE_URL}/api/v2/infer", json=payload)
    assert r.status_code == 200, f"Expected 200, got {r.status_code}"
    res = r.json()
    print(f"Execution Plane: {res.get('execution_plane')}")
    print(f"Routing Reason: {res.get('routing_reason')}")
    assert res.get("execution_plane") == "CIRCULAR_TRAP"
    print("[PASS] E2E Test 1 PASSED: Circularity detected and routed to CIRCULAR_TRAP!\n")

def test_e2e_audio_enclave_default():
    print("[*] E2E Test 2: Submitting Audio Task to /api/v2/infer...")
    payload = {
        "text": "Audio track payload: sample.wav (500 KB)",
        "modality": "AUDIO",
        "criteria": [
            {"name": "language identification", "type": "Free Text", "range": "Open"}
        ]
    }
    r = requests.post(f"{BASE_URL}/api/v2/infer", json=payload)
    assert r.status_code == 200, f"Expected 200, got {r.status_code}"
    res = r.json()
    print(f"Execution Plane: {res.get('execution_plane')}")
    print(f"Routing Reason: {res.get('routing_reason')}")
    assert res.get("execution_plane") == "ENCLAVE_REQUIRED"
    print("[PASS] E2E Test 2 PASSED: Audio defaulted to ENCLAVE_REQUIRED pending feasibility spike!\n")

def test_e2e_blind_inference_execution():
    print("[*] E2E Test 3: Submitting Structural Defect Task on 22.PNG to /api/v2/infer...")
    payload = {
        "text": "Visual payload: 22.PNG (60.6 KB)",
        "modality": "IMAGE",
        "criteria": [
            {"name": "surface scratch", "type": "Enum", "range": "None, Minor, Severe"}
        ]
    }
    r = requests.post(f"{BASE_URL}/api/v2/infer", json=payload)
    assert r.status_code == 200, f"Expected 200, got {r.status_code}"
    res = r.json()
    print(f"Execution Plane: {res.get('execution_plane')}")
    print(f"Policy Hash: {res.get('policy_hash')}")
    print(f"Anomaly Detected: {res.get('anomaly_detected')}")
    assert res.get("execution_plane") == "BLIND_ELIGIBLE"
    assert res.get("policy_hash", "").startswith("sha256:")
    assert res.get("anomaly_detected") is False
    print("[PASS] E2E Test 3 PASSED: Blind inference cleared with SHA-256 policy hash and clean consensus!\n")

if __name__ == "__main__":
    try:
        test_e2e_circular_trap()
        test_e2e_audio_enclave_default()
        test_e2e_blind_inference_execution()
        print("=======================================================")
        print("[SUCCESS] ALL E2E PRIVACY ROUTING TESTS PASSED!")
        print("=======================================================")
    except Exception as e:
        print(f"\n[FAIL] E2E TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
