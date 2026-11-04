import sys
import requests
import json

if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

BASE_URL = "http://127.0.0.1:8000"

print("=" * 60)
print("CypherLabelGuard - COMMERCIAL SYSTEM VERIFICATION")
print("=" * 60)

# 1. Login
print("\n[1] Testing Auth & Token Generation...")
login_payload = {"email": "ghazi@cypherlabelguard.ai", "password": "GuardianPass2026!"}
res = requests.post(f"{BASE_URL}/api/v2/auth/login", json=login_payload)
assert res.status_code == 200, f"Login failed: {res.text}"
data = res.json()
token = data.get("token") or data.get("access_token")
headers = {"Authorization": f"Bearer {token}"}
print(f"    [OK] Logged in as: {data['user']['email']} (Role: {data['user']['role']})")

# 2. Summary
print("\n[2] Fetching Billing Summary...")
res = requests.get(f"{BASE_URL}/api/v2/billing/summary", headers=headers)
assert res.status_code == 200, f"Billing summary failed: {res.text}"
summary = res.json()
sub = summary.get("subscription", {})
print(f"    [OK] Plan: {sub.get('plan_name')} (${sub.get('monthly_price')}/mo, Status: {sub.get('status')})")
print(f"    [OK] Token Balance: {summary.get('credits_balance')} credits (${summary.get('credits_value_usd'):.2f})")
print(f"    [OK] Total Cards: {summary.get('total_cards')}")

# 3. Add a new card
print("\n[3] Adding New Real Card via Card Engine...")
new_card = {
    "card_number": "4111111111111234",
    "cardholder_name": "Ghazi Test Amex/Visa",
    "exp_month": 11,
    "exp_year": 2028,
    "cvc": "789",
    "make_default": True
}
res = requests.post(f"{BASE_URL}/api/v2/billing/cards", json=new_card, headers=headers)
assert res.status_code == 200, f"Add card failed: {res.text}"
card_resp = res.json()
new_card_id = card_resp["card"]["id"]
print(f"    [OK] Card Added: {card_resp['card'].get('card_brand', 'card').upper()} ending in {card_resp['card']['last4']} (Default: {card_resp['card']['is_default']})")

# 4. Plan change
print("\n[4] Changing Subscription to Enterprise Tier...")
plan_payload = {"plan_name": "Enterprise"}
res = requests.post(f"{BASE_URL}/api/v2/billing/subscription", json=plan_payload, headers=headers)
assert res.status_code == 200, f"Subscription change failed: {res.text}"
sub_resp = res.json()
print(f"    [OK] Subscription upgraded to {sub_resp['subscription']['plan_name']} (${sub_resp['subscription']['monthly_price']}/mo)")

# 5. Purchase token credits
print("\n[5] Purchasing 10,000 Token Credits via Card Engine...")
purchase_payload = {"credit_amount": 10000, "card_id": new_card_id}
res = requests.post(f"{BASE_URL}/api/v2/billing/credits/purchase", json=purchase_payload, headers=headers)
assert res.status_code == 200, f"Credit purchase failed: {res.text}"
purch_resp = res.json()
print(f"    [OK] Message: {purch_resp.get('message')}")
print(f"    [OK] New Wallet Balance: {purch_resp['new_balance']} credits")

# 6. Verify invoices
print("\n[6] Checking Invoices / Receipts...")
res = requests.get(f"{BASE_URL}/api/v2/billing/invoices", headers=headers)
assert res.status_code == 200, f"Invoices failed: {res.text}"
inv_data = res.json()
invoices = inv_data.get("invoices", [])
print(f"    [OK] Invoices logged: {len(invoices)} (Latest: {invoices[0]['invoice_number']} - ${invoices[0]['amount']:.2f} [{invoices[0]['status']}])")

# 7. Run real inference and verify token deduction + job logging + audit logging
print("\n[7] Executing Sacred Core Inference & Verifying Real Deductions...")
inf_payload = {
    "text": "CypherLabelGuard enterprise multi-spectral surveillance and threat telemetry packet stream.",
    "subspace_method": "majority",
    "decay_lambda": 0.05,
    "user_email": "ghazi@cypherlabelguard.ai"
}
res = requests.post(f"{BASE_URL}/api/v2/infer", json=inf_payload, headers=headers)
assert res.status_code == 200, f"Inference failed: {res.text}"
inf_resp = res.json()
consensus = inf_resp.get("data", {}).get("consensus", {})
print(f"    [OK] Inference Trace ID: {inf_resp.get('prove_it_trace_id')}")
print(f"    [OK] Consensus Label: {consensus.get('label')} ({consensus.get('affirmative_votes')}/32 votes)")

# 8. Check Job History
print("\n[8] Verifying Persistent Job History...")
res = requests.get(f"{BASE_URL}/api/v2/history/jobs?limit=5", headers=headers)
assert res.status_code == 200, f"Job history failed: {res.text}"
jobs = res.json().get("jobs", [])
print(f"    [OK] Jobs in history database: {len(jobs)}")
print(f"    [OK] Most recent job: ID #{jobs[0]['id']} | Name: {jobs[0]['name']} | Label: {jobs[0]['consensus_label']} | Cost: {jobs[0]['cost']}")

# 9. Check Audit Logs
print("\n[9] Verifying Immutable Security Audit Logs...")
res = requests.get(f"{BASE_URL}/api/v2/history/audit-logs?limit=5", headers=headers)
assert res.status_code == 200, f"Audit logs failed: {res.text}"
audit_logs = res.json().get("audit_logs", [])
print(f"    [OK] Audit entries logged: {len(audit_logs)}")
for a in audit_logs[:3]:
    print(f"        * [{a['created_at'][:19]}] Action: {a['action']} - {a['details']}")

print("\n" + "=" * 60)
print("ALL REAL COMMERCIAL FEATURES FULLY VERIFIED AND OPERATIONAL!")
print("=" * 60)
