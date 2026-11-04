# ==============================================================================
# TEST SUITE: tests/test_core_sacred.py
# Validates the 4 Sacred Core Files and Core Invariants
# ==============================================================================

import asyncio
import unittest

from core.base_feature import BaseFeature
from core.context import ExecutionContext, VoteRecord
from core.orchestrator import CircuitBreaker, PipelineOrchestrator
from core.registry import FeatureRegistry


class DummyEchoFeature(BaseFeature):
    async def execute(self, context: ExecutionContext) -> ExecutionContext:
        payload = context.input_payload
        return context.evolve(
            metadata={"dummy_echo_processed": True, "input_len": len(str(payload))}
        )


class TestCoreSacred(unittest.IsolatedAsyncioTestCase):

    def test_context_immutability_and_evolution(self):
        ctx1 = ExecutionContext(input_payload={"text": "Original data"})
        ctx2 = ctx1.evolve(metadata={"step": 1})

        # ctx1 should remain completely untouched
        self.assertEqual(ctx1.metadata, {})
        self.assertEqual(ctx2.metadata, {"step": 1})
        self.assertEqual(ctx1.session_id, ctx2.session_id)
        self.assertEqual(ctx1.trace_id, ctx2.trace_id)

    def test_parliament_voting_record(self):
        ctx = ExecutionContext()
        ctx = ctx.with_vote(
            api="openai_gpt4",
            dimension="category",
            vote="Security",
            confidence=0.98,
            reasoning="Clear security incident keywords",
            latency_ms=120.5,
        )

        self.assertEqual(len(ctx.votes), 1)
        vote = ctx.votes[0]
        self.assertEqual(vote.api, "openai_gpt4")
        self.assertEqual(vote.dimension, "category")
        self.assertEqual(vote.vote, "Security")
        self.assertAlmostEqual(vote.confidence, 0.98)

    def test_lineage_sha256_audit_chain(self):
        ctx = ExecutionContext(input_payload={"initial": "state"})
        ctx = ctx.with_lineage_step("STEP_1", {"action": "parse"})
        ctx = ctx.with_lineage_step("STEP_2", {"action": "classify"})

        self.assertEqual(len(ctx.lineage_chain), 3)  # root + 2 steps
        self.assertTrue(ctx.verify_lineage())

    def test_zero_retention_purge(self):
        ctx = ExecutionContext(input_payload={"confidential": "secret credentials"})
        self.assertIn("confidential", ctx.input_payload)

        purged_ctx = ctx.purge()
        self.assertTrue(purged_ctx.is_purged)
        self.assertNotIn("confidential", purged_ctx.input_payload)
        self.assertTrue(purged_ctx.input_payload.get("PURGED"))

    def test_circuit_breaker(self):
        cb = CircuitBreaker("test_api", cooldown_seconds=1.0, max_failures=5)
        self.assertTrue(cb.is_available())

        # Record 3 failures -> trips to OPEN
        cb.record_failure()
        cb.record_failure()
        cb.record_failure()
        self.assertEqual(cb.state, "OPEN")
        self.assertFalse(cb.is_available())

        # Wait out cooldown
        import time
        time.sleep(1.1)
        self.assertTrue(cb.is_available())
        self.assertEqual(cb.state, "HALF_OPEN")

    async def test_orchestrator_feature_execution(self):
        manifest = {
            "id": "feat_test_echo",
            "name": "Echo Feature",
            "category": "CAT_TEST",
            "version": "1.0.0",
            "enabled": True,
        }
        feature = DummyEchoFeature(manifest)
        reg = FeatureRegistry()
        reg._instances["feat_test_echo"] = feature

        orch = PipelineOrchestrator(feature_registry=reg)
        initial_ctx = ExecutionContext(input_payload={"message": "hello"})

        final_ctx = await orch.run_pipeline(
            initial_ctx, feature_pipeline_order=["feat_test_echo"]
        )

        self.assertTrue(final_ctx.is_purged)
        self.assertTrue(final_ctx.verify_lineage())


if __name__ == "__main__":
    unittest.main()
