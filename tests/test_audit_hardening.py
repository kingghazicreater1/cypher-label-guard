"""Regression tests for the bug-hunt hardening pass:
batch ownership/auth, WebSocket auth + tenant-scoped telemetry, explicit guest flag,
honest batch error rows, and per-user parliament state.
"""
import os
import time
import unittest
from unittest import mock

from starlette.testclient import TestClient

from api.server import app, ws_manager, LATEST_PARLIAMENT_STATE
from api import batch_routes
from tests.clerk_test_utils import ClerkTestAuth


class TestAuditHardening(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app)
        cls.clerk = ClerkTestAuth(admin_emails="hardening-admin@example.test").start()
        a_id, a_mail = cls.clerk.new_identity()
        b_id, b_mail = cls.clerk.new_identity()
        cls.a_token = cls.clerk.token(a_id, a_mail)
        cls.b_token = cls.clerk.token(b_id, b_mail)
        cls.a_headers = cls.clerk.headers(cls.a_token)
        cls.b_headers = cls.clerk.headers(cls.b_token)

    @classmethod
    def tearDownClass(cls):
        cls.clerk.stop()

    def setUp(self):
        batch_routes.BATCH_REGISTRY.clear()

    # ---- batch routes -------------------------------------------------------
    def test_batch_status_and_download_require_login(self):
        batch_routes.BATCH_REGISTRY["batch_x"] = {
            "name": "n", "status": "COMPLETED", "total_rows": 1, "completed_rows": 1,
            "progress_pct": 100.0, "overall_confidence": 0.0, "labeled_rows": [{"a": "1"}],
            "start_timestamp": time.time(), "owner_id": "someone",
        }
        self.assertEqual(self.client.get("/api/v2/batch/status/batch_x").status_code, 401)
        self.assertEqual(self.client.get("/api/v2/batch/download/batch_x").status_code, 401)

    def test_batch_is_invisible_to_other_users(self):
        me = self.client.get("/api/v2/auth/me", headers=self.a_headers).json()
        uid = me.get("id") or me.get("user", {}).get("id")
        batch_routes.BATCH_REGISTRY["batch_mine"] = {
            "name": "n", "status": "COMPLETED", "total_rows": 1, "completed_rows": 1,
            "progress_pct": 100.0, "overall_confidence": 0.0, "labeled_rows": [{"a": "1"}],
            "start_timestamp": time.time(), "owner_id": uid,
        }
        self.assertEqual(self.client.get("/api/v2/batch/status/batch_mine", headers=self.a_headers).status_code, 200)
        self.assertEqual(self.client.get("/api/v2/batch/download/batch_mine", headers=self.a_headers).status_code, 200)
        self.assertEqual(self.client.get("/api/v2/batch/status/batch_mine", headers=self.b_headers).status_code, 404)
        self.assertEqual(self.client.get("/api/v2/batch/download/batch_mine", headers=self.b_headers).status_code, 404)

    def test_batch_start_requires_login(self):
        resp = self.client.post("/api/v2/batch/start", json={
            "name": "x", "csv_text": "a\n1", "target_column": "a", "criteria": [], "depth_tier": "Standard",
        })
        self.assertEqual(resp.status_code, 401)

    def test_finished_batches_are_evicted(self):
        batch_routes.BATCH_REGISTRY["old"] = {"status": "COMPLETED", "end_timestamp": time.time() - 10_000}
        batch_routes.BATCH_REGISTRY["live"] = {"status": "PROCESSING"}
        batch_routes._evict_stale_batches()
        self.assertNotIn("old", batch_routes.BATCH_REGISTRY)
        self.assertIn("live", batch_routes.BATCH_REGISTRY)

    # ---- websocket ----------------------------------------------------------
    def test_websocket_rejects_unauthenticated_clients(self):
        with self.client.websocket_connect("/ws/parliament") as ws:
            ws.send_json({"action": "AUTH", "token": "forged.token.value"})
            with self.assertRaises(Exception):
                ws.receive_json()

    def test_websocket_accepts_valid_token_and_scopes_broadcast(self):
        import asyncio
        with self.client.websocket_connect("/ws/parliament") as ws:
            ws.send_json({"action": "AUTH", "token": self.a_token})
            self.assertEqual(ws.receive_json()["event"], "CONNECTED")
            owner_ids = set(ws_manager.active_connections.values())
            self.assertEqual(len(owner_ids), 1)
            owner = next(iter(owner_ids))
            # A broadcast for another tenant, or for nobody, must not reach this client.
            asyncio.run(ws_manager.broadcast({"event": "LEAK"}, owner_id="other-tenant"))
            asyncio.run(ws_manager.broadcast({"event": "LEAK"}, owner_id=None))
            ws.send_json({"action": "PING"})
            self.assertEqual(ws.receive_json()["event"], "PONG")

    def test_parliament_latest_requires_login_and_is_per_user(self):
        self.assertEqual(self.client.get("/api/v2/parliament/latest").status_code, 401)
        resp = self.client.get("/api/v2/parliament/latest", headers=self.b_headers)
        self.assertEqual(resp.status_code, 200)
        self.assertNotIn("state", resp.json())

    # ---- guest flag ---------------------------------------------------------
    def test_guest_inference_needs_explicit_flag(self):
        with mock.patch.dict(os.environ, {"ALLOW_GUEST_INFERENCE": "false"}):
            resp = self.client.post("/api/v2/infer", json={"text": "hello world", "modality": "TEXT"})
            self.assertEqual(resp.status_code, 401)

    # ---- root-cause hardening (LFI, Prove-It isolation, Image Batch, Pools) -
    def test_image_batch_ownership_and_csv_sanitization(self):
        from api import batch_images_routes
        me = self.client.get("/api/v2/auth/me", headers=self.a_headers).json()
        uid = me.get("id") or me.get("user", {}).get("id")
        batch_images_routes.IMAGE_BATCH_REGISTRY["img_mine"] = {
            "batch_id": "img_mine",
            "owner_id": uid,
            "name": "Audit Batch",
            "folder_name": "General Workspace",
            "depth_tier": "Fast",
            "criteria": [{"name": "FormulaCheck", "type": "Free Text", "range": ""}],
            "status": "COMPLETED",
            "total": 1,
            "done": 1,
            "failed": 0,
            "progress_pct": 100.0,
            "concurrency": 5,
            "credits_charged": 1,
            "start_ts": time.time(),
            "elapsed_seconds": 0.5,
            "items": [{
                "index": 0,
                "name": "=CMD|' /C calc'!A0",
                "status": "COMPLETED",
                "decision": "CONFIRMED",
                "votes": "32/32",
                "overall_confidence": 95.0,
                "criteria_results": [{"name": "FormulaCheck", "value": "+SUM(1,2)", "confidence": 95.0}],
            }],
        }
        try:
            # Owner can view status and report
            self.assertEqual(
                self.client.get("/api/v2/batch/images/status/img_mine", headers=self.a_headers).status_code,
                200,
            )
            # Non-owner is blocked with 403
            self.assertEqual(
                self.client.get("/api/v2/batch/images/status/img_mine", headers=self.b_headers).status_code,
                403,
            )
            # Unauthenticated caller is blocked when ALLOW_GUEST_INFERENCE is false
            with mock.patch.dict(os.environ, {"ALLOW_GUEST_INFERENCE": "false"}):
                self.assertEqual(
                    self.client.get("/api/v2/batch/images/status/img_mine").status_code,
                    401,
                )
            # CSV report neutralizes leading '=' and '+' formula characters
            csv_res = self.client.get("/api/v2/batch/images/report/img_mine?format=csv", headers=self.a_headers)
            self.assertEqual(csv_res.status_code, 200)
            self.assertIn("'=CMD|", csv_res.text)
            self.assertIn("'+SUM(1,2)", csv_res.text)
        finally:
            batch_images_routes.IMAGE_BATCH_REGISTRY.pop("img_mine", None)

    def test_prove_it_dossier_tenant_isolation(self):
        from api.server import PROVE_IT_REGISTRY
        me = self.client.get("/api/v2/auth/me", headers=self.a_headers).json()
        uid = me.get("id") or me.get("user", {}).get("id")
        PROVE_IT_REGISTRY["trace_private_a"] = {
            "trace_id": "trace_private_a",
            "_owner_id": uid,
            "total_votes": 32,
            "lineage_unbroken": True,
        }
        try:
            # Owner A succeeds and internal _owner_id is stripped from response
            res_a = self.client.get("/api/v2/prove-it/trace_private_a", headers=self.a_headers)
            self.assertEqual(res_a.status_code, 200)
            self.assertNotIn("_owner_id", res_a.json()["dossier"])
            # User B is denied with 403
            res_b = self.client.get("/api/v2/prove-it/trace_private_a", headers=self.b_headers)
            self.assertEqual(res_b.status_code, 403)
        finally:
            PROVE_IT_REGISTRY.pop("trace_private_a", None)

    def test_vision_lfi_blocked(self):
        import asyncio
        from core.registry import registry
        from core.context import ExecutionContext
        registry.load_all_features()
        feat_35 = registry.get_feature("feat_35_vision_connector")
        ctx = ExecutionContext(
            trace_id="test-lfi-guard",
            input_payload={"modality": "VISION", "text": "test", "image": "README.md"},
        )
        evolved = asyncio.run(feat_35.execute(ctx))
        # Must NOT load local file from disk
        self.assertNotIn("Loaded local specimen file", evolved.input_payload.get("text", ""))

    def test_pools_leased_never_negative(self):
        # Guest is denied with 401
        self.assertEqual(self.client.get("/api/v2/pools").status_code, 401)
        res = self.client.get("/api/v2/pools", headers=self.a_headers)
        self.assertEqual(res.status_code, 200)
        for prov, stats in res.json().get("providers", {}).items():
            self.assertGreaterEqual(stats["leased"], 0, f"Provider {prov} has negative leased slots")
            self.assertEqual(stats["max_slots"], 125)

    def test_billing_subscription_and_cards_blocked_without_stripe(self):
        from api import billing_routes
        with mock.patch.object(billing_routes, "STRIPE_SECRET_KEY", ""):
            r1 = self.client.post("/api/v2/billing/cards", json={
                "card_number": "4242424242424242", "exp_month": 12, "exp_year": 2030, "cvc": "123",
            }, headers=self.a_headers)
            self.assertEqual(r1.status_code, 503)
            r2 = self.client.post("/api/v2/billing/subscription", json={"plan_name": "Team"}, headers=self.a_headers)
            self.assertEqual(r2.status_code, 503)

    def test_folders_and_keys_status_require_auth_and_isolate_tenants(self):
        # Guests blocked on folders and keys/status
        self.assertEqual(self.client.get("/api/v2/history/folders").status_code, 401)
        self.assertEqual(self.client.post("/api/v2/history/folders", json={"name": "SecretFolder"}).status_code, 401)
        self.assertEqual(self.client.get("/api/v2/keys/status").status_code, 401)
        # User A creates a folder; User B must not see User A's folder in GET /history/folders
        res_a = self.client.post("/api/v2/history/folders", json={"name": "UserAPrivateFolder"}, headers=self.a_headers)
        self.assertEqual(res_a.status_code, 200)
        res_b = self.client.get("/api/v2/history/folders", headers=self.b_headers)
        self.assertEqual(res_b.status_code, 200)
        self.assertNotIn("UserAPrivateFolder", res_b.json()["folders"])


if __name__ == "__main__":
    unittest.main()

