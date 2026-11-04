import httpx
import time
import json

BASE_URL = "http://127.0.0.1:8000"

TESTS = [
    {
        "domain": "Medical & Healthcare",
        "name": "Clinical Encounter & Epistemic Modalities",
        "text": (
            "On 12 December 2024, Dr. Emily Chen evaluated Mr. James Carter at St. Mary's Hospital. "
            "Patient presented with palpitations and mild chest discomfort, but explicitly denied any history of asthma. "
            "An ECG and echocardiogram revealed mild mitral valve regurgitation. Dr. Chen warned the patient that "
            "regurgitation could progress to heart failure if left unmonitored. Dr. Chen prescribed Atenolol 25mg once daily. "
            "Patient agreed to try the medication for two weeks and scheduled a follow-up appointment on 26 December 2024."
        ),
        "criteria": [
            {"name": "PERSONS", "type": "Free Text"},
            {"name": "ORGANIZATIONS", "type": "Free Text"},
            {"name": "MEDICATIONS", "type": "Free Text", "range": "dosage, frequency"},
            {"name": "CONDITIONS_AND_MODALITIES", "type": "Free Text", "range": "tag with [CONFIRMED], [NEGATED], [HYPOTHETICAL]"},
            {"name": "DATES", "type": "Free Text", "range": "format YYYY-MM-DD"}
        ],
        "metadata": {}
    },
    {
        "domain": "Legal & Contracts",
        "name": "Commercial Lease Agreement & Void Conditions",
        "text": (
            "This Commercial Lease Agreement is entered into by Mr. Thomas Wright (Landlord) and Ms. Sarah Jenkins (Tenant). "
            "Tenant agrees to pay monthly rent of $2,500 commencing on 2025-02-01 until termination on 2026-01-31. "
            "A late fee of $150 shall apply if rent is delayed past 5 days. Subletting without prior written consent is strictly prohibited. "
            "Early termination is void unless caused by a declared natural disaster, in which case Tenant remains liable for the full term."
        ),
        "criteria": [
            {"name": "PERSONS", "type": "Free Text"},
            {"name": "MONEY", "type": "Free Text"},
            {"name": "DATES", "type": "Free Text"},
            {"name": "OBLIGATIONS", "type": "Free Text", "range": "tag with [TENANT] or [LANDLORD]"},
            {"name": "VOID_OR_PROHIBITED_CLAUSES", "type": "Free Text", "range": "tag with [VOID] or [PROHIBITED]"}
        ],
        "metadata": {}
    },
    {
        "domain": "Banking & Cybersecurity",
        "name": "Phishing Alert & Temporal Grounding",
        "text": (
            "From: 'Chase Fraud Alert' <security@chase-verify-portal.com> "
            "To: customer@example.com. "
            "Dear Customer, on 22 October 2024 at 11:30 AM, an unauthorized withdrawal of $12,500 was initiated. "
            "A security fee of $150 has been held. You must verify your identity within 72 hours, or your account will be suspended. "
            "Sincerely, Mr. Robert Vance, Fraud Prevention Unit."
        ),
        "criteria": [
            {"name": "ORGANIZATION", "type": "Free Text"},
            {"name": "PERSON", "type": "Free Text"},
            {"name": "MONEY", "type": "Free Text"},
            {"name": "TIME", "type": "Free Text", "range": "clock time only, not duration"},
            {"name": "DATES", "type": "Free Text"}
        ],
        "metadata": {}
    },
    {
        "domain": "Computer Vision Studio",
        "name": "Physical Specimen & Anti-Dominance Invariants",
        "text": "Visual payload: WIN_20241025_001.jpg (Blue Ceramic Coffee Mug on granite desk)",
        "criteria": [
            {"name": "PRODUCT_NAME", "type": "Free Text"},
            {"name": "COUNT", "type": "Scale", "range": "1-10"},
            {"name": "COLOR", "type": "Free Text"},
            {"name": "EDIBLE", "type": "Enum", "range": "Edible, Non-edible"},
            {"name": "HUMAN_PRESENCE", "type": "Boolean", "range": "Yes, No"}
        ],
        "metadata": {
            "visual_primary_product": "Blue Ceramic Coffee Mug",
            "visual_detected_objects": ["mug", "coffee mug"],
            "visual_item_count": 1,
            "visual_dominant_color": "Blue",
            "visual_is_edible": False,
            "visual_human_present": False,
            "visual_human_details": "No human detected"
        }
    }
]

def run_suite():
    print("=" * 80)
    print("CypherLabelGuard -- UNIVERSAL PARLIAMENT ENGINE BETA CERTIFICATION SUITE")
    print(f"Target: {BASE_URL} | Test Domains: 4 | Total Criteria Headings: 20")
    print("=" * 80)
    
    total_headings = 0
    passed_headings = 0
    all_scores = []

    client = httpx.Client(timeout=40.0)

    for idx, test in enumerate(TESTS, 1):
        print(f"\n[{idx}/4] Domain: {test['domain']}")
        print(f"Test Scenario: {test['name']}")
        start_t = time.time()
        
        payload = {
            "text": test["text"],
            "depth_tier": "Standard",
            "criteria": test["criteria"],
            "context_metadata": test["metadata"]
        }
        
        try:
            r = client.post(f"{BASE_URL}/api/v2/infer", json=payload)
            elapsed = time.time() - start_t
            if r.status_code != 200:
                print(f"  [ERROR] HTTP {r.status_code}: {r.text[:200]}")
                continue
                
            data = r.json()
            crit_res = data.get("criteria_results") or []
            print(f"  Execution Time: {elapsed:.2f}s | Headings Evaluated: {len(crit_res)}")
            
            for c in crit_res:
                total_headings += 1
                name = c.get("name")
                val = c.get("value")
                conf = float(c.get("confidence", 0.0) or 0.0)
                agree = c.get("agreement")
                all_scores.append(conf)
                
                is_pass = conf >= 70.0
                if is_pass:
                    passed_headings += 1
                status_icon = "PASS" if conf >= 85.0 else ("WARN" if conf >= 70.0 else "FAIL")
                
                print(f"    [{status_icon}] {name:<26} -> {val[:60]:<60} | {conf:5.1f}% | {agree}")
        except Exception as e:
            print(f"  [FAILED] Connection error: {e}")

    print("\n" + "=" * 80)
    print("FINAL BETA CERTIFICATION REPORT")
    print("=" * 80)
    avg_score = sum(all_scores) / len(all_scores) if all_scores else 0.0
    pass_rate = (passed_headings / total_headings * 100) if total_headings else 0.0
    print(f"Total Evaluated Headings : {total_headings}")
    print(f"Passing Headings (>=70%) : {passed_headings} / {total_headings} ({pass_rate:.1f}%)")
    print(f"Composite Mean Confidence: {avg_score:.2f}%")
    print(f"Certification Status     : {'READY FOR PRODUCTION BETA' if pass_rate >= 90.0 and avg_score >= 85.0 else 'REQUIRES REFINEMENT'}")
    print("=" * 80)

if __name__ == "__main__":
    run_suite()
