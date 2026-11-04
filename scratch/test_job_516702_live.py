import requests
import json

payload = {
    "modality": "TEXT",
    "text": """From: "Chase Fraud Alert" <security@chase-verify-portal.com>
To: customer@example.com
Date: 22 October 2024, 11:30 AM
Subject: URGENT: Your account is locked. Action required within 12 hours.
Body:
Dear Customer,
We detected an unauthorized login attempt on your Chase Online account on 21 October 2024 at 03:15 AM from an unrecognized IP address in London, UK.
To protect your funds, we have placed a temporary hold on your account and blocked a pending wire transfer of $12,500.
You must verify your identity to unlock your account. Please click the link below to log in and confirm a $150 processing fee:
👉 [https://chase-verify-portal.com/login]
If you do not verify within 12 hours, your account will be permanently closed, and the $12,500 will be seized by the fraud department.
If you did not authorize this, call us immediately at +1-800-555-0199.
Sincerely,
Mr. Robert Vance
Head of Fraud Prevention, Chase""",
    "depth_tier": "Standard",
    "criteria": [
        {"name": "PERSON", "type": "Free Text", "range": "Open Free Text"},
        {"name": "ORGANIZATION", "type": "Free Text", "range": "Open Free Text"},
        {"name": "DATE", "type": "Free Text", "range": "Open Free Text"},
        {"name": "TIME", "type": "Free Text", "range": "Open Free Text"},
        {"name": "MONEY", "type": "Free Text", "range": "Open Free Text"},
        {"name": "EVENT", "type": "Free Text", "range": "Open Free Text"},
        {"name": "PURPOSE", "type": "Enum", "range": "PHISHING, LEGITIMATE, MARKETING"},
        {"name": "POLICY", "type": "Enum", "range": "ACCOUNT CLOSURE, FUNDS SEIZED, NONE"}
    ]
}

res = requests.post("http://127.0.0.1:8000/api/v2/infer", json=payload, timeout=60)
print("Status code:", res.status_code)
data = res.json()
print("Keys:", list(data.keys()))

overall_conf = data.get("overall_criteria_confidence", 0)
print(f"OVERALL CRITERIA CONFIDENCE: {overall_conf}%")
crit_res = data.get("criteria_results", [])
for cr in crit_res:
    print(f"Heading: {cr.get('name'):<15} | Value: {str(cr.get('value')):<30} | Conf: {cr.get('confidence')}% | Agree: {cr.get('agreement')}")
