import requests
import time
import sys

BASE_URL = "http://127.0.0.1:8000"

def run_tests():
    print("=== STARTING COMPLETE AUTHENTICATION PIPELINE TEST ===")
    session = requests.Session()

    test_email = f"commander_qa_{int(time.time())}@avguardian.ai"
    test_password = "SecurePassword2026!"
    test_name = "Chief Commander QA"

    # 1. Signup
    print("\n1. Testing User Signup...")
    signup_payload = {
        "email": test_email,
        "password": test_password,
        "full_name": test_name,
        "workspace_name": "QA Command Center"
    }
    res = session.post(f"{BASE_URL}/api/v2/auth/signup", json=signup_payload)
    assert res.status_code == 200, f"Signup failed: {res.text}"
    data = res.json()
    assert data["success"] is True
    assert "token" in data and len(data["token"]) > 20
    assert data["user"]["email"] == test_email
    assert data["user"]["full_name"] == test_name
    assert data["user"]["credits_balance"] == 5000
    token = data["token"]
    print(f" -> PASS: User created successfully. ID={data['user']['id']}, Credits={data['user']['credits_balance']}")

    # 2. Duplicate signup should be rejected
    print("\n2. Testing Duplicate Signup Prevention...")
    res_dup = session.post(f"{BASE_URL}/api/v2/auth/signup", json=signup_payload)
    assert res_dup.status_code == 400, f"Duplicate signup should fail with 400: {res_dup.status_code}"
    print(" -> PASS: Duplicate email rejected with HTTP 400.")

    # 3. Login with wrong password
    print("\n3. Testing Login with Wrong Password...")
    res_wrong = session.post(f"{BASE_URL}/api/v2/auth/login", json={"email": test_email, "password": "WrongPassword!"})
    assert res_wrong.status_code == 400, f"Wrong password should fail with 400: {res_wrong.status_code}"
    print(" -> PASS: Invalid password rejected with HTTP 400.")

    # 4. Login with correct password
    print("\n4. Testing Login with Valid Password...")
    res_login = session.post(f"{BASE_URL}/api/v2/auth/login", json={"email": test_email, "password": test_password})
    assert res_login.status_code == 200, f"Login failed: {res_login.text}"
    login_data = res_login.json()
    assert login_data["success"] is True
    assert "token" in login_data
    auth_token = login_data["token"]
    auth_headers = {"Authorization": f"Bearer {auth_token}"}
    print(" -> PASS: Login successful and JWT Bearer token issued.")

    # 5. Access /api/v2/auth/me with Bearer Token
    print("\n5. Testing /api/v2/auth/me Profile Hydration...")
    res_me = session.get(f"{BASE_URL}/api/v2/auth/me", headers=auth_headers)
    assert res_me.status_code == 200, f"/me failed: {res_me.text}"
    me_data = res_me.json()
    assert me_data["user"]["email"] == test_email
    assert me_data["credits_balance"] == 5000
    print(f" -> PASS: Profile hydrated for {me_data['user']['email']}, plan={me_data['subscription']['plan_name']}.")

    # 6. Access /api/v2/auth/me without token (should be 401)
    print("\n6. Testing /api/v2/auth/me Unauthorized Guard...")
    res_unauth = session.get(f"{BASE_URL}/api/v2/auth/me")
    assert res_unauth.status_code == 401, f"Expected 401, got {res_unauth.status_code}"
    print(" -> PASS: Unauthenticated access rejected with HTTP 401.")

    # 7. Access /api/v2/auth/me with corrupted token (should be 401)
    print("\n7. Testing /api/v2/auth/me Invalid Token Guard...")
    res_bad_token = session.get(f"{BASE_URL}/api/v2/auth/me", headers={"Authorization": "Bearer bad.token.value"})
    assert res_bad_token.status_code == 401, f"Expected 401, got {res_bad_token.status_code}"
    print(" -> PASS: Corrupted token rejected with HTTP 401.")

    # 8. Testing Guest Access on Keys & Billing (no token)
    print("\n8. Testing Guest Access on Keys & Billing Endpoints...")
    res_keys_guest = session.get(f"{BASE_URL}/api/v2/keys/status")
    assert res_keys_guest.status_code == 200, f"Guest keys status failed: {res_keys_guest.text}"
    res_billing_guest = session.get(f"{BASE_URL}/api/v2/billing/summary")
    assert res_billing_guest.status_code == 200, f"Guest billing failed: {res_billing_guest.text}"
    assert res_billing_guest.json().get("is_guest") is True
    print(" -> PASS: Guest session gracefully serviced on /keys/status and /billing/summary without crashing.")

    # 9. Testing Authenticated Access on Keys & Billing (with token)
    print("\n9. Testing Authenticated Keys & Billing Access...")
    res_keys_auth = session.get(f"{BASE_URL}/api/v2/keys/status", headers=auth_headers)
    assert res_keys_auth.status_code == 200
    res_billing_auth = session.get(f"{BASE_URL}/api/v2/billing/summary", headers=auth_headers)
    assert res_billing_auth.status_code == 200
    assert res_billing_auth.json().get("credits_balance") == 5000
    print(" -> PASS: Authenticated user received real wallet balance and slots.")

    # 10. Testing Google Authentication
    print("\n10. Testing Google OAuth Route...")
    google_email = f"google_user_{int(time.time())}@cypherlabelguard.ai"
    res_google = session.post(f"{BASE_URL}/api/v2/auth/google", json={
        "email": google_email,
        "name": "Google Pioneer"
    })
    assert res_google.status_code == 200, f"Google login failed: {res_google.text}"
    g_data = res_google.json()
    assert g_data["success"] is True
    assert g_data["user"]["email"] == google_email
    print(f" -> PASS: Google user established: {google_email}")

    # 11. Testing Phone SMS OTP Workflow
    print("\n11. Testing Mobile Number OTP Workflow...")
    test_phone = "+923009998877"
    res_send_otp = session.post(f"{BASE_URL}/api/v2/auth/phone/send-otp", json={"phone_number": test_phone})
    assert res_send_otp.status_code == 200, f"Send OTP failed: {res_send_otp.text}"
    otp_data = res_send_otp.json()
    assert "demo_otp" in otp_data
    code = otp_data["demo_otp"]
    print(f" -> Dispatched OTP code: {code}")

    # Verify wrong OTP fails
    res_verify_fail = session.post(f"{BASE_URL}/api/v2/auth/phone/verify-otp", json={"phone_number": test_phone, "otp_code": "000000"})
    assert res_verify_fail.status_code == 400, "Wrong OTP should fail with 400"
    print(" -> PASS: Invalid OTP code rejected with HTTP 400.")

    # Verify correct OTP succeeds
    res_verify_ok = session.post(f"{BASE_URL}/api/v2/auth/phone/verify-otp", json={"phone_number": test_phone, "otp_code": code})
    assert res_verify_ok.status_code == 200, f"OTP verification failed: {res_verify_ok.text}"
    phone_auth = res_verify_ok.json()
    assert phone_auth["success"] is True
    assert "token" in phone_auth
    print(f" -> PASS: Phone user authenticated. User={phone_auth['user']['email']}")

    # 12. Check Audit Logs for Forensics
    print("\n12. Verifying Audit Log Entries in SQLite DB...")
    res_logs = session.get(f"{BASE_URL}/api/v2/history/audit-logs?limit=10", headers=auth_headers)
    assert res_logs.status_code == 200, f"Audit logs failed: {res_logs.text}"
    logs_data = res_logs.json()
    logs = logs_data.get("audit_logs", [])
    actions = [l["action"] for l in logs]
    print(f" -> PASS: Audit logs retrieved ({len(logs)} entries). Recent actions: {actions[:5]}")

    print("\n=======================================================")
    print("[SUCCESS] ALL 12 AUTHENTICATION PIPELINE TESTS PASSED 100%!")
    print("=======================================================")

if __name__ == "__main__":
    run_tests()
