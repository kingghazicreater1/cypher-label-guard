import json
import unittest
from datetime import datetime, timezone
from db.models import JobRecord

class TestZeroHeadingNeverFalseGreen(unittest.TestCase):
    """
    Bug Class Test: Zero-Heading Jobs Must NEVER Produce False Green Confidence.
    Decoupled from ephemeral job IDs (#184256, #525286, etc.).
    Guarantees that:
    1. A job launched with 0 custom criteria (or empty criteria list) has strictly 0.0% criteria confidence.
    2. Serialization to dictionary/JSON never defaults or coerces empty confidences to 98.4%, 92.3%, or 95.0%.
    3. The criteria_results array is strictly empty, triggering UNVERIFIED state in frontend and backend.
    """

    def test_empty_criteria_strictly_yields_zero_confidence(self):
        record = JobRecord(
            user_id="test-user-id",
            job_number="test-zero-heading-001",
            name="Video container payload: WIN_20260830_21_50_59_Pro.mp4",
            modality="Video",
            status="Completed",
            progress=100,
            labels_count=0,
            cost="$0.005",
            consensus_label="COMPLETED",
            affirmative_votes=0,
            trace_id="test-trace-zero-001",
            lineage_hash="test-hash-zero-001",
            criteria_json=json.dumps([]),  # Zero custom headings
            created_at=datetime.now(timezone.utc)
        )

        dict_rep = record.to_dict()

        # 1. Overall confidence MUST strictly be float 0.0
        self.assertIsInstance(dict_rep["overall_criteria_confidence"], float)
        self.assertEqual(
            dict_rep["overall_criteria_confidence"],
            0.0,
            f"0 custom headings MUST produce 0.0% confidence, got {dict_rep['overall_criteria_confidence']}"
        )

        # 2. Criteria results MUST be empty list
        self.assertEqual(dict_rep["criteria_results"], [])

        # 3. Consensus label must be UNVERIFIED (0 CRITERIA), never Content Safety / Confirmed
        self.assertEqual(dict_rep["consensus_label"], "UNVERIFIED (0 CRITERIA)")
        self.assertEqual(dict_rep["affirmative_votes"], 0)

    def test_none_criteria_strictly_yields_zero_confidence(self):
        record = JobRecord(
            user_id="test-user-id",
            job_number="test-zero-heading-002",
            name="Text catalog classification",
            modality="Text",
            status="Completed",
            progress=100,
            labels_count=0,
            cost="$0.001",
            consensus_label="Content Safety",  # e.g. from generic classifier
            affirmative_votes=4,
            trace_id="test-trace-zero-002",
            lineage_hash="test-hash-zero-002",
            criteria_json=None,  # Null criteria in DB
            created_at=datetime.now(timezone.utc)
        )

        dict_rep = record.to_dict()
        self.assertEqual(dict_rep["overall_criteria_confidence"], 0.0)
        self.assertEqual(dict_rep["criteria_results"], [])
        self.assertEqual(dict_rep["consensus_label"], "UNVERIFIED (0 CRITERIA)")
        self.assertEqual(dict_rep["affirmative_votes"], 0)

if __name__ == "__main__":
    unittest.main()

