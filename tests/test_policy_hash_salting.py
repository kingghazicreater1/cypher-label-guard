import re
import unittest
from features.cat_c_privacy.blind_masker import BlindIngressMasker

class TestPolicyHashSalting(unittest.TestCase):
    """
    Unit test for Item 4: policy_hash salting: sha256(salt || policy).
    Guarantees cross-job unlinkability so identical policies never correlate across jobs.
    """

    def test_identical_inputs_generate_distinct_salted_hashes(self):
        """
        Two identical jobs with identical raw text, modality, and criteria
        MUST yield different policy hashes due to per-job cryptographic salt.
        """
        raw_text = "Visual payload: Confidential_Assembly_001.png"
        criteria = [{"name": "Surface Scratch", "type": "Boolean"}]

        hashes = set()
        for i in range(100):
            _, policy_hash, _ = BlindIngressMasker.mask_ingress(
                trace_id="test_fixed_trace",
                raw_text=raw_text,
                modality="IMAGE",
                criteria=criteria,
                workspace_name="Acme Corp Enterprise"
            )
            self.assertTrue(
                re.match(r"^sha256:[a-f0-9]{64}$", policy_hash),
                f"Policy hash format invalid: {policy_hash}"
            )
            hashes.add(policy_hash)

        # All 100 executions MUST yield 100 uniquely salted hashes
        self.assertEqual(len(hashes), 100, "Collision detected in salted policy hashes!")

    def test_cross_job_uncorrelated_entropy(self):
        """
        Calculates Hamming distance bit-divergence between sequential policy hashes.
        Should approximate 50% (mean ~128 bits flipped out of 256) for random cryptographic salt.
        """
        def hex_to_bits(hex_str):
            clean = hex_str.replace("sha256:", "")
            return "".join(f"{int(c, 16):04b}" for c in clean)

        _, hash1, _ = BlindIngressMasker.mask_ingress(
            trace_id="trace_a",
            raw_text="Visual payload: Item.png",
            modality="IMAGE",
            criteria=[]
        )
        _, hash2, _ = BlindIngressMasker.mask_ingress(
            trace_id="trace_b",
            raw_text="Visual payload: Item.png",
            modality="IMAGE",
            criteria=[]
        )

        bits1 = hex_to_bits(hash1)
        bits2 = hex_to_bits(hash2)
        diff_bits = sum(b1 != b2 for b1, b2 in zip(bits1, bits2))

        # 256 bits total. Divergence should be robustly >= 100 bits (statistically normal ~128)
        self.assertGreaterEqual(
            diff_bits,
            90,
            f"Bit divergence too low ({diff_bits}/256). Salt is not providing sufficient cryptographic diffusion."
        )

if __name__ == "__main__":
    unittest.main()
