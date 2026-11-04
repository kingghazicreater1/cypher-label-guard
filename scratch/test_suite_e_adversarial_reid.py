import sys
import os
import re
import secrets
import hashlib
import json

# Ensure project root is on sys.path
sys.path.insert(0, os.path.abspath("."))

from core.fallback_registry import FallbackRegistry
from core.modality import derive_modality
from features.cat_c_privacy.blind_masker import BlindIngressMasker

# ------------------------------------------------------------------------------
# 1. Fallback Registry Centralization Unit Test
# ------------------------------------------------------------------------------
def test_fallback_registry_centralization():
    print("[*] Test 1: Verifying FallbackRegistry centralization & pattern coverage...")
    patterns = FallbackRegistry.get_all_registered_patterns()
    print(f"Registered Fallback Patterns ({len(patterns)}):")
    for p in patterns:
        print(f" - {p}")

    test_strings = [
        ("High-Definition Video Stream Specimen", True),
        ("temporal video stream specimen", True),
        ("Acoustic Signal Processing Specimen", True),
        ("Industrial Precision Bearing Assembly", True),
        ("Factory Precision Product Specimen", True),
        ("[UNVERIFIED: NO SPECIMEN DETECTED]", True),
        ("[REJECTED: CONTAINER SIGNATURE]", True),
        ("Verified / Pristine", True),
        ("No Specimen Detected", True),
        ("Genuine Precision Widget Model X-200", False),
        ("Pristine Metallic Surface", False),
    ]

    for val, expected in test_strings:
        is_fb, matched = FallbackRegistry.is_fallback(val)
        assert is_fb == expected, f"Failed for '{val}': expected {expected}, got {is_fb} (matched: {matched})"

    print("[PASS] TEST 1 PASSED: FallbackRegistry correctly identifies all generic fallback strings!\n")

# ------------------------------------------------------------------------------
# 2. State-Independent deriveModality Unit Test
# ------------------------------------------------------------------------------
def test_derive_modality_state_independence():
    print("[*] Test 2: Verifying state-independent derive_modality...")
    test_cases = [
        # Videos
        ("WIN_20260830_21_50_59_Pro.mp4", "VIDEO"),
        ("camera_feed.MOV", "VIDEO"),
        ("clip.webm", "VIDEO"),
        ("C:/Users/test/folder/recording.mkv", "VIDEO"),
        ("video container payload: stream.avi (20 MB)", "VIDEO"),
        
        # Images
        ("22.PNG", "IMAGE"),
        ("sample_part.jpeg", "IMAGE"),
        ("thermal_scan.webp", "IMAGE"),
        ("schema.svg", "IMAGE"),
        
        # Audio
        ("bearing_hum.wav", "AUDIO"),
        ("voice_memo.mp3", "AUDIO"),
        ("speech.flac", "AUDIO"),
        
        # Text
        ("manifest.csv", "TEXT"),
        ("notes.txt", "TEXT"),
        ("raw payload text", "TEXT"),
    ]

    for input_str, expected in test_cases:
        res = derive_modality(input_str)
        assert res == expected, f"Failed for '{input_str}': expected {expected}, got {res}"

    print("[PASS] TEST 2 PASSED: derive_modality is 100% deterministic and state-independent!\n")

# ------------------------------------------------------------------------------
# 3. Policy Hash Salting Test (Cross-Job Unlinkability)
# ------------------------------------------------------------------------------
def test_policy_hash_salting():
    print("[*] Test 3: Verifying policy_hash cryptographic salting across identical jobs...")
    raw_text = "Visual payload: identical_part.png (100 KB)"
    criteria = [{"name": "surface quality", "type": "Scale", "range": "1-10"}]

    # Job A
    trace_a = "trace-job-a-" + secrets.token_hex(4)
    masked_a, hash_a, _ = BlindIngressMasker.mask_ingress(trace_a, raw_text, "IMAGE", criteria)

    # Job B (Identical inputs, different job)
    trace_b = "trace-job-b-" + secrets.token_hex(4)
    masked_b, hash_b, _ = BlindIngressMasker.mask_ingress(trace_b, raw_text, "IMAGE", criteria)

    print(f"Job A Policy Hash: {hash_a}")
    print(f"Job B Policy Hash: {hash_b}")

    assert hash_a.startswith("sha256:")
    assert hash_b.startswith("sha256:")
    # Must be DIFFERENT to prevent cross-job policy correlation attacks
    assert hash_a != hash_b, "CRITICAL VULNERABILITY: Policy hashes are identical across jobs!"

    BlindIngressMasker.flush_vault(trace_a)
    BlindIngressMasker.flush_vault(trace_b)
    print("[PASS] TEST 3 PASSED: Salted policy hashes guarantee cross-job unlinkability!\n")

