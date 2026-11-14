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
from types import SimpleNamespace
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

    def test_mid_confidence_never_leaks_domain_label(self):
        crit = [_crit("name", "Handcrafted soaps", 66.3)]
        decision, votes = bir._compute_decision(
            crit, {"affirmative_votes": 32, "label": "E-Commerce & Retail"}, 66.3
        )
        self.assertEqual(decision, "PARTIAL")
        self.assertNotEqual(decision, "E-Commerce & Retail")
        self.assertEqual(votes, 32)

        low_vote_decision, _ = bir._compute_decision(
            crit, {"affirmative_votes": 11, "label": "E-Commerce & Retail"}, 58.3
        )
        self.assertEqual(low_vote_decision, "HUMAN_REVIEW")

        zero_conf_decision, _ = bir._compute_decision(
            [_crit("name", "Unknown", 0.0)], {"affirmative_votes": 32, "label": "UNKNOWN"}, 0.0
        )
        self.assertEqual(zero_conf_decision, "HUMAN_REVIEW")


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
            self.assertEqual(bir._col_label("price"), "price (PKR, AI estimate)")

    def test_human_review_is_not_billed(self):
        items = [
            {"status": "COMPLETED", "decision": "CONFIRMED"},
            {"status": "COMPLETED", "decision": "PARTIAL"},
            {"status": "COMPLETED", "decision": "HUMAN_REVIEW"},
            {"status": "FAILED"},
        ]
        self.assertEqual(len(bir._billable_items(items)), 2)

    def test_vision_timeout_without_attempted_flag_fails_when_key_set(self):
        timed_out_ctx = SimpleNamespace(
            flags={},
            metadata={"vision_api_attempted": None, "vision_api_ok": None},
        )
        with patch.dict(os.environ, {"GEMINI_API_KEY": "test-key", "GOOGLE_API_KEY": "",
                                     "OPENROUTER_API_KEY": "", "OPENAI_API_KEY": ""}):
            err = bir._vision_failure_reason(timed_out_ctx)
            self.assertIsNotNone(err)
            self.assertIn("timed out", err.lower())

        with patch.dict(os.environ, {"GEMINI_API_KEY": "", "GOOGLE_API_KEY": "",
                                     "OPENROUTER_API_KEY": "", "OPENAI_API_KEY": ""}):
            self.assertIsNone(bir._vision_failure_reason(timed_out_ctx))

        ok_ctx = SimpleNamespace(
            flags={"vision_processed": True},
            metadata={"vision_api_attempted": True, "vision_api_ok": True},
        )
        with patch.dict(os.environ, {"GEMINI_API_KEY": "test-key"}):
            self.assertIsNone(bir._vision_failure_reason(ok_ctx))

    def test_vision_timeout_triggers_failed_and_zero_billing_in_batch(self):
        bid = "test_vision_timeout_batch"
        bir.IMAGE_BATCH_REGISTRY[bid] = {
            "batch_id": bid,
            "owner_id": "u1",
            "name": "t",
            "folder_name": "f",
            "depth_tier": "Standard",
            "status": "QUEUED",
            "total": 1,
            "done": 0,
            "failed": 0,
            "progress_pct": 0.0,
            "start_ts": 0.0,
            "precharged_credits": 5,
            "credits_charged": 5,
            "criteria": [{"name": "name of product"}],
            "items": [{"index": 0, "name": "ga3139.jpg", "image_data": "data:image/jpeg;base64,/9j/4AAQ",
                       "status": "QUEUED"}],
        }

        async def _fake_pipeline(_ctx):
            return SimpleNamespace(
                flags={},  # Orchestrator timeout returned unmodified context (no vision_processed)
                metadata={"criteria_results": [_crit("name of product", "Smartphone", 95.0)]},
                trace_id="trace-timeout",
            )

        fake_db = SimpleNamespace(
            query=lambda *_a, **_kw: SimpleNamespace(filter=lambda *_f: SimpleNamespace(first=lambda: None)),
            add=lambda *_a, **_kw: None,
            commit=lambda: None,
            rollback=lambda: None,
            close=lambda: None,
        )
        try:
            with patch.dict(os.environ, {"GEMINI_API_KEY": "test-key"}), \
                 patch.object(bir.orchestrator, "run_pipeline", side_effect=_fake_pipeline), \
                 patch.object(bir, "SessionLocal", return_value=fake_db):
                asyncio.run(bir._run_batch(bid, "u1", "u@test", "Standard", [{"name": "name of product"}]))
            item = bir.IMAGE_BATCH_REGISTRY[bid]["items"][0]
            self.assertEqual(item["status"], "FAILED")
            self.assertIn("timed out", item["error"].lower())
            self.assertEqual(len(bir._billable_items(bir.IMAGE_BATCH_REGISTRY[bid]["items"])), 0)
        finally:
            bir.IMAGE_BATCH_REGISTRY.pop(bid, None)

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
        with patch.dict(os.environ, {"REPORT_PRICE_CURRENCY": ""}):
            header = self._get("csv").body.decode().splitlines()[0]
        self.assertIn("currency not specified", header)
        with patch.dict(os.environ, {"REPORT_PRICE_CURRENCY": "PKR"}):
            header = self._get("csv").body.decode().splitlines()[0]
        self.assertIn("PKR, AI estimate", header)

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


