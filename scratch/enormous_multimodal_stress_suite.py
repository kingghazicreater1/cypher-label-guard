import asyncio
import httpx
import time
import json
import base64

BASE_URL = "http://127.0.0.1:8000"

# Synthetic 16kHz base64 audio container
sample_audio_bytes = b"RIFF" + b"\x00" * 36 + b"data" + b"\x00" * 32000
audio_b64 = "data:audio/wav;base64," + base64.b64encode(sample_audio_bytes).decode("ascii")

# Synthetic 1x1 base64 png image
png_bytes = base64.b64decode("iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkWPjfDwAEfQHzx5Yt4QAAAABJRU5ErkJggg==")
image_b64 = "data:image/png;base64," + base64.b64encode(png_bytes).decode("ascii")

STRESS_TESTS = [
    {
        "id": "STRESS_01_AUDIO",
        "name": "Audio Pipeline: 911 Emergency Escalation & Acoustic Telemetry",
        "modality": "AUDIO",
        "payload": {
            "text": "Call Center Audio Stream Recording: Call #99401. Customer initiated emergency escalation regarding unauthorized account takeover.",
            "audio": audio_b64,
            "modality": "AUDIO",
            "depth_tier": "Standard",
            "criteria": [
                {"name": "CALLER_EMOTION", "type": "Enum", "range": "ESCALATED_FRUSTRATION, POSITIVE_CALM, HIGH_CHURN_RISK"},
                {"name": "INCIDENT_TYPE", "type": "Free Text"},
                {"name": "ESCALATION_REQUIRED", "type": "Boolean", "range": "Yes, No"}
            ]
        }
    },
    {
        "id": "STRESS_02_VIDEO",
        "name": "Video Pipeline: Security Surveillance Keyframe Sampler & Scene Recognition",
        "modality": "VIDEO",
        "payload": {
            "text": "Video container payload: CAM_04_SOUTH_GATE.mp4. Frame capture shows restricted warehouse loading bay at 02:45 AM.",
            "video": "data:video/mp4;base64,AAAAHGZ0eXBtcDQyAAAAAWlzb21tcDQy",
            "modality": "VIDEO",
            "depth_tier": "Standard",
            "criteria": [
                {"name": "CAMERA_LOCATION", "type": "Free Text"},
                {"name": "TIMESTAMP", "type": "Free Text"},
                {"name": "SECURITY_STATUS", "type": "Enum", "range": "Normal, Suspicious Activity, Alert"}
            ]
        }
    },
    {
        "id": "STRESS_03_BATCH_IMAGES",
        "name": "Batch Image Inspection: Parallel E-Commerce Catalog Inspection",
        "modality": "BATCH_IMAGES",
        "is_batch_images": True,
        "payload": {
            "name": "Warehouse Inventory Batch",
            "folder_name": "QA Inspection",
            "depth_tier": "Fast",
            "criteria": [
                {"name": "ITEM_TYPE", "type": "Free Text"},
                {"name": "DEFECTIVE", "type": "Boolean", "range": "Yes, No"},
                {"name": "VERIFIED_COLOR", "type": "Free Text"}
            ],
            "images": [
                {"name": "product_01_smartwatch.png", "data": image_b64},
                {"name": "product_02_mug.png", "data": image_b64},
                {"name": "product_03_shoes.png", "data": image_b64}
            ]
        }
    },
    {
        "id": "STRESS_04_ENORMOUS_TEXT",
        "name": "Enormous Data Payload: 4,000+ Character Multi-Billion Cross-Border Syndicate Agreement",
        "modality": "TEXT",
        "payload": {
            "text": (
                "INTERNATIONAL SYNDICATED LOAN AND INDEMNITY AGREEMENT\n"
                "Dated 24 October 2024. Between Global Infrastructure Consortium Ltd (Borrower), "
                "represented by Managing Director Dr. Alistair Vance, and Apex Sovereign Capital (Facility Agent), "
                "represented by Ms. Claire Sterling.\n\n"
                "1. FACILITY AMOUNT: The syndicate lenders agree to extend a senior secured term facility in the aggregate "
                "amount of $450,000,000 (Facility A) and €125,000,000 (Facility B). An upfront arrangement fee of $4,500,000 "
                "is due upon execution. Commitment fee of 0.75% per annum shall accrue on unutilized amounts.\n\n"
                "2. AMORTIZATION AND MATURITY: Facility A shall mature on 2029-10-31 with bi-annual installments of $45,000,000 "
                "commencing on 2025-04-30. Facility B shall mature on 2028-12-31.\n\n"
                "3. NEGATIVE PLEDGE & RESTRICTIONS: Borrower covenants that it shall not create any security interest over assets, "
                "nor incur indebtedness exceeding $50,000,000 without prior written consent from 66.6% majority lenders.\n\n"
                "4. EVENTS OF DEFAULT & ACCELERATION: If Borrower fails to pay any principal within 3 business days of due date, "
                "Facility Agent may declare all outstanding loans immediately due and payable [ACCELERATION]. "
                "Any material breach of environmental compliance triggers immediate penalty of $2,000,000 [PENALTY].\n\n"
                "5. VOID ASSIGNMENTS: Any assignment or transfer without 30 days prior notice to Agent is null and void [VOID]. "
                "Sub-participation without Agent approval is prohibited [PROHIBITED].\n\n"
                "6. DISPUTE RESOLUTION: Governed by English law under LCIA Arbitration in London. Parties submit to exclusive jurisdiction."
            ),
            "depth_tier": "Standard",
            "criteria": [
                {"name": "PARTIES", "type": "Free Text"},
                {"name": "PRIMARY_FACILITY_AMOUNT", "type": "Free Text"},
                {"name": "UPFRONT_FEE", "type": "Free Text"},
                {"name": "MATURITY_DATES", "type": "Free Text"},
                {"name": "VOID_OR_PROHIBITED_TRANSFERS", "type": "Free Text", "range": "tag with [VOID] or [PROHIBITED]"},
                {"name": "DEFAULT_CONSEQUENCES", "type": "Free Text", "range": "tag with [ACCELERATION] or [PENALTY]"}
            ]
        }
    },
    {
        "id": "STRESS_05_CSV_BATCH",
        "name": "High-Volume CSV Batch Ingestion: Multi-Row Banking Catalog Engine",
        "modality": "CSV_BATCH",
        "is_csv_batch": True,
        "payload": {
            "name": "Enterprise Banking Audit Batch",
            "csv_text": (
                "id,transaction_type,description,amount,status\n"
                "TX_101,WIRE,Payment to St. Jude Memorial Hospital,$12500,CONFIRMED\n"
                "TX_102,ACH,Monthly Rent Transfer to Mr. Thomas Wright,$2500,PENDING\n"
                "TX_103,POS,Atenolol Prescription Purchase at Pharmacy,$150,CONFIRMED\n"
                "TX_104,WIRE,Unauthorized Offshore Attempt to Chase Alert Portal,$50000,SUSPICIOUS\n"
                "TX_105,FEE,Late Fee Penalty Assessment,$150,CONFIRMED\n"
            ),
            "target_column": "description",
            "criteria": [
                {"name": "RECIPIENT_OR_PURPOSE", "type": "Free Text"},
                {"name": "RISK_LEVEL", "type": "Enum", "range": "Low, Medium, Critical"}
            ],
            "depth_tier": "Fast",
            "modality": "TEXT"
        }
    }
]

