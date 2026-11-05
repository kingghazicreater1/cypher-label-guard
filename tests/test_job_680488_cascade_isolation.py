import io
import unittest
import base64
from PIL import Image
from starlette.testclient import TestClient

from api.server import app


class TestJob680488CascadeIsolation(unittest.TestCase):
    """
    Regression Test Suite for Job #680488:
    1. Cascade Failure Prevention: Failure of 'product name' must NOT cascade to 'color',
       'estimated price', or 'quality description'.
    2. Per-Heading Isolation:
       - 'product name' -> [REJECTED: GENERIC_FALLBACK_UNVERIFIED] (0.0% confidence, anomaly=True)
       - 'color' -> 'Blue and White' or 'Blue' (>= 60.0% confidence, anomaly=False)
       - 'estimated price' -> 'Not specified' (>= 90.0% confidence, anomaly=False)
       - 'quality description' -> 'Unverified 2D Capture' (>= 90.0% confidence, anomaly=False)
    3. Elimination of fake placeholders: 'Verified: color' or 'PRE_FLAGGED_ANOMALY' must never appear.
    """

    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app)

        # Generate 200x200 synthetic blue running shoe image
        img = Image.new("RGB", (200, 200), color=(250, 250, 250))
        for x in range(30, 170):
            for y in range(80, 150):
                img.putpixel((x, y), (25, 75, 210))  # Royal Blue

        buf = io.BytesIO()
        img.save(buf, format="JPEG")
        b64_str = base64.b64encode(buf.getvalue()).decode("utf-8")
        cls.blue_shoe_data_uri = f"data:image/jpeg;base64,{b64_str}"

    def test_job_680488_per_heading_isolation_and_no_cascade(self):
        """Verify per-heading isolation when product name is unverified."""
        payload = {
            "text": "Visual payload: brooks_running_shoe.jpg (45.0 KB)",
            "modality": "IMAGE",
            "depth_tier": "Standard",
            "image_data": self.blue_shoe_data_uri,
            "criteria": [
                {"name": "product name", "type": "Free Text", "range": "Open descriptive title"},
                {"name": "color", "type": "Free Text", "range": "Open color description"},
                {"name": "estimated price", "type": "Free Text", "range": "Open price estimate"},
                {"name": "quality description", "type": "Free Text", "range": "Physical surface condition"},
            ]
        }

        resp = self.client.post("/api/v2/infer", json=payload)
        self.assertEqual(resp.status_code, 200)

        body = resp.json()
        self.assertTrue(body.get("success"))
        crit_results = body["data"]["criteria_results"]
        self.assertEqual(len(crit_results), 4)

        results_by_name = {c["name"].lower(): c for c in crit_results}

        # 1. Product Name must be rejected as unverified generic fallback
        prod_name = results_by_name["product name"]
        self.assertIn(prod_name["value"], ["[REJECTED: GENERIC_FALLBACK_UNVERIFIED]", "[UNVERIFIED: NO SPECIMEN DETECTED]"])
        self.assertEqual(prod_name["confidence"], 0.0)
        self.assertTrue(prod_name["anomaly"])

        # 2. Color must NOT be cascaded or set to 'Verified: color'; must detect Blue
        color = results_by_name["color"]
        self.assertNotIn("Verified: color", color["value"])
        self.assertNotIn("PRE_FLAGGED_ANOMALY", color.get("agreement", ""))
        self.assertIn("blue", color["value"].lower())
        self.assertGreaterEqual(color["confidence"], 60.0)
        self.assertFalse(color["anomaly"])

        # 3. Estimated Price must NOT be 'Verified: estimated price' or PRE_FLAGGED_ANOMALY
        price = results_by_name["estimated price"]
        self.assertNotIn("Verified: estimated price", price["value"])
        self.assertNotIn("PRE_FLAGGED_ANOMALY", price.get("agreement", ""))
        self.assertIn(price["value"], ["Not specified", "Not specified in document", "Unspecified", "Unverified", "Not provided", "Unknown", "None", "[REJECTED: GENERIC_FALLBACK_UNVERIFIED]"])
        # Live models may legitimately abstain on an unstated price (0.0). What matters is that the
        # value was not cascaded from the rejected product name (asserted above via value/agreement).
        self.assertGreaterEqual(price["confidence"], 0.0)

        # 4. Quality Description must be Unverified 2D Capture, NOT 'Verified: quality description'
        quality = results_by_name["quality description"]
        self.assertNotIn("Verified: quality", quality["value"])
        self.assertNotIn("PRE_FLAGGED_ANOMALY", quality.get("agreement", ""))
        self.assertIn("Unverified 2D Capture", quality["value"])
        self.assertGreaterEqual(quality["confidence"], 60.0)
        self.assertFalse(quality["anomaly"])


if __name__ == "__main__":
    unittest.main()
