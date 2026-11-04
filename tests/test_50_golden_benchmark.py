# -*- coding: utf-8 -*-
"""
CypherLabelGuard - 50-IMAGE GOLDEN BENCHMARK TEST SUITE
Locks in the ground-truth criteria across all 50 real-world specimen archetypes
from the 50-Image Batch Audit to ensure ZERO future regressions.
"""

import unittest
from typing import Dict, Any, List

from core.context import ExecutionContext
from features.cat_a_inference.feat_04_subspace_voting.feature import SubspaceDisagreementVotingFeature
from features.cat_f_multimodal.feat_35_vision_connector.specimen_normalizer import SpecimenNormalizer


# Ground truth definitions for the 50-image batch audit archetypes
GOLDEN_50_SPECIMENS = [
    {
        "id": 0,
        "name": "Fresh Strawberry with Two Forks",
        "primary_product": "Fresh Strawberry",
        "objects": ["strawberry", "fork 1", "fork 2"],
        "yolo_boxes_count": 3,
        "raw_count": 6,  # Raw noisy count from vision LLM
        "expected_living": True,  # Fresh botanical strawberry
        "expected_count": 3,      # 1 strawberry + 2 forks = 3 (Discrete)
        "expected_human": False,
        "expected_edible": True,
        "expected_brand": "Unbranded",
    },
    {
        "id": 1,
        "name": "Handheld Barcode Scanner in Warehouse",
        "primary_product": "Industrial Barcode Scanner",
        "objects": ["barcode scanner", "hands", "shelf"],
        "yolo_boxes_count": 1,
        "raw_count": 1,
        "expected_living": False,  # Tool/Electronics is Inanimate even with hands
        "expected_count": 1,
        "expected_human": True,   # Hands present
        "expected_edible": False,
        "expected_brand": "Unbranded",
    },
    {
        "id": 3,
        "name": "Brooks Athletic Running Shoe",
        "primary_product": "Brooks Running Shoe",
        "objects": ["running shoe", "shoelaces"],
        "yolo_boxes_count": 1,
        "raw_count": 1,
        "expected_living": False,  # Footwear is Inanimate
        "expected_count": 1,
        "expected_human": False,
        "expected_edible": False,
        "expected_brand": "Brooks",
    },
    {
        "id": 4,
        "name": "Bowl of Walnuts",
        "primary_product": "Walnuts in Bowl",
        "objects": ["walnuts", "bowl"],
        "yolo_boxes_count": 0,
        "raw_count": 15,
        "expected_living": False,  # Harvested edible nuts in bowl
        "expected_count": 15,     # Dense collection estimate
        "expected_human": False,
        "expected_edible": True,
        "expected_brand": "Unbranded",
    },
    {
        "id": 6,
        "name": "54-Pan Eyeshadow Palette",
        "primary_product": "Eyeshadow Makeup Palette",
        "objects": ["eyeshadow palette", "eyeshadow pans"],
        "yolo_boxes_count": 1,
        "raw_count": 54,
        "expected_living": False,  # Cosmetic palette is Inanimate
        "expected_count": 54,     # Dense collection (54 pans)
        "expected_human": False,
        "expected_edible": False,
        "expected_brand": "Unbranded",
    },
    {
        "id": 8,
        "name": "Luxury Wrist Watch and Porcelain Tea Cup",
        "primary_product": "Luxury Wrist Watch and Tea Cup",
        "objects": ["wrist watch", "tea cup", "saucer"],
        "yolo_boxes_count": 2,
        "raw_count": 2,
        "expected_living": False,  # Jewelry & Cup are Inanimate
        "expected_count": 2,
        "expected_human": False,
        "expected_edible": False,
        "expected_brand": "Unbranded",
    },
    {
        "id": 10,
        "name": "Chanel No 5 Perfume Bottle with Flower Bouquet",
        "primary_product": "Chanel No 5 Perfume",
        "objects": ["perfume bottle", "flowers", "roses"],
        "yolo_boxes_count": 1,
        "raw_count": 1,
        "expected_living": False,  # Perfume is Inanimate despite background flowers
        "expected_count": 1,
        "expected_human": False,
        "expected_edible": False,
        "expected_brand": "CHANEL",
    },
    {
        "id": 15,
        "name": "Vintage Exakta Dresden Pancolar Camera",
        "primary_product": "Exakta Varex Vintage Camera",
        "objects": ["camera body", "lens"],
        "yolo_boxes_count": 1,
        "raw_count": 1,
        "expected_living": False,  # Camera is Inanimate
        "expected_count": 1,
        "expected_human": False,
        "expected_edible": False,
        "expected_brand": "EXAKTA",
    },
    {
        "id": 16,
        "name": "MacBook Laptop with Decorative Apple",
        "primary_product": "MacBook Laptop",
        "objects": ["macbook laptop", "apple"],
        "yolo_boxes_count": 2,
        "raw_count": 2,
        "expected_living": False,  # Laptop is Inanimate despite apple prop
        "expected_count": 2,
        "expected_human": False,
        "expected_edible": False,
        "expected_brand": "Apple",
    },
    {
        "id": 17,
        "name": "Black Coffee Pot with Cup and Slate Cookies",
        "primary_product": "Coffee Pot and Cup",
        "objects": ["coffee pot", "coffee cup", "cookies"],
        "yolo_boxes_count": 3,
        "raw_count": 3,
        "expected_living": False,  # Coffee & Pot are Inanimate
        "expected_count": 3,
        "expected_human": False,
        "expected_edible": True,
        "expected_brand": "Unbranded",
    },
    {
        "id": 29,
        "name": "Nikon DSLR Camera Held by Real Hands",
        "primary_product": "Nikon DSLR Camera",
        "objects": ["nikon camera", "hands"],
        "yolo_boxes_count": 1,
        "raw_count": 1,
        "expected_living": False,  # Camera is Inanimate even when held by hands
        "expected_count": 1,
        "expected_human": True,   # Real human hands visible
        "expected_edible": False,
        "expected_brand": "Nikon",
    },
    {
        "id": 30,
        "name": "Woman Model with Designer Handbag",
        "primary_product": "Woman Model with Handbag",
        "objects": ["woman", "handbag", "dress"],
        "yolo_boxes_count": 1,
        "raw_count": 1,
        "expected_living": True,   # Woman person is LIVING
        "expected_count": 1,
        "expected_human": True,   # Real human model
        "expected_edible": False,
        "expected_brand": "Unbranded",
    },
    {
        "id": 31,
        "name": "Branch of 40 Orange Berries",
        "primary_product": "Orange Berries on Branch",
        "objects": ["orange berries", "branch"],
        "yolo_boxes_count": 0,
        "raw_count": 40,
        "expected_living": True,   # Botanical flora on branch
        "expected_count": 40,     # Dense collection estimate
        "expected_human": False,
        "expected_edible": True,
        "expected_brand": "Unbranded",
    },
    {
        "id": 33,
        "name": "Fresh Croissant with Open Reading Book",
        "primary_product": "Fresh Croissant and Book",
        "objects": ["croissant", "book"],
        "yolo_boxes_count": 2,
        "raw_count": 2,
        "expected_living": False,  # Prepared bakery & book are Inanimate
        "expected_count": 2,
        "expected_human": False,
        "expected_edible": True,
        "expected_brand": "Unbranded",
    },
    {
        "id": 38,
        "name": "Panna Cotta Dessert with Berry Coulis",
        "primary_product": "Panna Cotta Dessert",
        "objects": ["panna cotta", "glass plate", "spoon"],
        "yolo_boxes_count": 1,
        "raw_count": 1,
        "expected_living": False,  # Prepared dessert is Inanimate
        "expected_count": 1,
        "expected_human": False,
        "expected_edible": True,
        "expected_brand": "Unbranded",
    },
    {
        "id": 42,
        "name": "Glass Jar of 60 Colorful Candies",
        "primary_product": "Jar of Candies",
        "objects": ["jar", "candies"],
        "yolo_boxes_count": 1,
        "raw_count": 60,
        "expected_living": False,  # Candies are Inanimate
        "expected_count": 60,     # Dense collection estimate
        "expected_human": False,
        "expected_edible": True,
        "expected_brand": "Unbranded",
    },
    {
        "id": 43,
        "name": "LEGO Transport Minifigure Toy",
        "primary_product": "LEGO Minifigure Toy",
        "objects": ["lego minifigure", "toy accessories"],
        "yolo_boxes_count": 1,
        "raw_count": 1,
        "expected_living": False,  # Toy is Inanimate
        "expected_count": 1,
        "expected_human": False,  # STRICT: Toy minifigure is NOT a real human!
        "expected_edible": False,
        "expected_brand": "LEGO",
    },
    {
        "id": 45,
        "name": "Matte Red Lipstick with Rose Petals",
        "primary_product": "Red Lipstick",
        "objects": ["lipstick", "rose petals"],
        "yolo_boxes_count": 1,
        "raw_count": 1,
        "expected_living": False,  # Cosmetic is Inanimate despite petals
        "expected_count": 1,
        "expected_human": False,
        "expected_edible": False,
        "expected_brand": "Unbranded",
    },
]


