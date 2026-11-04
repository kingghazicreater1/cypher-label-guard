import unittest
from features.cat_a_inference.feat_04_subspace_voting.feature import SubspaceDisagreementVotingFeature

class TestBatchAuditFixes(unittest.TestCase):
    def setUp(self):
        self.feat = SubspaceDisagreementVotingFeature({"id": "feat_04", "name": "Subspace Voting"})

    def test_heading_intent_routing(self):
        # Bug 1 & 3: Background material/surface was matching HUMAN_PRESENCE because of 'face' in 'surface'
        self.assertEqual(
            self.feat.classify_heading_intent("what is the dominant background material or surface?"),
            "BACKGROUND"
        )
        self.assertEqual(
            self.feat.classify_heading_intent("background surface"),
            "BACKGROUND"
        )
        self.assertEqual(
            self.feat.classify_heading_intent("is human present or human hands?"),
            "HUMAN_PRESENCE"
        )

        # Bug 1: Objects list + colors was matching generic COLOR
        self.assertEqual(
            self.feat.classify_heading_intent("detailed list of every single object and its exact color"),
            "PER_ITEM_COLORS"
        )

        # Bug 2: Living thing was dropping into GENERAL and returning "Verified Specimen Attribute"
        self.assertEqual(
            self.feat.classify_heading_intent("is the main object a living thing"),
            "LIVING_THING"
        )
        self.assertEqual(
            self.feat.classify_heading_intent("is it living or inanimate?"),
            "LIVING_THING"
        )

        # Bug 2: Visible damage was dropping into GENERAL and returning "Verified Specimen Attribute"
        self.assertEqual(
            self.feat.classify_heading_intent("describe any visible damage"),
            "DAMAGE_DEFECT"
        )
        self.assertEqual(
            self.feat.classify_heading_intent("any visible damage, crack or flaw"),
            "DAMAGE_DEFECT"
        )

        # Real photo vs CGI
        self.assertEqual(
            self.feat.classify_heading_intent("is this a real product photo or synthetic/cgi?"),
            "REAL_OR_SYNTHETIC"
        )

    def test_no_verified_specimen_attribute_placeholder(self):
        # Test living thing for roses (flowers) -> Living
        val_rose = self.feat._generate_demo_criterion_value(
            name="is the main object a living thing",
            c_type="Enum",
            c_range="Living, Inanimate",
            text="rose flowers in garden",
            context_metadata={
                "visual_primary_product": "Roses",
                "visual_detected_objects": ["roses", "flower stems"],
                "visual_background": "Dark garden background"
            }
        )
        self.assertEqual(val_rose, "Living")
        self.assertNotEqual(val_rose, "Verified Specimen Attribute")

        # Test living thing for wine bottle -> Inanimate
        val_wine = self.feat._generate_demo_criterion_value(
            name="is the main object a living thing",
            c_type="Enum",
            c_range="Living, Inanimate",
            text="wine bottle on table",
            context_metadata={
                "visual_primary_product": "Wine Bottle",
                "visual_detected_objects": ["wine bottle", "wine glass"],
                "visual_background": "Vineyard landscape"
            }
        )
        self.assertEqual(val_wine, "Inanimate")
        self.assertNotEqual(val_wine, "Verified Specimen Attribute")

        # Test background never returns "No human detected"
        val_bg = self.feat._generate_demo_criterion_value(
            name="what is the dominant background material or surface?",
            c_type="Free Text",
            c_range="",
            text="wine bottles",
            context_metadata={
                "visual_background": "Vineyard landscape",
                "visual_human_present": False,
            }
        )
        self.assertEqual(val_bg, "Vineyard landscape")
        self.assertNotIn("human", val_bg.lower())

        # Test damage never returns "Verified Specimen Attribute"
        val_damage = self.feat._generate_demo_criterion_value(
            name="describe any visible damage",
            c_type="Free Text",
            c_range="",
            text="clean knife",
            context_metadata={}
        )
        self.assertEqual(val_damage, "No visible damage / Pristine frame")
        self.assertNotEqual(val_damage, "Verified Specimen Attribute")

        # Test unknown heading returns honest "Unverified 2D Capture"
        val_unknown = self.feat._generate_demo_criterion_value(
            name="completely unknown speculative property",
            c_type="Free Text",
            c_range="",
            text="",
            context_metadata={}
        )
        self.assertEqual(val_unknown, "Unverified 2D Capture")
        self.assertNotEqual(val_unknown, "Verified Specimen Attribute")

    def test_batch_report_row_alignment(self):
        from api.batch_images_routes import _rows
        batch_state = {
            "name": "Test Batch",
            "folder_name": "Test Folder",
            "criteria": [
                {"name": "what is the dominant background material or surface?"},
                {"name": "detailed list of every single object and its exact color"},
                {"name": "is the main object a living thing"},
            ],
            "items": [
                {
                    "name": "wine.jpg",
                    "status": "COMPLETED",
                    "decision": "CONFIRMED",
                    "votes": "32/32",
                    "overall_confidence": 95.0,
                    "criteria_results": [
                        # Notice: key has stripped question mark or minor variation from LLM
                        {"name": "what is the dominant background material or surface", "value": "Vineyard landscape", "confidence": 95.0},
                        {"name": "detailed list of every single object and its exact color", "value": "Green wine bottle (Green)", "confidence": 95.0},
                        {"name": "is the main object a living thing", "value": "Inanimate", "confidence": 95.0},
                    ]
                }
            ]
        }
        headers, rows = _rows(batch_state)
        self.assertEqual(len(rows), 1)
        r = rows[0]
        # Verify perfect alignment of values with exact criteria headings
        self.assertEqual(r["what is the dominant background material or surface?"], "Vineyard landscape")
        self.assertEqual(r["what is the dominant background material or surface?_Confidence_%"], 95.0)
        self.assertEqual(r["detailed list of every single object and its exact color"], "Green wine bottle (Green)")
        self.assertEqual(r["is the main object a living thing"], "Inanimate")

    def test_failure_class_51_main_object_living_isolation(self):
        """Failure Class 51: Main object alone dictates living vs inanimate, ignoring props/background."""
        # Laptop with apple in background -> Inanimate
        val_laptop = self.feat._generate_demo_criterion_value(
            name="is the main object a living thing",
            c_type="Enum",
            c_range="Living, Inanimate",
            text="laptop computer on desk with an apple",
            context_metadata={
                "visual_primary_product": "Apple MacBook Laptop",
                "visual_detected_objects": ["laptop", "apple", "keyboard"],
            }
        )
        self.assertEqual(val_laptop, "Inanimate")

        # Hand holding barcode scanner -> Inanimate
        val_scanner = self.feat._generate_demo_criterion_value(
            name="is the main object a living thing",
            c_type="Enum",
            c_range="Living, Inanimate",
            text="operator hand holding barcode scanner",
            context_metadata={
                "visual_primary_product": "Industrial Barcode Scanner",
                "visual_detected_objects": ["barcode scanner", "hand"],
            }
        )
        self.assertEqual(val_scanner, "Inanimate")

        # Perfume with flower bouquet in background -> Inanimate
        val_perfume = self.feat._generate_demo_criterion_value(
            name="is the main object a living thing",
            c_type="Enum",
            c_range="Living, Inanimate",
            text="N°5 Chanel perfume bottle with roses in background",
            context_metadata={
                "visual_primary_product": "Chanel Perfume Bottle",
                "visual_detected_objects": ["perfume bottle", "roses", "flower bouquet"],
            }
        )
        self.assertEqual(val_perfume, "Inanimate")

        # Nikon Camera held by hands -> Inanimate
        val_camera = self.feat._generate_demo_criterion_value(
            name="is the main object a living thing",
            c_type="Enum",
            c_range="Living, Inanimate",
            text="hands holding Nikon DSLR camera",
            context_metadata={
                "visual_primary_product": "Nikon DSLR Camera",
                "visual_detected_objects": ["camera", "hand", "lens"],
            }
        )
        self.assertEqual(val_camera, "Inanimate")

        # Croissant + book -> Inanimate
        val_croissant = self.feat._generate_demo_criterion_value(
            name="is the main object a living thing",
            c_type="Enum",
            c_range="Living, Inanimate",
            text="croissant and book on table",
            context_metadata={
                "visual_primary_product": "Fresh Croissant and Book",
                "visual_detected_objects": ["croissant", "book", "napkin"],
            }
        )
        self.assertEqual(val_croissant, "Inanimate")

        # Panna cotta dessert -> Inanimate
        val_dessert = self.feat._generate_demo_criterion_value(
            name="is the main object a living thing",
            c_type="Enum",
            c_range="Living, Inanimate",
            text="panna cotta dessert on plate",
            context_metadata={
                "visual_primary_product": "Panna Cotta Dessert",
                "visual_detected_objects": ["dessert", "plate", "berries"],
            }
        )
        self.assertEqual(val_dessert, "Inanimate")

        # Red lipstick -> Inanimate
        val_lipstick = self.feat._generate_demo_criterion_value(
            name="is the main object a living thing",
            c_type="Enum",
            c_range="Living, Inanimate",
            text="red lipstick tube with flower decoration",
            context_metadata={
                "visual_primary_product": "Red Lipstick Tube",
                "visual_detected_objects": ["lipstick", "rose petals"],
            }
        )
        self.assertEqual(val_lipstick, "Inanimate")

        # Woman holding bag -> Living (main subject is a person)
        val_woman = self.feat._generate_demo_criterion_value(
            name="is the main object a living thing",
            c_type="Enum",
            c_range="Living, Inanimate",
            text="woman holding handbag",
            context_metadata={
                "visual_primary_product": "Woman Model with Handbag",
                "visual_detected_objects": ["woman", "handbag"],
            }
        )
        self.assertEqual(val_woman, "Living")

        # Fresh strawberry -> Living
        val_strawberry = self.feat._generate_demo_criterion_value(
            name="is the main object a living thing",
            c_type="Enum",
            c_range="Living, Inanimate",
            text="fresh strawberry on stem",
            context_metadata={
                "visual_primary_product": "Fresh Strawberry",
                "visual_detected_objects": ["strawberry", "leaf stem"],
            }
        )
        self.assertEqual(val_strawberry, "Living")

    def test_failure_class_54_lego_toy_not_human(self):
        """Failure Class 54: Lego minifigure or toy figurine must NOT be reported as real human."""
        val_lego = self.feat._generate_demo_criterion_value(
            name="is human present?",
            c_type="Boolean",
            c_range="",
            text="lego astronaut minifigure toy",
            context_metadata={
                "visual_primary_product": "Lego Minifigure Astronaut",
                "visual_detected_objects": ["lego minifigure", "toy", "helmet"],
                "visual_human_present": True,  # YOLO COCO misclassified minifigure as 'person'
            }
        )
        self.assertEqual(val_lego, "No")

    def test_failure_class_52_count_discrete_vs_dense(self):
        """Failure Class 52: Discrete countable items use YOLO/detected count, dense collections use multimodal estimate."""
        # Discrete: Strawberry + 2 forks -> 3 (not 6)
        val_discrete = self.feat._generate_demo_criterion_value(
            name="count of items",
            c_type="Scale",
            c_range="",
            text="strawberry and two forks",
            context_metadata={
                "visual_primary_product": "Fresh Strawberry and Forks",
                "visual_detected_objects": ["strawberry", "fork 1", "fork 2"],
                "visual_item_count": 6,  # LLM over-estimated
                "visual_bounding_boxes": [
                    {"label": "Strawberry"},
                    {"label": "Fork"},
                    {"label": "Fork"},
                ]
            }
        )
        self.assertEqual(val_discrete, "3")

        # Dense: Eyeshadow palette with 54 pans -> 54
        val_dense = self.feat._generate_demo_criterion_value(
            name="count of items",
            c_type="Scale",
            c_range="",
            text="eyeshadow makeup palette with 54 pans",
            context_metadata={
                "visual_primary_product": "Eyeshadow Makeup Palette",
                "visual_detected_objects": ["makeup palette"],
                "visual_item_count": 54,
                "visual_bounding_boxes": [{"label": "Palette"}]
            }
        )
        self.assertEqual(val_dense, "54")

if __name__ == "__main__":
    unittest.main()
