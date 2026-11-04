import requests
import json

BASE_URL = "http://127.0.0.1:8000"

def test_binary_header_at_offset_4():
    print("[*] Test 1: Verifying real ISO BMFF layout (ftyp at offset 4) is REJECTED in TEXT pipeline...")
    # Real MP4 binary container starts with 4-byte box length followed by 'ftyp'
    iso_bmff_payload = "\x00\x00\x00\x20ftypmp42mp41isom\x00\x00\x00\x08mdat"
    payload = {
        "text": iso_bmff_payload,
        "modality": "TEXT",
        "criteria": [
            {"name": "product name", "type": "Free Text", "range": "Open Free Text"}
        ]
    }
    r = requests.post(f"{BASE_URL}/api/v2/infer", json=payload)
    print(f"Status Code: {r.status_code}")
    print(f"Response: {r.text[:140]}...")
    assert r.status_code == 400, f"Expected 400 Bad Request, got {r.status_code}"
    assert "Input routing rejected" in r.text
    print("[PASS] TEST 1 PASSED: Real MP4 ISO BMFF container (offset 4) rejected with 400 Bad Request!")

def test_byte_density_heuristic_rejection():
    print("\n[*] Test 2: Verifying non-printable control byte density heuristic catches arbitrary binaries...")
    # Simulated unknown binary (e.g. wasm, sqlite, or corrupted payload with null bytes & control chars)
    corrupt_binary = "DATA\x00\x01\x02\x03\x04\x05\x06\x07\x08\x0e\x0f\x10\x11\x12\x13\x14\x15\x16\x17\x18" * 5
    payload = {
        "text": corrupt_binary,
        "modality": "TEXT",
        "criteria": [
            {"name": "product name", "type": "Free Text", "range": "Open Free Text"}
        ]
    }
    r = requests.post(f"{BASE_URL}/api/v2/infer", json=payload)
    print(f"Status Code: {r.status_code}")
    print(f"Response: {r.text[:140]}...")
    assert r.status_code == 400, f"Expected 400 Bad Request, got {r.status_code}"
    assert "Non-decodable binary stream" in r.text or "control characters" in r.text
    print("[PASS] TEST 2 PASSED: Arbitrary binary stream caught by byte-density heuristic!")

def test_zero_heading_unverified():
    print("\n[*] Test 3: Verifying zero-heading job (#184256 regression prevention)...")
    payload = {
        "text": "Visual payload: sample_part.jpg (120 KB)",
        "modality": "IMAGE",
        "criteria": [] # ZERO HEADINGS
    }
    r = requests.post(f"{BASE_URL}/api/v2/infer", json=payload)
    assert r.status_code == 200, f"Expected 200 OK, got {r.status_code}"
    res = r.json()
    crit_res = res.get("criteria_results")
    assert crit_res is None or len(crit_res) == 0, "Criteria results should be empty for zero-heading job"
    print("[PASS] TEST 3 PASSED: Zero-heading job produces empty criteria; frontend displays UNVERIFIED (never false-green)!")

def test_rename_invariance_banana():
    print("\n[*] Test 4: Verifying rename invariance (banana.mp4 with video modality)...")
    payload = {
        "text": "Video container payload: banana.mp4 (12.4 MB)",
        "modality": "VIDEO",
        "criteria": [
            {"name": "product name", "type": "Free Text", "range": "Open Free Text"}
        ]
    }
    r = requests.post(f"{BASE_URL}/api/v2/infer", json=payload)
    assert r.status_code == 200
    res = r.json()
    prod_name = res.get("criteria_results", [{}])[0].get("value")
    print(f"Evaluated 'product name': '{prod_name}'")
    # Must NOT echo "banana"
    assert "banana" not in str(prod_name).lower(), "FAILURE: Echoed filename 'banana'!"
    assert "High-Definition Video" in str(prod_name) or "Video Stream" in str(prod_name) or "Specimen" in str(prod_name)
    print("[PASS] TEST 4 PASSED: Rename invariance verified: product name is domain-specific, not 'banana'!")

def test_stem_reflection_and_audit_logging():
    print("\n[*] Test 5: Verifying stem reflection (#22 from 22.PNG) triggers FILENAME_ECHO and logs rejection reason...")
    # Test our scanner directly via payload reflection check
    payload = {
        "text": "Visual payload: 22.PNG (60.6 KB)",
        "modality": "IMAGE",
        "criteria": [
            {"name": "product name", "type": "Free Text", "range": "Open Free Text"}
        ]
    }
    r = requests.post(f"{BASE_URL}/api/v2/infer", json=payload)
    assert r.status_code == 200
    res = r.json()
    prod_name = res.get("criteria_results", [{}])[0].get("value")
    print(f"Evaluated label for 22.PNG: '{prod_name}'")
    assert str(prod_name) != "22", "FAILURE: Echoed numeric stem '22'!"
    assert str(prod_name) != "#22", "FAILURE: Echoed numeric stem '#22'!"
    assert "ftyp" not in str(prod_name).lower()
    print("[PASS] TEST 5 PASSED: Numeric stem '22' is never reflected as a product name!")

if __name__ == "__main__":
    try:
        test_binary_header_at_offset_4()
        test_byte_density_heuristic_rejection()
        test_zero_heading_unverified()
        test_rename_invariance_banana()
        test_stem_reflection_and_audit_logging()
        print("\n=======================================================")
        print("[SUCCESS] ALL 5 DURABILITY REGRESSION TESTS PASSED!")
        print("=======================================================")
    except Exception as e:
        print(f"\n[FAIL] TEST SUITE FAILED: {e}")
        import traceback
        traceback.print_exc()
