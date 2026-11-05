# ==============================================================================
# SECURITY TEST SUITE: tests/test_clerk_auth.py
# Proves the backend authenticates ONLY via signature-verified Clerk tokens and
# that every legacy bypass (commander-unlock, signup/login, google, phone) is gone.
# ==============================================================================
import time
import unittest
from unittest import mock

import jwt
from cryptography.hazmat.primitives.asymmetric import rsa
from starlette.testclient import TestClient

from api.server import app
from tests.clerk_test_utils import ClerkTestAuth, ISSUER


class TestClerkAuth(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.auth = ClerkTestAuth(admin_emails="boss@example.test").start()
        cls.client = TestClient(app)

    @classmethod
    def tearDownClass(cls):
        cls.auth.stop()

    # ---- removed endpoints -------------------------------------------------
    def test_legacy_endpoints_are_gone(self):
        for path in (
            "/api/v2/auth/commander-unlock",
            "/api/v2/auth/signup",
            "/api/v2/auth/login",
            "/api/v2/auth/google",
            "/api/v2/auth/phone/send-otp",
            "/api/v2/auth/phone/verify-otp",
        ):
            resp = self.client.post(path, json={"email": "a@b.co", "password": "x" * 8})
            self.assertIn(resp.status_code, (404, 405), path)

    # ---- rejection cases ---------------------------------------------------
    def test_no_header_rejected_on_protected_route(self):
        self.assertEqual(self.client.get("/api/v2/auth/me").status_code, 401)

    def test_forged_unsigned_token_rejected(self):
        now = int(time.time())
        forged = jwt.encode({"sub": "x", "iss": ISSUER, "iat": now, "exp": now + 60, "email": "boss@example.test"}, key=None, algorithm="none")
        self.assertEqual(self.client.get("/api/v2/auth/me", headers=self.auth.headers(forged)).status_code, 401)

    def test_hs256_token_rejected(self):
        uid, email = self.auth.new_identity()
        tok = self.auth.token(uid, email, key="a-shared-secret-of-sufficient-length-123456", alg="HS256")
        self.assertEqual(self.client.get("/api/v2/auth/me", headers=self.auth.headers(tok)).status_code, 401)

    def test_wrong_signing_key_rejected(self):
        uid, email = self.auth.new_identity()
        evil = rsa.generate_private_key(public_exponent=65537, key_size=2048)
        tok = self.auth.token(uid, email, key=evil)
        self.assertEqual(self.client.get("/api/v2/auth/me", headers=self.auth.headers(tok)).status_code, 401)

    def test_wrong_issuer_rejected(self):
        uid, email = self.auth.new_identity()
        tok = self.auth.token(uid, email, iss="https://evil.example.com")
        self.assertEqual(self.client.get("/api/v2/auth/me", headers=self.auth.headers(tok)).status_code, 401)

    def test_expired_token_rejected(self):
        uid, email = self.auth.new_identity()
        past = int(time.time()) - 3600
        tok = self.auth.token(uid, email, iat=past - 60, exp=past)
        self.assertEqual(self.client.get("/api/v2/auth/me", headers=self.auth.headers(tok)).status_code, 401)

    def test_invalid_header_is_not_treated_as_guest(self):
        # A present-but-bad token must be rejected, not silently downgraded to guest.
        resp = self.client.get("/api/v2/history/jobs", headers={"Authorization": "Bearer not-a-real-token"})
        self.assertEqual(resp.status_code, 401)

    def test_unverified_email_claim_rejected(self):
        uid, email = self.auth.new_identity()
        tok = self.auth.token(uid, email, email_verified=False)
        self.assertEqual(self.client.get("/api/v2/auth/me", headers=self.auth.headers(tok)).status_code, 401)

    def test_unconfigured_server_fails_closed(self):
        uid, email = self.auth.new_identity()
        tok = self.auth.token(uid, email)
        with mock.patch("api.auth_routes._issuer", return_value=None):
            resp = self.client.get("/api/v2/auth/me", headers=self.auth.headers(tok))
        self.assertEqual(resp.status_code, 503)

    # ---- success cases -----------------------------------------------------
    def test_valid_token_creates_unprivileged_user(self):
        uid, email = self.auth.new_identity()
        resp = self.client.get("/api/v2/auth/me", headers=self.auth.headers(self.auth.token(uid, email)))
        self.assertEqual(resp.status_code, 200)
        user = resp.json()["user"]
        self.assertEqual(user["email"], email)
        self.assertEqual(user["role"], "User")
        self.assertEqual(resp.json()["credits_balance"], 500)

    def test_clerk_sync_ignores_body_and_returns_no_token(self):
        uid, email = self.auth.new_identity()
        resp = self.client.post(
            "/api/v2/auth/clerk-sync",
            json={"email": "boss@example.test", "full_name": "Impostor", "clerk_id": "someone-else"},
            headers=self.auth.headers(self.auth.token(uid, email)),
        )
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertNotIn("token", data)
        self.assertEqual(data["user"]["email"], email)
        self.assertEqual(data["user"]["role"], "User")

    def test_clerk_sync_without_token_rejected(self):
        resp = self.client.post("/api/v2/auth/clerk-sync", json={"email": "boss@example.test"})
        self.assertEqual(resp.status_code, 401)

    def test_admin_only_for_allowlisted_verified_email(self):
        uid, _ = self.auth.new_identity()
        resp = self.client.get("/api/v2/auth/me", headers=self.auth.headers(self.auth.token(uid, "boss@example.test")))
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json()["user"]["role"], "Administrator")

    def test_normal_user_cannot_change_commander_rates_or_panic_flush(self):
        uid, email = self.auth.new_identity()
        headers = self.auth.headers(self.auth.token(uid, email))
        rates = {
            "base_text_credits": 1,
            "vision_inspection_credits": 1,
            "parliament_consensus_credits": 1,
            "cryptographic_proof_credits": 1,
            "turbo_speed_credits": 1,
        }
        r = self.client.post("/api/v2/billing/rates", json=rates, headers=headers)
        self.assertEqual(r.status_code, 403)
        r = self.client.post("/api/v2/panic-flush", json={"reason": "x"}, headers=headers)
        self.assertEqual(r.status_code, 403)


if __name__ == "__main__":
    unittest.main()
