import json
import unittest
from datetime import datetime, timezone
from db.models import JobRecord

class TestRegression490563(unittest.TestCase):
    """
    Regression Test Suite for Job #490563:
    1. Bug #11: Heading Rejection -> Overall 0.0% Confidence (Never coerced or defaulted).
    2. Anomaly Detection -> consensus_label is REJECTED_ANOMALY and anomaly_detected is True.
    3. Nullish Coalescing Safety: 0.0% confidence must be strictly preserved across serialization.
    """

    def test_heading_anomaly_revokes_overall_confidence_to_zero(self):
        criteria_with_anomaly = [
            {
                "name": "product name",
                "type": "Free Text",
                "value": "[REJECTED: GENERIC_FALLBACK_UNVERIFIED]",
                "confidence": 0.0,
                "agreement": "0 of 4 APIs (Auto-Rejected: GENERIC_FALLBACK_UNVERIFIED)",
                "anomaly": True,
                "anomaly_reason": "Context Guard Triggered"
            }
        ]

        record = JobRecord(
            user_id="test-user-id",
            job_number="490563",
            name="Video container payload: WIN_20260830_21_50_59_Pro.mp4",
            modality="Video",
            status="Completed",
            progress=100,
            labels_count=1,
            cost="$0.005",
            consensus_label="REJECTED_ANOMALY",
            affirmative_votes=0,
            trace_id="test-trace-id",
            lineage_hash="test-hash",
            criteria_json=json.dumps(criteria_with_anomaly),
            created_at=datetime.now(timezone.utc)
        )

        dict_rep = record.to_dict()

        # Bug #11 Verification: overall confidence MUST be 0.0, never null or default 98.4/92.3
        self.assertEqual(
            dict_rep["overall_criteria_confidence"],
            0.0,
            f"Expected overall_criteria_confidence to be 0.0 on anomaly, got {dict_rep['overall_criteria_confidence']}"
        )
        self.assertTrue(dict_rep["anomaly_detected"])
        self.assertEqual(dict_rep["consensus_label"], "REJECTED_ANOMALY")
        self.assertEqual(dict_rep["affirmative_votes"], 0)

    def test_genuine_job_preserves_high_confidence(self):
        criteria_clean = [
            {"name": "Color", "type": "Enum", "value": "Blue", "confidence": 98.0, "anomaly": False},
            {"name": "Quality", "type": "Scale", "value": "9", "confidence": 96.0, "anomaly": False},
        ]

        record = JobRecord(
            user_id="test-user-id",
            job_number="490564",
            name="Vision Inspection: Clean_Widget_01",
            modality="Image",
            status="Completed",
            progress=100,
            labels_count=2,
            cost="$0.005",
            consensus_label="CONFIRMED",
            affirmative_votes=32,
            trace_id="test-trace-clean",
            lineage_hash="test-hash-clean",
            criteria_json=json.dumps(criteria_clean),
            created_at=datetime.now(timezone.utc)
        )

        dict_rep = record.to_dict()
        self.assertEqual(dict_rep["overall_criteria_confidence"], 97.0)
        self.assertFalse(dict_rep["anomaly_detected"])
        self.assertEqual(dict_rep["consensus_label"], "CONFIRMED")
        self.assertEqual(dict_rep["affirmative_votes"], 32)

    def test_zero_heading_yields_zero_confidence_unverified(self):
        """
        Job #525286 Regression Test:
        When a job is launched with 0 custom headings:
        - overall_criteria_confidence MUST strictly be 0.0 (never 98.4 or any other fallback).
        - criteria_results is empty list [].
        """
        record = JobRecord(
            user_id="test-user-id",
            job_number="525286",
            name="Video container payload: WIN_20260830_21_50_59_Pro.mp4",
            modality="Video",
            status="Completed",
            progress=100,
            labels_count=0,
            cost="$0.005",
            consensus_label="COMPLETED",
            affirmative_votes=0,
            trace_id="test-trace-525286",
            lineage_hash="test-hash-525286",
            criteria_json=json.dumps([]),  # 0 custom headings
            created_at=datetime.now(timezone.utc)
        )

        dict_rep = record.to_dict()
        self.assertEqual(
            dict_rep["overall_criteria_confidence"],
            0.0,
            f"0 custom headings MUST produce 0.0 confidence, got {dict_rep['overall_criteria_confidence']}"
        )
        self.assertEqual(dict_rep["criteria_results"], [])

if __name__ == "__main__":
    unittest.main()

