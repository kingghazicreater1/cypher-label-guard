import httpx
import json

text = (
    "On 10 May 2024, a customer, Mrs. Folake Adeyemi, attempted to withdraw ₦800,000 at the Ikeja branch "
    "of Northgate Bank. The transaction was flagged under the bank's automated fraud-detection policy because "
    "it was initiated at 2:30 PM, outside her typical transaction hours, and her account had been active with "
    "micro-deposits only three days prior on 7 May 2024. The teller, Mr. Chidi Eze, placed a temporary restriction "
    "on the account. Northgate Bank claimed that an automated SMS alert was dispatched to Mrs. Adeyemi's registered "
    "mobile number immediately, but Mrs. Adeyemi vehemently disputed receiving any alert. She demanded an immediate "
    "reversal of the ₦40,000 chargeback fee assessed on 8 May 2024 and lodged a formal customer grievance with the "
    "bank manager, threatening to close her account and switch to a competitor. After an internal case review, the "
    "bank manager refused to refund the chargeback fee, upholding the policy violation."
)

criteria = [
    {"name": "PERSON", "type": "Free Text", "range": ""},
    {"name": "ORGANIZATION", "type": "Free Text", "range": ""},
    {"name": "DATE", "type": "Free Text", "range": ""},
    {"name": "TIME", "type": "Free Text", "range": ""},
    {"name": "MONEY", "type": "Free Text", "range": ""},
    {"name": "POLICY", "type": "Free Text", "range": ""},
    {"name": "EVENT", "type": "Free Text", "range": ""},
    {"name": "ROLE", "type": "Free Text", "range": ""}
]

payload = {
    "text": text,
    "modality": "TEXT",
    "depth_tier": "Standard",
    "criteria": criteria
}

# Restart backend process check
r = httpx.post("http://127.0.0.1:8000/api/v2/infer", json=payload, timeout=35.0)
data = r.json()

print("\n================== JOB #344871 LIVE PARLIAMENT RESULTS ==================")
print("Consensus Decision :", data.get("data", {}).get("consensus", {}).get("decision"))
print("Consensus Label    :", data.get("data", {}).get("consensus", {}).get("label"))
print("Affirmative Votes  :", data.get("data", {}).get("consensus", {}).get("affirmative_votes"), "/ 32")
print("Overall Confidence :", data.get("overall_criteria_confidence"), "%")
print("Anomaly Detected   :", data.get("anomaly_detected"))
print("\n--- Criteria Headings Breakdown (Universal Set-Wise Consensus) ---")
for c in data.get("criteria_results", []):
    safe_val = str(c.get("value", "")).encode("ascii", errors="replace").decode("ascii")
    print(f"  [{c.get('name'):15s}] -> {safe_val}")
    print(f"    Confidence: {c.get('confidence')}% | Agreement: {c.get('agreement')}")
print("=========================================================================")
