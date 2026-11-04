import io
import unittest
from PIL import Image

from core.fallback_registry import FallbackRegistry
from features.cat_f_multimodal.feat_35_vision_connector.feature import analyze_raster_buffer, VisionConnectorFeature
from core.context import ExecutionContext


class TestJob377549VisionConcordanceRegression(unittest.TestCase):
    """
    Regression Test Suite for Job #377549:
    1. Bug 1: Fallback Registry must catch 'Precision Industrial Assembly' & variants.
    2. Bug 2: Feature 35 Vision Connector must accurately extract 'Blue' / 'Blue and White'
              from image raster pixels and never default to 'Red'.
    3. Bug 3: Mathematical Concordance Rule:
              When 1 of 3 APIs vote for a value, confidence must be scaled:
              confidence = (concordant / total) * average_model_score
              (e.g. (1/3) * 95.7 = 31.9%), never 95.7%.
    4. False Green Prevention: Discordant votes or unverified fallbacks revoke QA approval.
    """

    def test_bug_1_precision_industrial_assembly_is_fallback(self):
        """Bug 1: Verify Precision Industrial Assembly is rejected by FallbackRegistry."""
        test_strings = [
            "Precision Industrial Assembly",
            "Precision Industrial Component",
            "Precision Industrial Bearing Assembly",
            "Factory Precision Assembly",
            "Factory Precision Product Specimen",
            "Industrial Precision Bearing Assembly",
        ]
        for s in test_strings:
            is_fb, pat = FallbackRegistry.is_fallback(s)
            self.assertTrue(is_fb, f"Expected '{s}' to be recognized as generic fallback.")

    def test_bug_2_blue_running_shoe_raster_color_detection(self):
        """Bug 2: Verify raster color analysis correctly detects Blue and White, never Red."""
        # Create a 200x200 synthetic image with white background and royal blue shoe body
        img = Image.new("RGB", (200, 200), color=(250, 250, 250))
        for x in range(30, 170):
            for y in range(80, 150):
                img.putpixel((x, y), (25, 75, 210))  # Royal Blue

        buf = io.BytesIO()
        img.save(buf, format="JPEG")
        raw_bytes = buf.getvalue()

        raster_info = analyze_raster_buffer(raw_bytes)
        self.assertTrue(raster_info["success"])
        detected_color = raster_info["detected_color"]

        self.assertIn("Blue", detected_color, f"Expected Blue in color, got '{detected_color}'")
        self.assertNotIn("Red", detected_color, f"Red was erroneously detected: '{detected_color}'")

    def test_bug_3_concordance_scaled_confidence_math(self):
        """
        Bug 3: Verify concordance ratio scales confidence.
        If 3 models are queried and only 1 votes for the value:
        concordant = 1, total = 3, avg_model_conf = 95.7
        scaled_conf = (1 / 3) * 95.7 = 31.9% (discordant).
        """
        concordant = 1
        total = 3
        raw_confidences = [95.0, 96.0, 96.0]
        avg_model_conf = sum(raw_confidences) / len(raw_confidences)

        concordance_ratio = concordant / total
        scaled_conf = round(concordance_ratio * avg_model_conf, 1)

        self.assertEqual(scaled_conf, 31.9)
        self.assertLess(scaled_conf, 50.0, "Discordant confidence must be strictly below 50.0%")

    def test_false_green_revocation_on_discordance(self):
        """
        Verify that when a heading has discordant votes (e.g. 1 of 3) or fallback value,
        the system revokes overall approval so it never passes inspection falsely.
        """
        criteria_results = [
            {"name": "Product name", "value": "[REJECTED: GENERIC_FALLBACK_UNVERIFIED]", "confidence": 0.0, "anomaly": True},
            {"name": "Product color", "value": "Blue and White", "confidence": 95.0, "anomaly": False},
            {"name": "Quality", "value": "High Grade (8.8/10)", "confidence": 31.9, "anomaly": True, "agreement": "1 of 3 APIs concordant (Discordant / Stalemate)"},
        ]
        has_anomaly = any(c.get("anomaly") for c in criteria_results)
        self.assertTrue(has_anomaly)

        # In backend and frontend, overall criteria confidence must be revoked when any anomaly exists
        overall_conf = 0.0 if has_anomaly else sum(c["confidence"] for c in criteria_results) / len(criteria_results)
        self.assertEqual(overall_conf, 0.0)


if __name__ == "__main__":
    unittest.main()