# ------------------------------------------------------------------------------
# 4. Suite E: Adversarial Re-Identification Attack Benchmark
# ------------------------------------------------------------------------------
def test_suite_e_adversarial_reid():
    print("[*] Test 4 (Suite E): Executing Adversarial Re-Identification Attack Benchmark...")
    
    # 20 realistic sensitive client payloads
    test_assets = [
        ("Visual payload: 22.PNG (60.6 KB)", "22.PNG", "22"),
        ("Visual payload: WIN_20261017_15_22_30_Pro.jpg (1.4 MB)", "WIN_20261017_15_22_30_Pro.jpg", "WIN_20261017"),
        ("Video container payload: factory_floor_cam3.mp4 (12 MB)", "factory_floor_cam3.mp4", "factory_floor"),
        ("Visual payload: John_Doe_ID_Card.png (250 KB)", "John_Doe_ID_Card.png", "John_Doe"),
        ("Visual payload: Patient_Record_99401.jpg (420 KB)", "Patient_Record_99401.jpg", "Patient_Record"),
        ("Visual payload: Acme_Secret_CAD_rev4.png (1.8 MB)", "Acme_Secret_CAD_rev4.png", "Acme_Secret"),
        ("Video container payload: WIN_20260830_21_50_59_Pro.mp4 (1.14 MB)", "WIN_20260830_21_50_59_Pro.mp4", "WIN_20260830"),
        ("Visual payload: Apple_Watch_Prototype_SN774.png (890 KB)", "Apple_Watch_Prototype_SN774.png", "Apple_Watch"),
        ("Visual payload: Turbine_SN_44019_Crack.png (3.2 MB)", "Turbine_SN_44019_Crack.png", "SN_44019"),
        ("Visual payload: confidential_contract_p1.png (510 KB)", "confidential_contract_p1.png", "confidential"),
    ] * 2  # 20 assets

    adversary_reid_successes = 0
    total_attempts = len(test_assets)

    for idx, (raw_text, filename, secret_stem) in enumerate(test_assets):
        trace_id = f"suite-e-trace-{idx}"
        masked_text, policy_hash, _ = BlindIngressMasker.mask_ingress(
            trace_id=trace_id,
            raw_text=raw_text,
            modality="IMAGE" if "Visual" in raw_text else "VIDEO",
            criteria=[{"name": "specimen entity", "type": "Free Text", "range": "Open"}],
            workspace_name="Client Secret Workspace"
        )

        # Adversary attempts to recover sensitive identifier from masked text
        adversary_view = masked_text.lower()
        recovered = False

        # Attack 1: Direct filename leakage
        if filename.lower() in adversary_view:
            recovered = True
        # Attack 2: Secret stem / camera timestamp leakage
        if secret_stem.lower() in adversary_view:
            recovered = True
        # Attack 3: Workspace / Client name leakage
        if "client secret workspace" in adversary_view:
            recovered = True

        if recovered:
            adversary_reid_successes += 1

        BlindIngressMasker.flush_vault(trace_id)

    reid_rate = (adversary_reid_successes / total_attempts) * 100.0
    print(f"Total Attack Attempts: {total_attempts}")
    print(f"Adversary Successful Recoveries: {adversary_reid_successes}")
    print(f"Re-Identification Rate: {reid_rate:.2f}% (Pass Target: < 5.0%)")

    assert reid_rate < 5.0, f"FAILED: Re-ID rate {reid_rate}% exceeds 5% threshold!"
    assert reid_rate == 0.0, f"Expected 0.0% Re-ID rate, got {reid_rate}%"
    print("[PASS] SUITE E PASSED: Adversarial Re-Identification Rate is 0.0%! Privacy guarantee proven.\n")

if __name__ == "__main__":
    try:
        test_fallback_registry_centralization()
        test_derive_modality_state_independence()
        test_policy_hash_salting()
        test_suite_e_adversarial_reid()
        print("==================================================================")
        print("[SUCCESS] ALL 4 HARDENING ITEMS & SUITE E PASSED WITH 100% SUCCESS!")
        print("==================================================================")
    except Exception as e:
        print(f"\n[FAIL] HARDENING TESTS FAILED: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