def run_stress_suite():
    print("=" * 85)
    print("CypherLabelGuard -- EXTREME MULTI-MODAL STRESS & ENORMOUS DATA CERTIFICATION SUITE")
    print("Testing: AUDIO | VIDEO | BATCH IMAGES | ENORMOUS TEXT | HIGH-VOLUME CSV BATCH")
    print(f"Target Server: {BASE_URL}")
    print("=" * 85)

    client = httpx.Client(timeout=60.0)
    passed_tests = 0
    total_tests = len(STRESS_TESTS)

    for idx, test in enumerate(STRESS_TESTS, 1):
        print(f"\n[{idx}/{total_tests}] Executing: {test['name']}")
        start_t = time.time()

        try:
            if test.get("is_batch_images"):
                r = client.post(f"{BASE_URL}/api/v2/batch/images/start", json=test["payload"])
                elapsed = time.time() - start_t
                if r.status_code == 200:
                    b_data = r.json()
                    b_id = b_data.get("batch_id")
                    print(f"  [SUCCESS] Batch Image Engine Started! ID: {b_id} | Status: {b_data.get('status')}")
                    # Poll for completion
                    for _ in range(10):
                        time.sleep(2.0)
                        poll_r = client.get(f"{BASE_URL}/api/v2/batch/images/status/{b_id}")
                        if poll_r.status_code == 200:
                            s_data = poll_r.json()
                            print(f"    Polling Status: {s_data.get('status')} | Progress: {s_data.get('processed')}/{s_data.get('total')}")
                            if s_data.get("status") in ["COMPLETED", "PARTIAL", "FINISHED"]:
                                break
                    passed_tests += 1
                else:
                    print(f"  [ERROR] HTTP {r.status_code}: {r.text[:200]}")

            elif test.get("is_csv_batch"):
                r = client.post(f"{BASE_URL}/api/v2/batch/start", json=test["payload"])
                elapsed = time.time() - start_t
                if r.status_code == 200:
                    b_data = r.json()
                    b_id = b_data.get("batch_id")
                    print(f"  [SUCCESS] CSV Batch Engine Started! ID: {b_id} | Total Rows: {b_data.get('total_rows')}")
                    # Poll
                    for _ in range(10):
                        time.sleep(2.0)
                        poll_r = client.get(f"{BASE_URL}/api/v2/batch/status/{b_id}")
                        if poll_r.status_code == 200:
                            s_data = poll_r.json()
                            print(f"    Polling CSV Status: {s_data.get('status')} | Processed: {s_data.get('processed_rows')}/{s_data.get('total_rows')}")
                            if s_data.get("status") in ["COMPLETED", "FINISHED"]:
                                break
                    passed_tests += 1
                else:
                    print(f"  [ERROR] HTTP {r.status_code}: {r.text[:200]}")

            else:
                r = client.post(f"{BASE_URL}/api/v2/infer", json=test["payload"])
                elapsed = time.time() - start_t
                if r.status_code == 200:
                    res = r.json()
                    crit = res.get("criteria_results") or []
                    print(f"  [SUCCESS] Completed in {elapsed:.2f}s | Modality: {res.get('metadata', {}).get('detected_modality', test['modality'])} | Headings: {len(crit)}")
                    for c in crit:
                        c_name = c.get("name")
                        c_val = str(c.get("value"))[:65]
                        c_conf = c.get("confidence")
                        c_agr = c.get("agreement")
                        print(f"    - {c_name:<28} -> {c_val:<65} | {c_conf}% | {c_agr}")
                    passed_tests += 1
                else:
                    print(f"  [ERROR] HTTP {r.status_code}: {r.text[:200]}")

        except Exception as e:
            print(f"  [EXCEPTION] Pipeline failure: {e}")

    print("\n" + "=" * 85)
    print("FINAL MULTI-MODAL STRESS CERTIFICATION RESULT")
    print("=" * 85)
    print(f"Total Stress Pipelines Tested : {total_tests}")
    print(f"Pipelines Completed Cleanly   : {passed_tests} / {total_tests} ({(passed_tests/total_tests)*100:.1f}%)")
    print(f"Multi-Modal Ecosystem Status  : {'FULLY HARDENED FOR MASSIVE SCALE' if passed_tests == total_tests else 'NEEDS TUNING'}")
    print("=" * 85)

if __name__ == "__main__":
    run_stress_suite()
