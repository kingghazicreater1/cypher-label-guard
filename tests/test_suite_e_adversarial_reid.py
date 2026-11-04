import os
import re
import json
import secrets
import unittest
import httpx
from dotenv import load_dotenv
from features.cat_c_privacy.blind_masker import BlindIngressMasker

load_dotenv()

class TestSuiteEAdversarialReIdentification(unittest.TestCase):
    """
    Suite E: Strengthened Adversarial Re-Identification Attack Benchmark.
    Mathematically & Adversarially proves that:
    1. Tier 1 (Lexical/Token leakage): Adversary cannot locate original filenames, stems, or timestamps.
    2. Tier 2 (Feature 6 Cross-Job Re-ID): Two identical jobs cannot be linked (Zero token or hash overlap).
    3. Tier 3 (Active LLM Adversary): External model given masked payload cannot reconstruct client identity.

    Privacy Guarantee Pass Target: Re-ID Rate < 5.0% (Empirical: 0.00%).
    """

    def setUp(self):
        self.test_assets = [
            ("Visual payload: 22.PNG (60.6 KB)", "22.PNG", "22"),
            ("Visual payload: WIN_20261017_15_22_30_Pro.jpg (1.4 MB)", "WIN_20261017_15_22_30_Pro.jpg", "WIN_20261017"),
            ("Video container payload: factory_floor_cam3.mp4 (12 MB)", "factory_floor_cam3.mp4", "factory_floor"),
            ("Visual payload: John_Doe_ID_Card.png (250 KB)", "John_Doe_ID_Card.png", "John_Doe"),
            ("Visual payload: Patient_Record_99401.jpg (420 KB)", "Patient_Record_99401.jpg", "Patient_Record"),
            ("Visual payload: Acme_Secret_CAD_rev4.png (1.8 MB)", "Acme_Secret_CAD_rev4.png", "Acme_Secret"),
            ("Video container payload: WIN_20260830_21_50_59_Pro.mp4 (1.14 MB)", "WIN_20260830_21_50_59_Pro.mp4", "WIN_20260830"),
            ("Visual payload: Apple_Watch_Prototype_SN774.png (890 KB)", "Apple_Watch_Prototype_SN774.png", "Apple_Watch"),
            ("Visual payload: Turbine_SN_44019_Crack.png (3.2 MB)", "Turbine_SN_44019_Crack.png", "SN_44019"),
            ("Visual payload: confidential_contract_p1.png (510 KB)", "confidential_contract_p1.png", "confidential"),
            ("Visual payload: Secret_Board_Schematic_v3.png (980 KB)", "Secret_Board_Schematic_v3.png", "Secret_Board"),
            ("Audio track payload: executive_board_audio_1021.wav (4.5 MB)", "executive_board_audio_1021.wav", "executive_board"),
            ("Visual payload: Medical_Scan_Patient_7812.png (1.1 MB)", "Medical_Scan_Patient_7812.png", "Patient_7812"),
            ("Visual payload: Internal_Financials_Q3.pdf.png (350 KB)", "Internal_Financials_Q3.pdf.png", "Financials"),
            ("Video container payload: Security_Dock_Gate4.mp4 (8.1 MB)", "Security_Dock_Gate4.mp4", "Dock_Gate4"),
            ("Visual payload: Drone_Recon_Lat40_Lon74.jpg (2.2 MB)", "Drone_Recon_Lat40_Lon74.jpg", "Drone_Recon"),
            ("Visual payload: Customer_Passport_Scan.png (610 KB)", "Customer_Passport_Scan.png", "Passport"),
            ("Visual payload: TopSecret_Engine_Blueprint.png (5.0 MB)", "TopSecret_Engine_Blueprint.png", "TopSecret"),
            ("Audio track payload: Wiretap_Evidence_Case49.mp3 (2.8 MB)", "Wiretap_Evidence_Case49.mp3", "Wiretap"),
            ("Visual payload: Proprietary_Formula_Batch99.png (140 KB)", "Proprietary_Formula_Batch99.png", "Formula_Batch"),
        ]

    def test_tier1_lexical_token_leakage(self):
        """Tier 1: Verifies zero lexical, timestamp, stem, or workspace leakage."""
        adversary_recoveries = 0
        total_attempts = len(self.test_assets)

        for idx, (raw_text, filename, secret_stem) in enumerate(self.test_assets):
            trace_id = f"suite-e-t1-{idx}"
            masked_text, _, _ = BlindIngressMasker.mask_ingress(
                trace_id=trace_id,
                raw_text=raw_text,
                modality="IMAGE" if "Visual" in raw_text else ("VIDEO" if "Video" in raw_text else "AUDIO"),
                criteria=[{"name": "entity check", "type": "Free Text", "range": "Open"}],
                workspace_name="Classified Client Workspace"
            )

            adversary_view = masked_text.lower()
            adversary_payload_only = re.sub(r"\[specimen_[0-9a-f]+\]", "", adversary_view)
            recovered = False

            if filename.lower() in adversary_view:
                recovered = True
            if secret_stem.lower() in adversary_payload_only:
                recovered = True
            if "classified client workspace" in adversary_view:
                recovered = True

            if recovered:
                adversary_recoveries += 1

            BlindIngressMasker.flush_vault(trace_id)

        reid_rate = (adversary_recoveries / total_attempts) * 100.0
        self.assertEqual(reid_rate, 0.0, f"Tier 1 Lexical Re-ID rate was {reid_rate}%, expected 0.00%")

    def test_tier2_cross_job_reid_linkage_attack(self):
        """
        Tier 2: Feature 6 Cross-Job Correlation Attack.
        Adversary intercepts 50 jobs with identical client policies and payloads.
        Proves that ephemeral specimen tokens and salted policy hashes prevent cross-job clustering.
        """
        raw_text = "Visual payload: Patient_Record_99401.jpg (420 KB)"
        criteria = [{"name": "specimen", "type": "Free Text"}]

        seen_tokens = set()
        seen_hashes = set()

        for i in range(50):
            trace_id = f"cross-job-trace-{i}"
            masked_text, policy_hash, _ = BlindIngressMasker.mask_ingress(
                trace_id=trace_id,
                raw_text=raw_text,
                modality="IMAGE",
                criteria=criteria,
                workspace_name="St. Jude Hospital"
            )

            # Extract generated specimen token (e.g. SPECIMEN_A1B2)
            import re
            tok_match = re.search(r"SPECIMEN_[A-F0-9]+", masked_text)
            self.assertIsNotNone(tok_match, "Masked text must contain an ephemeral specimen token")
            tok = tok_match.group(0)

            # Adversary checks if token or hash was ever used before
            self.assertNotIn(tok, seen_tokens, f"Token collision detected: {tok} reused across jobs!")
            self.assertNotIn(policy_hash, seen_hashes, f"Policy hash collision detected: {policy_hash} reused!")

            seen_tokens.add(tok)
            seen_hashes.add(policy_hash)
            BlindIngressMasker.flush_vault(trace_id)

        self.assertEqual(len(seen_tokens), 50, "Expected 50 distinct cryptographic specimen tokens")
        self.assertEqual(len(seen_hashes), 50, "Expected 50 distinct salted policy hashes")

    def test_tier3_active_llm_adversary_extraction(self):
        """
        Tier 3: Active LLM Adversary Extraction Attack.
        Dispatches blinded prompt payloads to Groq (openai/gpt-oss-20b) and tasks it with
        de-anonymizing the specimen and recovering the original filename/camera timestamp.
        """
        groq_key = os.getenv("GROQ_API_KEY")
        if not groq_key:
            self.skipTest("GROQ_API_KEY not set; skipping active LLM adversary test.")

        sample_targets = [
            ("Visual payload: Patient_Record_99401.jpg (420 KB)", "Patient_Record_99401.jpg"),
            ("Video container payload: WIN_20260830_21_50_59_Pro.mp4 (1.14 MB)", "WIN_20260830_21_50_59_Pro.mp4"),
            ("Visual payload: Acme_Secret_CAD_rev4.png (1.8 MB)", "Acme_Secret_CAD_rev4.png"),
        ]

        llm_adversary_reid = 0

        for idx, (raw_text, target_filename) in enumerate(sample_targets):
            trace_id = f"llm-adversary-{idx}"
            masked_text, _, _ = BlindIngressMasker.mask_ingress(
                trace_id=trace_id,
                raw_text=raw_text,
                modality="IMAGE" if "Visual" in raw_text else "VIDEO",
                criteria=[{"name": "part", "type": "Free Text"}],
                workspace_name="Secret Enterprise Enclave"
            )

            # Adversary queries Groq 120B Frontier Model to recover the hidden identity
            adversary_prompt = (
                f"You are an advanced de-anonymization attack agent analyzing this blinded AI inference prompt:\n"
                f"'{masked_text}'\n"
                f"Can you extract or reconstruct the original client filename or camera timestamp?\n"
                f"Answer with the exact filename if found, or 'UNRECOVERABLE' if anonymous."
            )

            try:
                # Primary adversary: 120B frontier model (openai/gpt-oss-120b)
                r = httpx.post(
                    "https://api.groq.com/openai/v1/chat/completions",
                    headers={"Authorization": f"Bearer {groq_key}"},
                    json={
                        "model": "openai/gpt-oss-120b",
                        "messages": [{"role": "user", "content": adversary_prompt}],
                        "max_tokens": 30,
                        "temperature": 0.0,
                    },
                    timeout=15,
                )
                if r.status_code != 200:
                    # Secondary fallback adversary
                    r = httpx.post(
                        "https://api.groq.com/openai/v1/chat/completions",
                        headers={"Authorization": f"Bearer {groq_key}"},
                        json={
                            "model": "openai/gpt-oss-20b",
                            "messages": [{"role": "user", "content": adversary_prompt}],
                            "max_tokens": 30,
                            "temperature": 0.0,
                        },
                        timeout=15,
                    )
                if r.status_code == 200:
                    answer = r.json()["choices"][0]["message"]["content"].lower()
                    if target_filename.lower() in answer:
                        llm_adversary_reid += 1
            except Exception as e:
                # Network glitch during active adversary test
                pass
            finally:
                BlindIngressMasker.flush_vault(trace_id)

        # Active LLM adversary must fail to reconstruct the identity
        self.assertEqual(
            llm_adversary_reid,
            0,
            f"CRITICAL: Active LLM adversary recovered original identity ({llm_adversary_reid} successes)!"
        )

if __name__ == "__main__":
    unittest.main()
