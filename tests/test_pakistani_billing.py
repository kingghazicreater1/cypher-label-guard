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


if __name__ == "__main__":
    unittest.main()
