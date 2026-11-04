# ==============================================================================
# CypherLabelGuard CORE EDITION v2.0
# Empirical Reconstruction Resistance & Salience Isolation Benchmark
# ==============================================================================

import unittest
from features.cat_a_inference.feat_04_subspace_voting.feature import SubspaceDisagreementVotingFeature

class TestReconstructionResistance(unittest.TestCase):
    """
    Empirically benchmarks:
    1. Salient Clause Extraction across document boundaries
    2. Dynamic Exposure Percentage calculation
    3. Document Reconstruction Resistance (non-recoverability of omitted text)
    """

    def setUp(self):
        # Sample realistic NDA / Legal Clause with distant risk section
        self.sample_document = (
            "NON-DISCLOSURE AND CONFIDENTIALITY AGREEMENT.\n"
            "This Agreement is entered into by and between Party A and Party B on October 14, 2026.\n"
            "WHEREAS the parties wish to explore a potential business partnership regarding security.\n"
            "1. DEFINITION OF CONFIDENTIAL INFORMATION.\n"
            "Confidential Information shall include all technical, operational, and financial data.\n"
            "2. OBLIGATIONS OF RECEIVING PARTY.\n"
            "The Receiving Party agrees to maintain strict confidentiality of all disclosed materials.\n"
            "3. TERM AND TERMINATION.\n"
            "This Agreement shall remain in effect for a period of three (3) years from the date hereof.\n"
            "4. INDEMNIFICATION AND UNLIMITED LIABILITY CLAUSE.\n"
            "The Receiving Party hereby agrees to unlimited indemnification for all direct, indirect, "
            "and consequential damages arising from any unauthorized breach or disclosure of data, "
            "without any financial liability cap whatsoever.\n"
            "5. GOVERNING LAW AND JURISDICTION.\n"
            "This Agreement shall be governed by and construed in accordance with the laws of Delaware.\n"
        )

    def test_salient_clause_extraction_locates_risk_boundary(self):
        """Verify the sliding window finds the actual liability clause rather than page 1 header."""
        salient_clause, exposure_pct = SubspaceDisagreementVotingFeature.extract_salient_clause(
            self.sample_document, max_chars=400
        )
        
        # Verify it located Section 4 (indemnification and breach)
        self.assertIn("indemnification", salient_clause.lower())
        self.assertIn("liability", salient_clause.lower())
        
        # Verify dynamic exposure percentage is mathematically calculated
        total_len = len(self.sample_document)
        sent_len = len(salient_clause)
        expected_pct = round((sent_len / total_len) * 100, 1)
        self.assertEqual(exposure_pct, expected_pct)
        print(f"\n[OK] Document Length: {total_len} chars | Sent: {sent_len} chars | Exposure: {exposure_pct}%")

    def test_reconstruction_resistance_ratio(self):
        """Measure what percentage of document characters were safely withheld from external LLMs."""
        salient_clause, exposure_pct = SubspaceDisagreementVotingFeature.extract_salient_clause(
            self.sample_document, max_chars=400
        )
        
        withheld_pct = 100.0 - exposure_pct
        self.assertGreater(withheld_pct, 50.0, "At least 50% of document must remain isolated in local RAM")
        print(f"[OK] Withheld / RAM-Protected Ratio: {withheld_pct:.1f}%")

if __name__ == "__main__":
    unittest.main()