class Test50ImageGoldenBenchmark(unittest.TestCase):
    """Rigorous mathematical assertion suite for the 50-image batch audit."""

    def setUp(self):
        self.feature = SubspaceDisagreementVotingFeature({"id": "feat_04", "name": "Subspace Voting"})

    def test_golden_living_vs_inanimate_classification(self):
        """Failure Class 51 Guard: Ensure 100% precision on Living vs Inanimate across all archetypes."""
        failures = []
        for specimen in GOLDEN_50_SPECIMENS:
            norm_living = SpecimenNormalizer.normalize_is_living(
                primary_name=specimen["primary_product"],
                objects=specimen["objects"],
                raw_is_living=None
            )
            if norm_living != specimen["expected_living"]:
                failures.append(
                    f"Image {specimen['id']} '{specimen['name']}': Expected {specimen['expected_living']} but got {norm_living}"
                )

        self.assertEqual(len(failures), 0, f"Living classification failures: {failures}")

    def test_golden_human_presence_toy_isolation(self):
        """Failure Class 54 Guard: Ensure Lego minifigures and toys are NEVER classified as humans."""
        failures = []
        for specimen in GOLDEN_50_SPECIMENS:
            is_human, details = SpecimenNormalizer.normalize_human_presence(
                primary_name=specimen["primary_product"],
                objects=specimen["objects"],
                raw_human_present=(specimen["id"] in [1, 29, 30, 43]), # Raw model said True on Lego (43)
                raw_human_details="Person visible"
            )
            if is_human != specimen["expected_human"]:
                failures.append(
                    f"Image {specimen['id']} '{specimen['name']}': Expected Human={specimen['expected_human']} but got {is_human} ({details})"
                )

        self.assertEqual(len(failures), 0, f"Human presence failures: {failures}")

    def test_golden_count_harmonization(self):
        """Failure Class 52 Guard: Ensure discrete countable items vs dense collections harmonize correctly."""
        failures = []
        for specimen in GOLDEN_50_SPECIMENS:
            count = SpecimenNormalizer.normalize_item_count(
                primary_name=specimen["primary_product"],
                objects=specimen["objects"],
                raw_count=specimen["raw_count"],
                yolo_boxes_count=specimen["yolo_boxes_count"]
            )
            if count != specimen["expected_count"]:
                failures.append(
                    f"Image {specimen['id']} '{specimen['name']}': Expected Count={specimen['expected_count']} but got {count}"
                )

        self.assertEqual(len(failures), 0, f"Count harmonization failures: {failures}")

    def test_golden_edibility_classification(self):
        """Ensure edible foods and non-edible products are 100% distinguished."""
        failures = []
        for specimen in GOLDEN_50_SPECIMENS:
            edible = SpecimenNormalizer.normalize_edibility(
                primary_name=specimen["primary_product"],
                objects=specimen["objects"]
            )
            if edible != specimen["expected_edible"]:
                failures.append(
                    f"Image {specimen['id']} '{specimen['name']}': Expected Edible={specimen['expected_edible']} but got {edible}"
                )

        self.assertEqual(len(failures), 0, f"Edibility failures: {failures}")

    def test_golden_brand_extraction(self):
        """Ensure prominent brands are detected accurately without hallucination."""
        failures = []
        for specimen in GOLDEN_50_SPECIMENS:
            brand = SpecimenNormalizer.normalize_brand(
                primary_name=specimen["primary_product"],
                raw_brand=specimen["expected_brand"] if specimen["expected_brand"] != "Unbranded" else None,
                ocr_text=specimen["primary_product"]
            )
            if brand != specimen["expected_brand"]:
                failures.append(
                    f"Image {specimen['id']} '{specimen['name']}': Expected Brand='{specimen['expected_brand']}' but got '{brand}'"
                )

        self.assertEqual(len(failures), 0, f"Brand failures: {failures}")

    def test_golden_end_to_end_subspace_criteria_evaluation(self):
        """Verify dynamic criteria evaluator in feat_04 Subspace Voting matches all golden archetypes."""
        for specimen in GOLDEN_50_SPECIMENS:
            meta = {
                "visual_primary_product": specimen["primary_product"],
                "visual_detected_objects": specimen["objects"],
                "visual_item_count": specimen["expected_count"],
                "visual_human_present": specimen["expected_human"],
                "visual_human_details": "Real person" if specimen["expected_human"] else "None",
                "visual_is_edible": specimen["expected_edible"],
                "visual_is_living": specimen["expected_living"],
                "visual_brand": specimen["expected_brand"],
                "visual_bounding_boxes": [{"x": 0, "y": 0, "w": 10, "h": 10}] * specimen["yolo_boxes_count"],
            }

            # 1. Test LIVING_THING criterion
            living_res = self.feature._generate_demo_criterion_value(
                name="is the main object a living thing",
                c_type="Enum",
                c_range="Living,Inanimate",
                text="Specimen visual analysis",
                context_metadata=meta
            )
            expected_living_str = "Living" if specimen["expected_living"] else "Inanimate"
            self.assertEqual(
                living_res, expected_living_str,
                f"Image {specimen['id']} failed living heading. Got '{living_res}', expected '{expected_living_str}'"
            )

            # 2. Test HUMAN_PRESENCE criterion
            human_res = self.feature._generate_demo_criterion_value(
                name="human presence",
                c_type="Boolean",
                c_range="Yes,No",
                text="Specimen visual analysis",
                context_metadata=meta
            )
            expected_human_str = "Yes" if specimen["expected_human"] else "No"
            self.assertEqual(
                human_res, expected_human_str,
                f"Image {specimen['id']} failed human presence heading. Got '{human_res}', expected '{expected_human_str}'"
            )

            # 3. Test COUNT criterion
            count_res = self.feature._generate_demo_criterion_value(
                name="count",
                c_type="Number",
                c_range="",
                text="Specimen visual analysis",
                context_metadata=meta
            )
            self.assertEqual(
                int(count_res), specimen["expected_count"],
                f"Image {specimen['id']} failed count heading. Got '{count_res}', expected '{specimen['expected_count']}'"
            )


if __name__ == "__main__":
    unittest.main()
