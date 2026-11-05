"""Test helper: lets the suite exercise the real Clerk-JWT verification path offline.

Generates an RSA keypair, makes `api.auth_routes` trust it as the Clerk JWKS, and mints
Clerk-shaped session tokens. Nothing here ever reaches the network.
"""
import os
import time
import uuid
from types import SimpleNamespace
from unittest import mock

import jwt
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa

ISSUER = "https://test-app.clerk.accounts.dev"


def _new_key():
    return rsa.generate_private_key(public_exponent=65537, key_size=2048)


class ClerkTestAuth:
    def __init__(self, admin_emails: str = ""):
        self.private_key = _new_key()
        self.admin_emails = admin_emails
        self._patches = []
        self.created_ids = []

    def start(self):
        pub = self.private_key.public_key()
        fake_client = SimpleNamespace(get_signing_key_from_jwt=lambda _tok: SimpleNamespace(key=pub))
        env = {"CLERK_ISSUER": ISSUER, "ADMIN_EMAILS": self.admin_emails, "CLERK_SECRET_KEY": ""}
        self._patches = [
            mock.patch.dict(os.environ, env),
            mock.patch("api.auth_routes._jwk_client", lambda _issuer: fake_client),
        ]
        for p in self._patches:
            p.start()
        return self

    def stop(self):
        for p in reversed(self._patches):
            p.stop()
        self._patches = []
        self.cleanup_users()

    def cleanup_users(self):
        if not self.created_ids:
            return
        from db.database import SessionLocal
        from db.models import AuditLogEntry, User

        db = SessionLocal()
        try:
            for uid in self.created_ids:
                db.query(AuditLogEntry).filter(AuditLogEntry.user_id == uid).delete()
                db.query(User).filter(User.id == uid).delete()
            db.commit()
        finally:
            db.close()
        self.created_ids = []

    def new_identity(self, email=None):
        uid = f"user_test_{uuid.uuid4().hex[:20]}"
        self.created_ids.append(uid)
        return uid, email or f"{uid}@example.test"

    def token(self, sub, email, key=None, alg="RS256", **overrides):
        now = int(time.time())
        claims = {
            "sub": sub,
            "iss": ISSUER,
            "iat": now,
            "exp": now + 60,
            "email": email,
            "email_verified": True,
            "name": "Test User",
        }
        claims.update(overrides)
        claims = {k: v for k, v in claims.items() if v is not None}
        return jwt.encode(claims, key or self.private_key, algorithm=alg, headers={"kid": "test"})

    @staticmethod
    def headers(token):
        return {"Authorization": f"Bearer {token}"}
