import httpx
import json
import sys

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

text = (
    "On 12 June 2024, a customer, Mrs. Amara Obi, attempted to transfer ₦1,500,000 from her current account "
    "at Horizon Bank to a beneficiary, Mr. Femi Adeleke. The transfer was initiated via mobile banking but was "
    "blocked by the bank's anti-fraud policy because the beneficiary account had been flagged for suspicious activity "
    "on 9 June 2024. Mrs. Obi was informed that the funds would not be released unless she visited a branch and "
    "provided additional identification. She argued that she had made similar transfers before without issues and "
    "claimed the bank's SMS notification system had never alerted her to the flag. Horizon Bank's compliance officer, "
    "Ms. Ngozi Okoro, stated that the alert had been sent and that a charge of ₦2,500 had been deducted for the manual "
    "review. Mrs. Obi threatened to close her account if the matter was not resolved within 72 hours. The compliance "
    "officer agreed to expedite the review but confirmed that no refund of the ₦2,500 charge would be issued unless the "
    "flag was proven to be an error. A complaint was filed at 3:15 PM, and Mrs. Obi left without the transfer being completed."
)

criteria = [
    {"name": "PERSON", "type": "Free Text"},
    {"name": "ORGANIZATIONS", "type": "Free Text"},
    {"name": "DATE", "type": "Free Text"},
    {"name": "TIME", "type": "Free Text"},
    {"name": "MONEY", "type": "Free Text"},
    {"name": "ROLE", "type": "Free Text"},
    {"name": "EVENT", "type": "Free Text"}
]

payload = {
    "text": text,
    "depth": "Standard",
    "criteria": criteria,
    "metadata": {
        "job_id": "416976_VERIFICATION",
    }
}

try:
    with httpx.Client(timeout=45.0) as client:
        r = client.post("http://127.0.0.1:8000/api/v2/infer", json=payload)
        print("Status Code:", r.status_code)
        if r.status_code == 200:
            data = r.json()
            print("\n=== PARLIAMENT DECISION ===")
            print("Job ID:", data.get("job_id"))
            print("Overall Criteria Confidence:", data.get("overall_criteria_confidence"), "%")

            print("\n=== CRITERIA RESULTS ===")
            crit_results = data.get("criteria_results", [])
            for c in crit_results:
                print(f"[{c.get('name')}]")
                print(f"  Value: {c.get('value')}")
                print(f"  Confidence: {c.get('confidence')}%")
                print(f"  Agreement: {c.get('agreement')}")
                print(f"  Votes: {json.dumps(c.get('votes'), ensure_ascii=False)}")
                print()
        else:
            print("Error response:", r.text)
except Exception as e:
    print("Exception connecting to backend:", e)
