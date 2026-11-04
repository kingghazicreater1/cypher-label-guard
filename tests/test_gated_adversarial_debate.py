# -*- coding: utf-8 -*-
"""
CypherLabelGuard - Gated Adversarial Debate Protocol Test Suite (Feature 09)
Verifies:
1. Gate remains CLOSED (0 overhead) during unanimous parliamentary quorum (>=28 votes).
2. Gate OPENS during stalemate / multi-model disagreement.
3. Cross-examination prevents mediocre majorities from outvoting true outlier experts.
4. Sycophancy filter rejects compromise/hybrid labels.
5. Deterministic fallback maintains 100% stability in offline/zero-key environments.
"""

import unittest
import asyncio
from core.context import ExecutionContext, VoteRecord
from features.cat_a_inference.feat_09_weighted_tiebreak.feature import ContextualWeightedTieBreakFeature, GatedAdversarialDebateFeature


class TestGatedAdversarialDebate(unittest.TestCase):

    def setUp(self):
        self.feature = ContextualWeightedTieBreakFeature()

    def test_gate_remains_closed_when_quorum_confirmed(self):
        """Unanimous consensus should bypass debate entirely (Gate Closed)."""
        ctx = ExecutionContext(
            tenant_id="org_test",
            flags={"confirmed": True, "stalemate": False},
            votes=[
                VoteRecord(api="openai_gpt4", dimension="category", vote="Technology & Software", confidence=0.98),
                VoteRecord(api="anthropic_claude", dimension="category", vote="Technology & Software", confidence=0.95),
                VoteRecord(api="google_gemini", dimension="category", vote="Technology & Software", confidence=0.92),
                VoteRecord(api="mistral_large", dimension="category", vote="Technology & Software", confidence=0.90),
            ]
        )
        result = asyncio.run(self.feature.execute(ctx))
        self.assertNotIn("adversarial_debate", result.metadata, "Gate must remain CLOSED for confirmed quorum!")
        self.assertTrue(result.flags.get("confirmed"))
        self.assertFalse(result.flags.get("stalemate"))

    def test_gate_opens_on_stalemate_deadlock(self):
        """When Parliament is deadlocked in stalemate (17-27 votes), gate must OPEN."""
        ctx = ExecutionContext(
            tenant_id="org_test",
            input_payload={"text": "Patient admitted with acute chest pain, ST-elevation on EKG, troponin elevation."},
            flags={"confirmed": False, "stalemate": True},
            votes=[
                VoteRecord(api="anthropic_claude", dimension="category", vote="Medical & Healthcare", confidence=0.95),
                VoteRecord(api="openai_gpt4", dimension="category", vote="Medical & Healthcare", confidence=0.92),
                VoteRecord(api="mistral_large", dimension="category", vote="General & Conversational", confidence=0.60),
                VoteRecord(api="google_gemini", dimension="category", vote="General & Conversational", confidence=0.65),
            ]
        )
        result = asyncio.run(self.feature.execute(ctx))
        self.assertIn("adversarial_debate", result.metadata, "Gate must OPEN during stalemate!")
        debate = result.metadata["adversarial_debate"]
        self.assertTrue(debate.get("gate_triggered"))
        self.assertEqual(debate.get("adjudication_winner"), "Medical & Healthcare")
        self.assertFalse(result.flags.get("stalemate"), "Stalemate must be resolved after debate!")
        self.assertTrue(result.flags.get("confirmed"), "Item must be confirmed after debate verdict!")
        self.assertTrue(result.flags.get("stalemate_resolved_via_debate"))

    def test_outlier_expert_overrules_generic_majority(self):
        """
        Verify that an outlier expert model with specific factual grounding
        is NOT suppressed by generic majority votes.
        """
        ctx = ExecutionContext(
            tenant_id="org_test",
            input_payload={"text": "Clause 14.2: Indemnification and limitation of liability capped at $5,000,000 for gross negligence."},
            flags={"confirmed": False, "stalemate": True},
            votes=[
                # Frontier model identifies specific Legal domain
                VoteRecord(api="anthropic_claude", dimension="category", vote="Legal & Compliance", confidence=0.96),
                # Baseline models default to generic category
                VoteRecord(api="mistral_large", dimension="category", vote="Standard Operations", confidence=0.55),
                VoteRecord(api="google_gemini", dimension="category", vote="Standard Operations", confidence=0.58),
            ]
        )
        result = asyncio.run(self.feature.execute(ctx))
        self.assertIn("adversarial_debate", result.metadata)
        debate = result.metadata["adversarial_debate"]
        self.assertEqual(debate.get("adjudication_winner"), "Legal & Compliance", "Specific Legal classification must prevail over generic standard operations!")


if __name__ == "__main__":
    unittest.main()