class TestCriteriaConcordanceFairness(unittest.TestCase):
    def setUp(self):
        from features.cat_a_inference.feat_04_subspace_voting.feature import SubspaceDisagreementVotingFeature
        self.feat_cls = SubspaceDisagreementVotingFeature

    def test_prose_paraphrases_reach_consensus_even_with_semicolon(self):
        votes = {
            "groq": "Vibrant vine tomatoes paired with crisp basil; unbranded produce ready for gourmet cooking.",
            "gemini": "Fresh vine-ripened red tomatoes and aromatic green basil leaves presented naturally on wood.",
            "openrouter": "High quality tomatoes on the vine with fragrant basil leaves displayed on a rustic table.",
        }
        vals = list(votes.values())
        self.assertTrue(self.feat_cls._is_generative_prose_criterion(
            "detail of product in 50 words", "Free Text", vals, True
        ))
        chosen, ratio, agree_str, freq = self.feat_cls._compute_prose_concordance(
            votes, vals, "detail of product in 50 words", 3, {"tomato", "basil"}, True
        )
        self.assertEqual(ratio, 1.0)
        self.assertEqual(freq, 3)
        self.assertIn("Semantic Prose Consensus", agree_str)
        self.assertTrue(chosen.endswith("."))

    def test_conflicting_prose_is_never_merged(self):
        votes = {
            "groq": "This bottle is badly cracked, broken, and appears counterfeit with damaged label.",
            "gemini": "A pristine, authentic, undamaged glass bottle in brand-new retail condition.",
        }
        vals = list(votes.values())
        _, ratio, _, freq = self.feat_cls._compute_prose_concordance(
            votes, vals, "description", 2, {"bottle"}, True
        )
        self.assertEqual(freq, 1)
        self.assertEqual(ratio, 0.5)

    def test_numeric_estimates_and_short_labels(self):
        res_close = self.feat_cls._compute_numeric_estimate_concordance(
            ["1200", "1500"], "estimate price", "Range", 2, True
        )
        self.assertIsNotNone(res_close)
        _, ratio_close, _, _ = res_close
        self.assertGreaterEqual(ratio_close, 0.85)

        res_range = self.feat_cls._compute_numeric_estimate_concordance(
            ["$5-$10", "0", "$3.00 - $6.00"], "estimate price", "Range", 3, True
        )
        self.assertIsNotNone(res_range)
        _, ratio_range, _, _ = res_range
        self.assertGreaterEqual(ratio_range, 0.70)

        self.assertIsNone(self.feat_cls._compute_numeric_estimate_concordance(
            ["10", "1000"], "estimate price", "Range", 2, True
        ))

        self.assertEqual(self.feat_cls._canonicalize_short_label("Lipstick Set", "Free Text"), "lipstick")
        self.assertEqual(self.feat_cls._canonicalize_short_label("Lipstick", "Free Text"), "lipstick")
        self.assertNotEqual(self.feat_cls._canonicalize_short_label("Yes", "Boolean"), "no")


