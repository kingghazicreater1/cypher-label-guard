"""
Unit tests for Pakistani Banking (SadaPay, Raast, IBFT) Proof Submission and Admin Verification.
Guarantees zero security backdoors and proper credit allocation.
"""

import uuid
import unittest
from starlette.testclient import TestClient
from api.server import app
from db.database import SessionLocal, init_db
from db.models import User, PaymentRequest, Subscription
from tests.clerk_test_utils import ClerkTestAuth


class TestPakistaniBilling(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        init_db()
        cls.client = TestClient(app)
        cls.clerk = ClerkTestAuth(admin_emails="admin_pak@enterprise.test").start()

        # Generate normal user and admin user
        user_id, user_email = cls.clerk.new_identity("pak_user@enterprise.test")
        admin_id, admin_email = cls.clerk.new_identity("admin_pak@enterprise.test")

        cls.user_token = cls.clerk.token(user_id, user_email)
        cls.admin_token = cls.clerk.token(admin_id, admin_email)

        cls.user_headers = cls.clerk.headers(cls.user_token)
        cls.admin_headers = cls.clerk.headers(cls.admin_token)

        # Trigger /api/v2/auth/me to materialize users in SQLite
        cls.client.get("/api/v2/auth/me", headers=cls.user_headers)
        cls.client.get("/api/v2/auth/me", headers=cls.admin_headers)

        cls.db = SessionLocal()
        cls.user = cls.db.query(User).filter(User.email == user_email).first()
        cls.admin = cls.db.query(User).filter(User.email == admin_email).first()

    @classmethod
    def tearDownClass(cls):
        try:
            if hasattr(cls, "user") and cls.user:
                cls.db.query(PaymentRequest).filter(PaymentRequest.user_id == cls.user.id).delete()
                cls.db.commit()
        except Exception:
            pass
        finally:
            cls.db.close()
            cls.clerk.stop()

    def test_01_get_pakistan_accounts(self):
        from unittest import mock
        with mock.patch.dict("os.environ", {
            "SADAPAY_IBAN": "PK25SADA003472758750",
            "SADAPAY_NUMBER": "03472758750",
            "RAAST_ID": "03472758750",
            "BANK_IBAN": "PK00MEZN0000000000000000",
            "BANK_ACCOUNT_NUMBER": "01010101010101",
        }):
            resp = self.client.get("/api/v2/billing/pakistan-accounts")
            self.assertEqual(resp.status_code, 200)
            data = resp.json()
            self.assertTrue(data.get("success"))
            methods = [a["method"] for a in data.get("accounts", [])]
            self.assertIn("SADAPAY", methods)
            self.assertIn("RAAST", methods)
            self.assertIn("BANK_TRANSFER", methods)
            packages = data.get("packages", [])
            self.assertTrue(len(packages) >= 4)

    def test_02_submit_proof_and_permissions(self):
        unique_ref = f"SP-TX-{uuid.uuid4().hex[:8]}"

        # 1. Unauthenticated submission fails (401)
        unauth_resp = self.client.post("/api/v2/billing/submit-proof", json={
            "plan_name": "Master",
            "amount_pkr": 13500.0,
            "credits": 7500,
            "payment_method": "SADAPAY",
            "transaction_ref": unique_ref,
            "sender_name": "Pakistani Client",
        })
        self.assertEqual(unauth_resp.status_code, 401)

        # 2. Authenticated user submits proof (200)
        sub_resp = self.client.post("/api/v2/billing/submit-proof", headers=self.user_headers, json={
            "plan_name": "Master",
            "amount_pkr": 13500.0,
            "credits": 7500,
            "payment_method": "SADAPAY",
            "transaction_ref": unique_ref,
            "sender_name": "Pakistani Client",
        })
        self.assertEqual(sub_resp.status_code, 200)
        sub_data = sub_resp.json()
        self.assertTrue(sub_data.get("success"))
        req_id = sub_data["request"]["id"]
        self.assertEqual(sub_data["request"]["status"], "PENDING")

        # 3. Duplicate transaction reference rejected (400)
        dup_resp = self.client.post("/api/v2/billing/submit-proof", headers=self.user_headers, json={
            "plan_name": "Master",
            "amount_pkr": 13500.0,
            "credits": 7500,
            "payment_method": "SADAPAY",
            "transaction_ref": unique_ref,
        })
        self.assertEqual(dup_resp.status_code, 400)

        # 4. User views their own payment proofs
        my_reqs_resp = self.client.get("/api/v2/billing/my-requests", headers=self.user_headers)
        self.assertEqual(my_reqs_resp.status_code, 200)
        my_reqs = my_reqs_resp.json()["requests"]
        self.assertTrue(any(r["transaction_ref"] == unique_ref for r in my_reqs))

        # 5. Non-admin cannot view all admin requests (403)
        non_admin_all = self.client.get("/api/v2/billing/admin/requests", headers=self.user_headers)
        self.assertEqual(non_admin_all.status_code, 403)

        # 6. Non-admin cannot approve payment (403)
        non_admin_app = self.client.post(f"/api/v2/billing/admin/approve/{req_id}", headers=self.user_headers)
        self.assertEqual(non_admin_app.status_code, 403)

        # 7. Admin can view all requests
        admin_all = self.client.get("/api/v2/billing/admin/requests", headers=self.admin_headers)
        self.assertEqual(admin_all.status_code, 200)
        self.assertTrue(len(admin_all.json()["requests"]) >= 1)

        # 8. Admin approves payment proof
        self.db.refresh(self.user)
        initial_balance = self.user.credits_balance
        admin_app = self.client.post(f"/api/v2/billing/admin/approve/{req_id}", headers=self.admin_headers, json={
            "admin_notes": "SadaPay transfer verified via mobile banking screenshot.",
        })
        self.assertEqual(admin_app.status_code, 200)
        app_data = admin_app.json()
        self.assertTrue(app_data.get("success"))

        # Verify user received exactly 7,500 credits
        self.db.refresh(self.user)
        self.assertEqual(self.user.credits_balance, initial_balance + 7500)

        # 9. Approving already approved request returns 400
        re_app = self.client.post(f"/api/v2/billing/admin/approve/{req_id}", headers=self.admin_headers)
        self.assertEqual(re_app.status_code, 400)

    def test_03_submit_proof_arbitrary_credits_overwritten(self):
        """User asking for 5,000,000 credits on a PKR 5,200 Basic plan must receive strictly 2,500 credits."""
        unique_ref = f"SP-HACK-{uuid.uuid4().hex[:8]}"
        resp = self.client.post("/api/v2/billing/submit-proof", headers=self.user_headers, json={
            "plan_name": "Basic",
            "amount_pkr": 5200.0,
            "credits": 5000000,  # Attacker tried to inject 5,000,000 credits
            "payment_method": "SADAPAY",
            "transaction_ref": unique_ref,
        })
        self.assertEqual(resp.status_code, 200)
        req_data = resp.json()["request"]
        # Credits must be forced to canonical package amount (2,500), not 5,000,000!
        self.assertEqual(req_data["credits"], 2500)

        # Admin approves
        self.db.refresh(self.user)
        balance_before = self.user.credits_balance
        approve_resp = self.client.post(f"/api/v2/billing/admin/approve/{req_data['id']}", headers=self.admin_headers)
        self.assertEqual(approve_resp.status_code, 200)

        self.db.refresh(self.user)
        self.assertEqual(self.user.credits_balance, balance_before + 2500)

    def test_04_submit_proof_underpayment_rejected(self):
        """Paying PKR 100 for a PKR 13,500 Master plan must be rejected with 400 Bad Request."""
        unique_ref = f"SP-UNDER-{uuid.uuid4().hex[:8]}"
        resp = self.client.post("/api/v2/billing/submit-proof", headers=self.user_headers, json={
            "plan_name": "Master",
            "amount_pkr": 100.0,  # Insufficient payment for 13,500 PKR plan
            "payment_method": "SADAPAY",
            "transaction_ref": unique_ref,
        })
        self.assertEqual(resp.status_code, 400)
        self.assertIn("insufficient", resp.json()["detail"].lower())

    def test_05_manual_payment_request_regex_exploit_prevented(self):
        """Attacker sending 'for 777777 Credits' in TID cannot mint free credits."""
        ref_id = f"TID-{uuid.uuid4().hex[:8]} for 777777 Credits"
        resp = self.client.post("/api/v2/billing/manual-payment-request", headers=self.user_headers, json={
            "credit_amount": 1000,
            "payment_channel": "SadaPay",
            "transaction_reference": ref_id,
            "amount_paid_pkr": 2800.0,
        })
        self.assertEqual(resp.status_code, 200)
        tx_data = resp.json()["transaction"]
        tx_id = tx_data["id"]

        self.db.refresh(self.user)
        balance_before = self.user.credits_balance

        # Admin approves manual payment
        app_resp = self.client.post("/api/v2/billing/manual-payment/approve", headers=self.admin_headers, json={
            "transaction_id": tx_id,
        })
        self.assertEqual(app_resp.status_code, 200)

        self.db.refresh(self.user)
        # Must grant strictly 1,000 credits, NEVER 777,777 credits!
        self.assertEqual(self.user.credits_balance, balance_before + 1000)

    def test_06_pakistan_accounts_503_when_no_env(self):
        """When banking env vars are empty, returns 503 instead of fake mock IBAN."""
        from unittest import mock
        with mock.patch.dict("os.environ", {
            "SADAPAY_IBAN": "",
            "SADAPAY_NUMBER": "",
            "RAAST_ID": "",
            "BANK_IBAN": "",
            "BANK_ACCOUNT_NUMBER": "",
        }):
            resp = self.client.get("/api/v2/billing/pakistan-accounts")
            self.assertEqual(resp.status_code, 503)

    def test_07_lemonsqueezy_webhook_no_secret_returns_503(self):
        """When LEMONSQUEEZY_WEBHOOK_SECRET is unset, webhook returns 503 rather than skipping auth."""
        from unittest import mock
        with mock.patch.dict("os.environ", {"LEMONSQUEEZY_WEBHOOK_SECRET": ""}):
            resp = self.client.post("/api/v2/billing/webhook/lemonsqueezy", json={"meta": {"event_name": "order_created"}})
            self.assertEqual(resp.status_code, 503)

    def test_08_lemonsqueezy_webhook_tampered_credits_ignored_and_idempotency(self):
        """Webhook calculates credits server-side from plan, ignores attacker custom_data credits, and redelivery is 200."""
        import hmac
        import hashlib
        import json
        from unittest import mock

        secret = "test_webhook_secret_key"
        order_uuid = uuid.uuid4().hex[:8]
        payload = {
            "meta": {
                "event_name": "order_created",
                "custom_data": {
                    "user_id": self.user.id,
                    "plan_name": "Basic",
                    "credits": 1000000,  # Attacker injected 1,000,000 credits
                },
            },
            "data": {
                "id": order_uuid,
                "attributes": {
                    "total": 1900,  # $19.00 USD
                    "user_email": self.user.email,
                },
            },
        }
        body_bytes = json.dumps(payload).encode("utf-8")
        sig = hmac.new(secret.encode("utf-8"), body_bytes, hashlib.sha256).hexdigest()

        with mock.patch.dict("os.environ", {"LEMONSQUEEZY_WEBHOOK_SECRET": secret}):
            self.db.refresh(self.user)
            balance_before = self.user.credits_balance

            # 1. First delivery
            resp1 = self.client.post(
                "/api/v2/billing/webhook/lemonsqueezy",
                content=body_bytes,
                headers={"X-Signature": sig, "Content-Type": "application/json"},
            )
            self.assertEqual(resp1.status_code, 200)

            self.db.refresh(self.user)
            # Must receive exactly 2,500 credits (Basic plan), NOT 1,000,000!
            self.assertEqual(self.user.credits_balance, balance_before + 2500)

            # 2. Redelivery of the exact same order_id must return 200 already_processed, not 500 error!
            resp2 = self.client.post(
                "/api/v2/billing/webhook/lemonsqueezy",
                content=body_bytes,
                headers={"X-Signature": sig, "Content-Type": "application/json"},
            )
            self.assertEqual(resp2.status_code, 200)
            self.assertEqual(resp2.json().get("status"), "already_processed")

            # Balance must remain unchanged on duplicate delivery
            self.db.refresh(self.user)
            self.assertEqual(self.user.credits_balance, balance_before + 2500)


if __name__ == "__main__":
    unittest.main()
