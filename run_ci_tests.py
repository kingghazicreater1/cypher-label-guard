#!/usr/bin/env python3
"""
CypherLabelGuard Comprehensive CI Test Runner.
Executes both Frontend (Node.js) and Backend (Python) test suites.
Guarantees zero silent regressions across:
1. State-independent modality derivation
2. Centralized fallback registry
3. policy_hash salting
4. Suite E strengthened adversarial re-identification (Tiers 1, 2, 3)
5. Job #490563 regression (falsy 0.0 confidence & wizard file purge)
6. Pakistani Banking & Manual Proof Verification Suite
"""

import sys
import subprocess
import os

def run_step(name: str, cmd: list) -> bool:
    print(f"\n========================================================")
    print(f"[*] Running CI Test Step: {name}")
    print(f"[*] Command: {' '.join(cmd)}")
    print(f"========================================================")
    result = subprocess.run(cmd, cwd=os.path.abspath(os.path.dirname(__file__)))
    if result.returncode != 0:
        print(f"\n[FAIL] Step '{name}' FAILED with exit code {result.returncode}!")
        return False
    print(f"[PASS] Step '{name}' PASSED cleanly.")
    return True

def main():
    steps = [
        ("Frontend Modality Parity Unit Test", ["node", "scratch/test_frontend_modality.mjs"]),
        ("Frontend Job #490563 Falsy & Wizard Purge Regression", ["node", "scratch/test_regression_frontend_490563.mjs"]),
        ("Frontend Vision Studio Anomaly Coupling Test", ["node", "scratch/test_vision_studio_anomaly_coupling.mjs"]),
        ("Backend Fallback Registry Unit Test", ["python", "-m", "unittest", "tests/test_fallback_registry.py"]),
        ("Backend State-Independent Modality Unit Test", ["python", "-m", "unittest", "tests/test_derive_modality.py"]),
        ("Backend Policy Hash Salting Test", ["python", "-m", "unittest", "tests/test_policy_hash_salting.py"]),
        ("Backend Job #490563 Confidence Revocation Test", ["python", "-m", "unittest", "tests/test_regression_490563.py"]),
        ("Zero-Heading Class Test (Never False-Green)", ["python", "-m", "unittest", "tests/test_zero_heading_never_false_green.py"]),
        ("Automated Anti-Fallback Scanner (Zero ?? 9X / or 9X / 98.4)", ["python", "-m", "unittest", "tests/test_anti_fallback_scanner.py"]),
        ("Job #377549 Vision Concordance Regression (Backend)", ["python", "-m", "unittest", "tests/test_job_377549_vision_concordance_regression.py"]),
        ("Job #377549 Frontend Regression Test", ["node", "scratch/test_job_377549_regression.mjs"]),
        ("Suite E Strengthened Adversarial Re-ID Benchmark (Tiers 1, 2, 3)", ["python", "-m", "unittest", "tests/test_suite_e_adversarial_reid.py"]),
        ("Gated Adversarial Debate Protocol Suite (Feature 09)", ["python", "-m", "unittest", "tests/test_gated_adversarial_debate.py"]),
        ("Clerk Auth Security Suite (signature-verified, no backdoors)", ["python", "-m", "unittest", "tests/test_clerk_auth.py"]),
        ("Audit Hardening Suite (batch ownership, WS auth, tenant-scoped telemetry)", ["python", "-m", "unittest", "tests/test_audit_hardening.py"]),
        ("Job #680488 Cascade Isolation & Fallback Rejection", ["python", "-m", "unittest", "tests/test_job_680488_cascade_isolation.py"]),
        ("Job #382356 Multi-Object Vision Detection", ["python", "-m", "unittest", "tests/test_job_382356_multiobject_detection.py"]),
        ("Pakistani Banking & Manual Proof Verification Suite", ["python", "-m", "unittest", "tests/test_pakistani_billing.py"]),
        ("Provider Auto-Pacer & Truthful Progress Suite (429 backoff, spacing, no false claims)", ["python", "-m", "unittest", "tests/test_provider_pacer.py"]),
        ("Comprehensive Multi-Modal CI Test Matrix (5 Modalities, Guards & Feature 38)", ["python", "-m", "unittest", "tests/test_multimodal_comprehensive_matrix.py"]),
    ]

    failed_steps = []
    passed_steps = []

    for name, cmd in steps:
        if run_step(name, cmd):
            passed_steps.append(name)
        else:
            failed_steps.append(name)

    print("\n========================================================")
    print(f"[*] CI EXECUTION SUMMARY: {len(passed_steps)}/{len(steps)} SUITES PASSED")
    print("========================================================")
    if failed_steps:
        print(f"\n[FAIL] THE FOLLOWING {len(failed_steps)} CI SUITE(S) FAILED:")
        for fs in failed_steps:
            print(f"  [X] {fs}")
        sys.exit(1)
    else:
        print(f"\n[SUCCESS] ALL {len(steps)} CI TEST SUITES PASSED CLEANLY (100% SUCCESS)!")
        sys.exit(0)

if __name__ == "__main__":
    main()
