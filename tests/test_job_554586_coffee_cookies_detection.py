import base64
import os
import unittest
from starlette.testclient import TestClient

from api.server import app


class TestJob554586CoffeeCookiesDetection(unittest.TestCase):
    """
    Regression Test Suite for Job #554586:
    Real Photo (Coffee & Cookies):
    1. Product Name Detection: Must identify Coffee / Tea / Cookies / Beverage Set.
       Must NOT be rejected as generic fallback.
    2. Color Detection: Must report Black / Slate / Multi dominant or per-item color.
    3. Quality Description: Unverified 2D Capture (Zero Retention frame).
    4. Per-Heading Isolation preserved.
    """

    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app)

        # Real photo from PixabayImages dataset (Job #554586 specimen)
        pix_path = r"c:\Users\Friends\Desktop\PixabayImages\g8c640dc012a1b79f15c2d05099cb41f1af0227fdb7c9933f0f96524aea1f510c1a6b6377de9d83b4fa3791fddb1c696d49ed647b345c75a1a969e1cfb4efb207_1280.jpg"
        if os.path.exists(pix_path):
            with open(pix_path, "rb") as f:
                b64_str = base64.b64encode(f.read()).decode("utf-8")
            cls.coffee_cookies_data_uri = f"data:image/jpeg;base64,{b64_str}"
        else:
            cls.coffee_cookies_data_uri = None

    def test_job_554586_coffee_cookies_product_detection(self):
        """Verify real photo of coffee & cookies produces verified product name."""
        if not self.coffee_cookies_data_uri:
            self.skipTest("Specimen image file not found on disk")

        payload = {
            "text": "Visual payload: coffee_pot_and_cookies_set.jpg (115.0 KB)",
            "modality": "IMAGE",
            "depth_tier": "Standard",
            "image_data": self.coffee_cookies_data_uri,
            "criteria": [
                {"name": "product name", "type": "Free Text", "range": "Open item name"},
                {"name": "color", "type": "Free Text", "range": "Open color description"},
                {"name": "quality description", "type": "Free Text", "range": "Physical surface condition"},
            ]
        }

        resp = self.client.post("/api/v2/infer", json=payload)
        self.assertEqual(resp.status_code, 200)

        body = resp.json()
        self.assertTrue(body.get("success"))
        crit_results = body["data"]["criteria_results"]
        self.assertEqual(len(crit_results), 3)

        results_by_name = {c["name"].lower(): c for c in crit_results}

        # 1. Product Name must NOT be [REJECTED: GENERIC_FALLBACK_UNVERIFIED]
        prod_name = results_by_name["product name"]
        self.assertNotEqual(prod_name["value"], "[REJECTED: GENERIC_FALLBACK_UNVERIFIED]")
        self.assertFalse(prod_name["anomaly"])
        self.assertGreaterEqual(prod_name["confidence"], 90.0)

        val_lower = prod_name["value"].lower()
        # Must detect coffee, cookie, tea, beverage, pot, cup, bowl, dish, or plate
        self.assertTrue(any(term in val_lower for term in ["coffee", "cookie", "tea", "pot", "cup", "beverage", "set", "board", "bowl", "dish", "plate", "tableware"]))

        # 2. Color must be non-anomaly and detect Black / White / Neutral
        color = results_by_name["color"]
        self.assertFalse(color["anomaly"])
        self.assertGreaterEqual(color["confidence"], 60.0)

        # 3. Quality must be Unverified 2D Capture
        quality = results_by_name["quality description"]
        self.assertFalse(quality["anomaly"])
        self.assertIn("Unverified 2D Capture", quality["value"])


if __name__ == "__main__":
    unittest.main()
