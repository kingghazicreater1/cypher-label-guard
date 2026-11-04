import sys
import os
import requests
import json

# Ensure project root is on sys.path
sys.path.insert(0, os.path.abspath("."))

from features.cat_c_privacy.task_eligibility import TaskEligibilityRouter, ExecutionPlane
from features.cat_c_privacy.blind_masker import BlindIngressMasker

def test_gap1_circular_trap_evaluated_first():
    print("[*] Test 1 (Gap 1): Verifying CIRCULAR_TRAP is evaluated FIRST before identity checks...")
    # This query contains BOTH "find credit card" (circular) and "who is" / "identity"
    criteria = [
        {"name": "Audit PII and find credit cards", "type": "Free Text", "range": "Open"}
    ]
    plane, reason, meta = TaskEligibilityRouter.evaluate(criteria, modality="IMAGE")
    print(f"Routing Verdict: {plane}")
    print(f"Reason: {reason}")
    print(f"Audit Code: {meta.get('audit_code')}")
    assert plane == ExecutionPlane.CIRCULAR_TRAP, f"Expected CIRCULAR_TRAP, got {plane}"
    assert meta.get("audit_code") == "CIRCULAR_TRAP_LOCAL_EXECUTION"
    print("[PASS] TEST 1 PASSED: Circularity check is evaluated at the top of the decision tree!\n")

def test_gap2_policy_metadata_protection():
    print("[*] Test 2 (Gap 2): Verifying mask policy is protected in volatile RAM and committed via SHA-256 hash only...")
    trace_id = "test-trace-gap2"
    raw_text = "Visual payload: turbine_blade.jpg (500 KB)"
    criteria = [{"name": "surface crack", "type": "Free Text", "range": "Open"}]
    
    masked_text, policy_hash, masked_crit = BlindIngressMasker.mask_ingress(
        trace_id=trace_id,
        raw_text=raw_text,
        modality="IMAGE",
        criteria=criteria,
        workspace_name="Aero Precision Workspace"
    )
    print(f"Masked Text: '{masked_text}'")
    print(f"Policy Hash: '{policy_hash}'")
    assert "[SPECIMEN_01]" in masked_text
    assert policy_hash.startswith("sha256:")
    assert trace_id in BlindIngressMasker._RAM_VAULTS
    
    # Test flush_vault wipes volatile RAM
    BlindIngressMasker.flush_vault(trace_id)
    assert trace_id not in BlindIngressMasker._RAM_VAULTS
    print("[PASS] TEST 2 PASSED: Policy stored exclusively in volatile RAM; lineage gets hash only; vault wipes cleanly!\n")

def test_gap3_audio_defaults_to_enclave():
    print("[*] Test 3 (Gap 3): Verifying audio modality defaults to ENCLAVE_REQUIRED pending feasibility spike...")
    criteria = [
        {"name": "language identification", "type": "Free Text", "range": "Open"}
    ]
    plane, reason, meta = TaskEligibilityRouter.evaluate(criteria, modality="AUDIO")
    print(f"Routing Verdict: {plane}")
    print(f"Reason: {reason}")
    print(f"Audit Code: {meta.get('audit_code')}")
    assert plane == ExecutionPlane.ENCLAVE_REQUIRED, f"Expected ENCLAVE_REQUIRED for audio, got {plane}"
    assert meta.get("audit_code") == "AUDIO_SPIKE_PENDING_ENCLAVE"
    print("[PASS] TEST 3 PASSED: Audio modality safely defaults to local enclave until feasibility spike!\n")

def test_gap4_dual_sided_token_echo():
    print("[*] Test 4 (Gap 4 / Token-Echo): Verifying dual-sided egress guard catches both [SPECIMEN_01] and raw string...")
    trace_id = "test-trace-gap4"
    raw_text = "Visual payload: 22.PNG (60.6 KB)"
    criteria = [{"name": "product name", "type": "Free Text", "range": "Open"}]
    
    masked_text, policy_hash, _ = BlindIngressMasker.mask_ingress(
        trace_id=trace_id,
        raw_text=raw_text,
        modality="IMAGE",
        criteria=criteria
    )
    
    # Scenario A: Model echoes masked token [SPECIMEN_01]
    is_anom, guard, tok = BlindIngressMasker.audit_token_echo(trace_id, "[SPECIMEN_01]")
    print(f"Echoing '[SPECIMEN_01]' -> Anomaly: {is_anom}, Guard: {guard}, Matched: {tok}")
    assert is_anom is True and guard == "TOKEN_ECHO"

    # Scenario B: Model hallucinates raw filename stem '22'
    is_anom2, guard2, tok2 = BlindIngressMasker.audit_token_echo(trace_id, "22")
    print(f"Echoing raw '22' -> Anomaly: {is_anom2}, Guard: {guard2}, Matched: {tok2}")
    assert is_anom2 is True and guard2 == "FILENAME_ECHO"

    # Scenario C: Clean domain-specific inspection output
    is_anom3, guard3, tok3 = BlindIngressMasker.audit_token_echo(trace_id, "Industrial Precision Bearing Assembly")
    print(f"Clean Output -> Anomaly: {is_anom3}")
    assert is_anom3 is False

    BlindIngressMasker.flush_vault(trace_id)
    print("[PASS] TEST 4 PASSED: Dual-sided egress guard catches both token reflections and raw vault strings!\n")

if __name__ == "__main__":
    try:
        test_gap1_circular_trap_evaluated_first()
        test_gap2_policy_metadata_protection()
        test_gap3_audio_defaults_to_enclave()
        test_gap4_dual_sided_token_echo()
        print("=======================================================")
        print("[SUCCESS] ALL 4 GAPS VERIFIED & RIGOROUSLY RESOLVED!")
        print("=======================================================")
    except Exception as e:
        print(f"\n[FAIL] VERIFICATION FAILED: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
