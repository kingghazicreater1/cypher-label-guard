import os
import re
import unittest
from core.fallback_registry import FallbackRegistry

class TestFallbackRegistry(unittest.TestCase):
    """
    Unit test for Centralized Fallback Registry.
    Guarantees:
    1. All known generic descriptors and unverified markers are identified.
    2. Genuine business outputs are never falsely flagged.
    3. Every fallback string in the codebase matches FALLBACK_PATTERNS.
    """

    def test_known_fallback_patterns(self):
        fallbacks = [
            "High-Definition Video Stream Specimen",
            "Temporal Video Stream Specimen",
            "Acoustic Signal Processing Specimen",
            "Industrial Precision Bearing Assembly",
            "Factory Precision Product Specimen",
            "Precision Industrial Assembly",
            "Precision Industrial Component",
            "Factory Precision Assembly",
            "[UNVERIFIED: NO SPECIMEN DETECTED]",
            "[UNVERIFIED: TIMEOUT]",
            "[REJECTED: container signature]",
            "Verified / Pristine",
            "no specimen detected",
            "  high-definition video stream specimen  ",  # casing and whitespace
        ]
        for fb in fallbacks:
            is_fb, pattern = FallbackRegistry.is_fallback(fb)
            self.assertTrue(is_fb, f"Expected '{fb}' to be recognized as fallback, pattern was '{pattern}'")

    def test_genuine_values_not_flagged(self):
        genuine_values = [
            "iPhone 15 Pro Max Titanium Frame",
            "Surface Scratch (depth: 0.12mm) along bevel",
            "Pass - within tolerance 0.05mm",
            "High-carbon steel ball bearing 6204",
            "1080p stream at 60fps nominal",
            "Clear acoustic speech audio with no clipping",
            "Samsung Galaxy S24 Ultra",
        ]
        for val in genuine_values:
            is_fb, pattern = FallbackRegistry.is_fallback(val)
            self.assertFalse(is_fb, f"Legitimate value '{val}' was falsely flagged by pattern '{pattern}'")

    def test_canonical_unverified_constant(self):
        is_fb, _ = FallbackRegistry.is_fallback(FallbackRegistry.CANONICAL_UNVERIFIED_VALUE)
        self.assertTrue(is_fb)
        self.assertIn("UNVERIFIED", FallbackRegistry.CANONICAL_UNVERIFIED_VALUE)

    def test_all_codebase_fallbacks_are_registered(self):
        """
        Static assertion: Scan codebase for any hardcoded specimen/fallback phrases.
        Every fallback string in codebase MUST be covered by FallbackRegistry.
        """
        repo_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        target_dirs = [
            os.path.join(repo_root, "api"),
            os.path.join(repo_root, "core"),
            os.path.join(repo_root, "features"),
        ]

        # Potential fallback indicators that developers might write
        suspicious_regex = re.compile(
            r'["\']([^"\']*(?:Stream Specimen|Precision Bearing|Product Specimen|no specimen detected|\[UNVERIFIED|\[REJECTED)[^"\']*)["\']',
            re.IGNORECASE,
        )

        unregistered_found = []

        for t_dir in target_dirs:
            for root, _, files in os.walk(t_dir):
                for f in files:
                    if not f.endswith(".py") or f == "fallback_registry.py":
                        continue
                    path = os.path.join(root, f)
                    with open(path, "r", encoding="utf-8", errors="ignore") as fp:
                        content = fp.read()
                    matches = suspicious_regex.findall(content)
                    for m in matches:
                        is_fb, _ = FallbackRegistry.is_fallback(m)
                        if not is_fb:
                            unregistered_found.append((path, m))

        self.assertEqual(
            len(unregistered_found),
            0,
            f"Found unregistered fallback strings in codebase: {unregistered_found}. They MUST be added to FallbackRegistry!",
        )

if __name__ == "__main__":
    unittest.main()
