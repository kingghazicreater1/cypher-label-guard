import httpx
import json

text = (
    "On 2 April 2024, Zainab Holdings Ltd. transferred ₦2,400,000 from its corporate account at Mercury Bank "
    "to Delta Supplies Co. for industrial equipment. However, the transaction was flagged by Mercury Bank's automated "
    "Anti-Money Laundering (AML) monitoring policy because it exceeded the ₦2,000,000 single-transaction threshold. "
    "A temporary hold was placed on the funds. Mr. Tunde Balogun, the compliance officer at Mercury Bank, contacted "
    "Zainab Holdings requesting commercial invoices and tax identification documents. On 3 April 2024, after reviewing "
    "the submitted documents, Mr. Balogun authorized the release of the funds using his secure hardware token. "
    "Delta Supplies Co. confirmed receipt at 3:15 PM but lodged a formal complaint regarding the delayed delivery schedule. "
    "To preserve the client relationship, Mercury Bank agreed to waive the ₦15,000 expedited processing fee, while "
    "Mr. Balogun noted internally that Zainab Holdings intended to review alternative banking partners if future holds occurred."
)

criteria = [
    {"name": "PERSON", "type": "Free Text", "range": ""},
    {"name": "ORGANIZATION", "type": "Free Text", "range": ""},
    {"name": "DATE", "type": "Free Text", "range": ""},
    {"name": "MONEY", "type": "Free Text", "range": ""},
    {"name": "POLICY", "type": "Free Text", "range": ""},
    {"name": "FINANCIAL INSTRUMENTS", "type": "Free Text", "range": ""},
    {"name": "EVENTS", "type": "Free Text", "range": ""}
]

payload = {
    "text": text,
    "modality": "TEXT",
    "depth_tier": "Standard",
    "criteria": criteria
}

r = httpx.post("http://127.0.0.1:8000/api/v2/infer", json=payload, timeout=35.0)
data = r.json()

print("\n================== JOB #330414 LIVE PARLIAMENT RESULTS ==================")
print("Consensus Decision :", data.get("data", {}).get("consensus", {}).get("decision"))
print("Consensus Label    :", data.get("data", {}).get("consensus", {}).get("label"))
print("Affirmative Votes  :", data.get("data", {}).get("consensus", {}).get("affirmative_votes"), "/ 32")
print("Overall Confidence :", data.get("overall_criteria_confidence"), "%")
print("Anomaly Detected   :", data.get("anomaly_detected"))
print("\n--- Criteria Headings Breakdown ---")
for c in data.get("criteria_results", []):
    safe_val = str(c.get("value", "")).encode("ascii", errors="replace").decode("ascii")
    print(f"  [{c.get('name'):22s}] -> {safe_val}")
    print(f"    Confidence: {c.get('confidence')}% | Agreement: {c.get('agreement')}")
print("=========================================================================")
