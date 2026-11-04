import requests
import json

text_550932 = """On 14 September 2024, at 08:00 AM, Mr. Arthur Miller was admitted to St. Jude Memorial Hospital due to severe chest pain that began 3 days prior. The attending physician, Dr. Sarah Jenkins, noted that the patient had a history of hypertension but denied any history of diabetes or prior heart attacks. Initial troponin levels were elevated at 2.5 ng/mL, but an ECG ruled out a myocardial infarction. Dr. Jenkins prescribed 50mg of Metoprolol to be taken twice daily. She scheduled a follow-up stress test for 20 September 2024. However, Mr. Miller stated he might skip the stress test because he cannot afford the $450 co-pay. The doctor warned him that if he skipped the medication, the risk of a stroke would increase significantly."""

# Test Option A: User explicitly chose Option A (Entity name only)
payload_opt_a = {
    "modality": "TEXT",
    "text": text_550932,
    "depth_tier": "Standard",
    "criteria": [
        {
            "name": "medication_name",
            "type": "Free Text",
            "range": "Canonical entity name only without modifiers, dosage, or regimen"
        }
    ]
}

res = requests.post("http://127.0.0.1:8000/api/v2/infer", json=payload_opt_a, timeout=60)
data = res.json()
print("Status code:", res.status_code)
for cr in data.get("criteria_results", []):
    print(f"Heading: {cr.get('name')} | Value: '{cr.get('value')}' | Conf: {cr.get('confidence')}% | Agree: {cr.get('agreement')}")