class TestCatalogExportAndAliases(unittest.TestCase):
    def _sample_state(self):
        return {
            "batch_id": "b_store",
            "user_id": None,
            "name": "Winter Collection",
            "folder_name": "E-Commerce",
            "depth_tier": "Standard",
            "status": "COMPLETED",
            "total": 2,
            "failed": 0,
            "credits_charged": 10,
            "elapsed_seconds": 4.2,
            "criteria": [
                {"name": "name of product"},
                {"name": "estimate price"},
                {"name": "why you should by it ?"},
            ],
            "items": [
                {
                    "name": "dress_maroon.jpg",
                    "status": "COMPLETED",
                    "decision": "CONFIRMED",
                    "votes": "32/32",
                    "overall_confidence": 96.0,
                    "lineage_hash": "lin_1",
                    "trace_id": "trc_1",
                    "criteria_results": [
                        {"name": "name of product", "value": "Maroon Velvet Dress", "confidence": 96.0},
                        {"name": "estimate price", "value": "PKR 4,500", "confidence": 92.0},
                        {
                            "name": "why you should by it ?",
                            "value": "Rich seasonal velvet fabric with traditional embroidery, ready for festive occasions and winter wear.",
                            "confidence": 94.0,
                        },
                    ],
                },
                {
                    "name": "perfume_oud.jpg",
                    "status": "COMPLETED",
                    "decision": "PARTIAL",
                    "votes": "22/32",
                    "overall_confidence": 74.0,
                    "lineage_hash": "lin_2",
                    "trace_id": "trc_2",
                    "criteria_results": [
                        {"name": "name of product", "value": "Royal Oud EDP 100ml", "confidence": 82.0},
                        {"name": "estimate price", "value": "PKR 2,800", "confidence": 68.0},
                        {"name": "why you should by it ?", "value": "Long-lasting woody fragrance.", "confidence": 72.0},
                    ],
                },
            ],
        }

    def test_store_csv_applies_aliases_and_strips_audit_columns(self):
        aliases = json.dumps({
            "name of product": "Product Title",
            "estimate price": "Price (PKR)",
            "why you should by it ?": "Selling Point",
        })
        with patch.dict(bir.IMAGE_BATCH_REGISTRY, {"b_store": self._sample_state()}):
            resp = asyncio.run(
                bir.image_batch_report("b_store", "csv", None, mode="store", aliases=aliases)
            )
        text = resp.body.decode("utf-8")
        first_line = text.splitlines()[0]
        self.assertEqual(first_line, "Photo,Product Title,Price (PKR),Selling Point")
        self.assertNotIn("Votes", text)
        self.assertNotIn("Lineage_Hash", text)
        self.assertIn("Maroon Velvet Dress", text)

    def test_catalog_pdf_creates_one_page_per_product(self):
        aliases = json.dumps({"name of product": "Product Title", "estimate price": "Price (PKR)"})
        with patch.dict(bir.IMAGE_BATCH_REGISTRY, {"b_store": self._sample_state()}):
            resp = asyncio.run(
                bir.image_batch_report("b_store", "pdf", None, layout="catalog", aliases=aliases)
            )
        self.assertTrue(resp.body.startswith(b"%PDF"))
        # 2 items -> ReportLab root /Pages /Count 2
        self.assertIn(b"/Count 2", resp.body)

    def test_history_export_supports_store_csv_and_catalog_pdf(self):
        from sqlalchemy import create_engine
        from sqlalchemy.orm import sessionmaker
        from db.database import Base
        from db.models import User, JobRecord
        from api.history_routes import export_jobs_batch

        engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
        Base.metadata.create_all(bind=engine)
        SessionLocal = sessionmaker(bind=engine)
        db = SessionLocal()
        try:
            u = User(id="u_store", email="store@example.com", hashed_password="x", role="User")
            db.add(u)
            for idx, (fname, title) in enumerate([("bag.jpg", "Leather Tote Bag"), ("watch.jpg", "Chronograph Watch")], start=1):
                db.add(JobRecord(
                    id=f"id_{idx}",
                    user_id="u_store",
                    job_number=f"JOB-{idx}",
                    name=fname,
                    modality="VISION",
                    status="COMPLETED",
                    consensus_label=title,
                    affirmative_votes=30,
                    folder_name="Shop",
                    trace_id=f"trc_{idx}",
                    criteria_json=json.dumps([
                        {"heading": "name of product", "winning_label": title, "confidence": 95.0},
                        {"heading": "estimate price", "winning_label": "PKR 3,200", "confidence": 91.0},
                    ]),
                ))
            db.commit()

            mock_user = SimpleNamespace(id="u_store", role="User")
            aliases = json.dumps({"name of product": "Product Title", "estimate price": "Price (PKR)"})
            csv_resp = export_jobs_batch(
                folder="Shop", job_ids=None, format="csv", user=mock_user, db=db, mode="store", aliases=aliases
            )
            csv_lines = csv_resp.body.decode("utf-8").splitlines()
            self.assertEqual(csv_lines[0], "Image / Asset Name,Product Title,Price (PKR)")
            self.assertIn("Leather Tote Bag", csv_resp.body.decode("utf-8"))

            pdf_resp = export_jobs_batch(
                folder="Shop", job_ids=None, format="pdf", user=mock_user, db=db, layout="catalog", aliases=aliases
            )
            self.assertTrue(pdf_resp.body.startswith(b"%PDF"))
            self.assertIn(b"/Count 2", pdf_resp.body)
        finally:
            db.close()
            engine.dispose()

    def test_short_phrase_subset_concordance_merges_silver_metal_spoon(self):
        from features.cat_a_inference.feat_04_subspace_voting.feature import SubspaceDisagreementVotingFeature
        # Verify concept stem extraction and subset clustering for "Silver metal spoon", "Silver", "Silver metal"
        stems_1 = SubspaceDisagreementVotingFeature._extract_concept_stems("Silver metal spoon")
        stems_2 = SubspaceDisagreementVotingFeature._extract_concept_stems("Silver")
        stems_3 = SubspaceDisagreementVotingFeature._extract_concept_stems("Silver metal")
        self.assertTrue(stems_2 <= stems_3 <= stems_1)
        self.assertEqual(stems_2, {"silver"})


if __name__ == "__main__":
    unittest.main()
