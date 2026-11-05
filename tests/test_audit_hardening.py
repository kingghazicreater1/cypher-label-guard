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


if __name__ == "__main__":
    unittest.main()

