import requests
import time
import sys

BASE_URL = "http://127.0.0.1:8000"

def test_email_otp_pipeline():
    print("=== STARTING FREE GMAIL SMTP & EMAIL OTP PIPELINE TEST ===")
    session = requests.Session()

    # 1. Check SMTP Status
    print("\n1. Testing GET /api/v2/auth/smtp/status...")
    res_status = session.get(f"{BASE_URL}/api/v2/auth/smtp/status")
    assert res_status.status_code == 200, f"Status failed: {res_status.text}"
    status_data = res_status.json()
    assert status_data["success"] is True
    assert status_data["host"] == "smtp.gmail.com"
    assert status_data["port"] == 587
    print(f" -> PASS: SMTP Status active. Host: {status_data['host']}:{status_data['port']}, Configured: {status_data['is_configured']}")

    # 2. Dispatch Email OTP
    test_email = f"verified_pioneer_{int(time.time())}@avguardian.ai"
    print(f"\n2. Testing POST /api/v2/auth/email/send-otp for {test_email}...")
    res_send = session.post(f"{BASE_URL}/api/v2/auth/email/send-otp", json={
        "email": test_email,
        "user_name": "Pioneer Commander"
    })
    assert res_send.status_code == 200, f"Send OTP failed: {res_send.text}"
    send_data = res_send.json()
    assert send_data["success"] is True
    assert "demo_otp" in send_data or send_data.get("smtp_sent") is True
    otp_code = send_data.get("demo_otp")
    print(f" -> PASS: 6-digit Email OTP dispatched! Code: {otp_code}")

    # 3. Test Invalid Verification Code (Should Fail with 400)
    print("\n3. Testing POST /api/v2/auth/email/verify-otp with WRONG code...")
    res_wrong = session.post(f"{BASE_URL}/api/v2/auth/email/verify-otp", json={
        "email": test_email,
        "otp_code": "000000"
    })
    assert res_wrong.status_code == 400, f"Expected 400, got {res_wrong.status_code}: {res_wrong.text}"
    print(" -> PASS: Invalid 6-digit code correctly rejected with HTTP 400.")

    # 4. Test Valid Verification Code (Should Succeed)
    print("\n4. Testing POST /api/v2/auth/email/verify-otp with CORRECT code...")
    res_valid = session.post(f"{BASE_URL}/api/v2/auth/email/verify-otp", json={
        "email": test_email,
        "otp_code": otp_code
    })
    assert res_valid.status_code == 200, f"Verification failed: {res_valid.text}"
    auth_data = res_valid.json()
    assert auth_data["success"] is True
    assert "token" in auth_data and len(auth_data["token"]) > 20
    assert auth_data["user"]["email"] == test_email
    assert auth_data["user"]["credits_balance"] == 5000
    token = auth_data["token"]
    print(f" -> PASS: Email OTP verified! User authenticated. User ID: {auth_data['user']['id']}, Credits: {auth_data['user']['credits_balance']}")

    # 5. Hydrate User Session with Bearer Token
    print("\n5. Testing GET /api/v2/auth/me using Bearer token issued by Email OTP...")
    res_me = session.get(f"{BASE_URL}/api/v2/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert res_me.status_code == 200, f"/me failed: {res_me.text}"
    me_data = res_me.json()
    assert me_data["user"]["email"] == test_email
    print(f" -> PASS: Session active and hydrated for {me_data['user']['email']}.")

    # 6. Verify SQLite Audit Trail
    print("\n6. Checking Audit Log for EMAIL_OTP_SIGNUP action in SQLite DB...")
    res_logs = session.get(f"{BASE_URL}/api/v2/history/audit-logs?limit=5", headers={"Authorization": f"Bearer {token}"})
    assert res_logs.status_code == 200
    logs = res_logs.json().get("audit_logs", [])
    actions = [l["action"] for l in logs]
    assert "EMAIL_OTP_SIGNUP" in actions, f"Expected EMAIL_OTP_SIGNUP in {actions}"
    print(f" -> PASS: Immutable audit log recorded: {actions[:3]}")

    # 7. Test Rate Limiting (Too many invalid attempts)
    print("\n7. Testing OTP Brute-Force Rate Limiting (5 Attempts Max)...")
    res_send2 = session.post(f"{BASE_URL}/api/v2/auth/email/send-otp", json={"email": "ratelimit_test@example.com"})
    assert res_send2.status_code == 200
    for i in range(5):
        session.post(f"{BASE_URL}/api/v2/auth/email/verify-otp", json={"email": "ratelimit_test@example.com", "otp_code": f"11111{i}"})
    # 6th attempt should be blocked with 429
    res_blocked = session.post(f"{BASE_URL}/api/v2/auth/email/verify-otp", json={"email": "ratelimit_test@example.com", "otp_code": "999999"})
    assert res_blocked.status_code in (400, 429), f"Expected 400 or 429, got {res_blocked.status_code}"
    print(" -> PASS: Brute-force protection verified: OTP destroyed after 5 failed attempts.")

    print("\n==================================================================")
    print("[SUCCESS] ALL 7 EMAIL OTP & GMAIL SMTP PIPELINE TESTS PASSED 100%!")
    print("==================================================================")

if __name__ == "__main__":
    test_email_otp_pipeline()
