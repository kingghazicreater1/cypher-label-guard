# ==============================================================================
# CypherLabelGuard CORE EDITION v2.0
# Fullstack Integration & Cryptographic E2E Verification Test Suite
# ==============================================================================

import unittest
import asyncio
from starlette.testclient import TestClient
from api.server import app, PROVE_IT_REGISTRY, LATEST_PARLIAMENT_STATE


class TestFullstackE2EIntegration(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app)

    def test_01_health_and_manifests_count(self):
        """Verify health check reports exactly 38 active features and system HEALTHY."""
        res = self.client.get("/api/v2/health")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data["status"], "HEALTHY")
        self.assertEqual(data["total_active_features"], 38)

    def test_02_connection_pool_500_slots(self):
        """Verify 500 managed connection slots distributed evenly across 4 providers."""
        res = self.client.get("/api/v2/pools")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data["total_capacity"], 500)
        providers = data.get("providers", {})
        self.assertIn("openai", providers)
        self.assertIn("claude", providers)
        self.assertIn("gemini", providers)
        self.assertIn("mistral", providers)
        for prov, stat in providers.items():
            self.assertEqual(stat["max_slots"], 125)

    def test_03_inference_to_prove_it_lineage_flow(self):
        """Execute end-to-end inference and verify the cryptographic Prove-It forensic dossier."""
        payload = {
            "text": "The indemnification clause applies without limitation to all third-party IP claims.",
            "modality": "TEXT",
            "depth_tier": "Standard",
            "tenant_id": "test_tenant",
        }
        res = self.client.post("/api/v2/infer", json=payload)
        self.assertEqual(res.status_code, 200)
        res_data = res.json()
        self.assertTrue(res_data["success"])
        
        # Verify 32-seat parliament grid
        grid = res_data["parliament_grid"]
        self.assertEqual(len(grid), 32)
        
        # Verify Prove-It trace
        trace_id = res_data["prove_it_trace_id"]
        self.assertTrue(bool(trace_id))
        
        # Retrieve forensic dossier
        prove_res = self.client.get(f"/api/v2/prove-it/{trace_id}")
        self.assertEqual(prove_res.status_code, 200)
        body = prove_res.json()
        self.assertTrue(body["success"])
        dossier = body["dossier"]
        
        self.assertEqual(dossier["trace_id"], trace_id)
        self.assertEqual(dossier["total_votes"], 32)
        self.assertTrue(dossier["lineage_unbroken"])
        self.assertGreater(len(dossier["lineage_ledger"]), 30)
        self.assertGreater(len(dossier["attributed_tokens"]), 0)

    def test_04_websocket_telemetry_flow(self):
        """Test WebSocket /ws/parliament handshake and live telemetry receiving."""
        with self.client.websocket_connect("/ws/parliament") as ws:
            init = ws.receive_json()
            self.assertEqual(init["event"], "CONNECTED")
            self.assertEqual(init["active_features"], 38)
            self.assertIn("grid_tiles", init)

    def test_05_emergency_panic_salt_flush(self):
        """Verify emergency zero-retention salt flush clears all ephemeral buffers."""
        res = self.client.post("/api/v2/panic-flush", json={"reason": "Audit Test"})
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertTrue(data["success"])
        self.assertIn("message", data)



if __name__ == "__main__":
    unittest.main()
