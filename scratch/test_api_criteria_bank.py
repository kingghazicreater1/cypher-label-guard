import httpx
import json

payload = {
    "text": (
        "On March 15, 2024, Mr. Daniel Okafor visited the Lagos branch of FirstTrust Bank to open a savings account. "
        "He presented his national identity card and proof of address, as required by the bank's Know Your Customer (KYC) policy. "
        "The account officer, Ms. Adaeze Nwosu, explained that the account would attract a 4% annual interest rate and a minimum "
        "opening deposit of ₦50,000. Mr. Okafor deposited ₦75,000 and was issued an ATM card."
    ),
    "modality": "TEXT",
    "depth_tier": "Standard",
    "criteria": [
        {"name": "account type", "type": "Free Text", "range": ""},
        {"name": "bank name", "type": "Free Text", "range": ""},
        {"name": "deposit amount", "type": "Free Text", "range": ""}
    ]
}

r = httpx.post("http://127.0.0.1:8000/api/v2/infer", json=payload, timeout=30.0)
data = r.json()

print("Consensus Decision:", data["data"]["consensus"]["decision"])
print("Consensus Label   :", data["data"]["consensus"]["label"])
print("Affirmative Votes :", data["data"]["consensus"]["affirmative_votes"], "/", data["data"]["consensus"]["total_votes_cast"])
print("\nCriteria Results:")
for c in data.get("criteria_results", []):
    safe_val = c['value'].encode('ascii', errors='replace').decode('ascii')
    print(f"  - {c['name']:15s}: {safe_val} | Conf: {c['confidence']}% | Agreement: {c['agreement']}")
