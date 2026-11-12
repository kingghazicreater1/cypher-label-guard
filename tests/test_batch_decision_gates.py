"""Customer-facing correctness gates for image batches:
  1. Confidence alone can never give CONFIRMED when the parliament quorum was not reached.
  2. Blank (no extraction) photos are detected so they can be failed + refunded.
  3. Price columns carry a currency note; reports include a decision legend.
  4. PDF export renders with fixed column widths and no crash on long values.
"""
import asyncio
import json
import os
import sys
import unittest
from unittest.mock import patch

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from api import batch_images_routes as bir  # noqa: E402


def _crit(name, value, conf, agreement="3 of 4 APIs", anomaly=False, reason=""):
    return {"name": name, "value": value, "confidence": conf, "agreement": agreement,
            "anomaly": anomaly, "anomaly_reason": reason}


class TestDecisionGates(unittest.TestCase):
    def test_single_provider_high_confidence_is_not_confirmed(self):
        crit = [_crit("name of product", "Maroon Dress", 90.0,
                      agreement="1 of 4 APIs (openrouter - Quorum Not Reached, Human Review)")]
        decision, votes = bir._compute_decision(crit, {"affirmative_votes": 11}, 90.0)
        self.assertEqual(decision, "HUMAN_REVIEW")
        self.assertEqual(votes, 11)

    def test_low_votes_without_quorum_text_still_not_confirmed(self):
        crit = [_crit("x", "v", 95.0)]
        decision, _ = bir._compute_decision(crit, {"affirmative_votes": 11}, 95.0)
        self.assertEqual(decision, "HUMAN_REVIEW")

    def test_stalemate_votes_cap_at_partial(self):
        crit = [_crit("x", "v", 95.0)]
        decision, _ = bir._compute_decision(crit, {"affirmative_votes": 21}, 95.0)
        self.assertEqual(decision, "PARTIAL")

    def test_full_quorum_high_confidence_is_confirmed(self):
        crit = [_crit("x", "v", 95.0)]
        decision, votes = bir._compute_decision(crit, {"affirmative_votes": 32}, 95.0)
        self.assertEqual(decision, "CONFIRMED")
        self.assertEqual(votes, 32)

    def test_anomaly_is_rejected(self):
        crit = [_crit("x", "v", 95.0, anomaly=True)]
        decision, _ = bir._compute_decision(crit, {"affirmative_votes": 32}, 95.0)
        self.assertEqual(decision, "REJECTED")


class TestBlankDetection(unittest.TestCase):
    def test_mostly_blank_photo_is_flagged(self):
        crit = [
            _crit("name of product", "Not specified in document", 0.0, anomaly=True,
                  reason="No consensus: AI models did not extract 'name of product' from the payload."),
            _crit("why you should buy it", "Not specified in document", 0.0, anomaly=True,
                  reason="No consensus: AI models did not extract 'why' from the payload."),
            _crit("Quality", "Unverified 2D Capture", 96.0),
            _crit("give a price number", "Not specified", 0.0, anomaly=True,
                  reason="No consensus: AI models did not extract 'price' from the payload."),
            _crit("color of main product", "Red", 95.0),
        ]
        self.assertGreaterEqual(bir._no_extraction_ratio(crit), 0.5)

    def test_normal_photo_not_flagged(self):
        crit = [_crit("name", "Lipstick", 100.0), _crit("color", "red", 100.0)]
        self.assertEqual(bir._no_extraction_ratio(crit), 0.0)


class TestCurrencyAndLegend(unittest.TestCase):
    def test_price_label_flags_missing_currency(self):
        with patch.dict(os.environ, {"REPORT_PRICE_CURRENCY": ""}):
            self.assertIn("currency not specified", bir._col_label("give a price number"))
            self.assertEqual(bir._col_label("Quality"), "Quality")

    def test_price_label_uses_configured_currency(self):
        with patch.dict(os.environ, {"REPORT_PRICE_CURRENCY": "pkr"}):
            self.assertEqual(bir._col_label("price"), "price (PKR)")

    def test_legend_covers_every_decision(self):
        for key in ("CONFIRMED", "PARTIAL", "HUMAN_REVIEW", "REJECTED"):
            self.assertIn(key, bir.DECISION_LEGEND)


class TestReportExport(unittest.TestCase):
    def _state(self):
        long_val = "Multicolor (silver, gold, beige, white, mint green, metallic brown, dark brown, red, glitter, orange, light blue, purple)"
        items = [
            {"name": "a.jpg", "status": "COMPLETED", "decision": "CONFIRMED", "votes": "32/32",
             "overall_confidence": 95.0, "lineage_hash": "abc123def4567890", "trace_id": "t1",
             "criteria_results": [_crit("name of product", "Nail polish bottles", 90.0),
                                  _crit("give a price number", "1200", 90.0),
                                  _crit("color of main product", long_val, 90.0)]},
            {"name": "b.jpg", "status": "FAILED", "error": "No usable labels were extracted for this photo."},
        ]
        return {
            "name": "t", "folder_name": "f", "depth_tier": "Standard", "total": 2, "failed": 1,
            "credits_charged": 5, "elapsed_seconds": 10.0, "status": "COMPLETED", "items": items,
            "criteria": [{"name": "name of product"}, {"name": "give a price number"},
                         {"name": "color of main product"}],
        }

    def _get(self, fmt):
        with patch.object(bir, "_owned", return_value=self._state()):
            return asyncio.run(bir.image_batch_report("b1", fmt, None))

    def test_csv_has_currency_note_in_header(self):
        body = self._get("csv").body.decode()
        self.assertIn("currency not specified", body.splitlines()[0])

    def test_json_contains_legend(self):
        data = json.loads(self._get("json").body)
        self.assertIn("decision_legend", data)

    def test_pdf_builds(self):
        try:
            import reportlab  # noqa: F401
        except ImportError:
            self.skipTest("reportlab not installed")
        resp = self._get("pdf")
        self.assertTrue(resp.body.startswith(b"%PDF"))


if __name__ == "__main__":
    unittest.main()
