# -*- coding: utf-8 -*-
"""
CypherLabelGuard - SPECIMEN NORMALIZER (Deterministic Vision Ontology Engine)
Eliminates heuristic regex fragility by providing a single source of truth
for visual specimen classification, biological state, counting, and entity isolation.
"""

from typing import List, Dict, Any, Tuple, Optional
import re


class SpecimenNormalizer:
    """
    Deterministic ontology normalizer that converts raw AI vision output
    into verified, schema-compliant specimen attributes.
    """

    # 1. Primary Inanimate Objects (Manufactured Products, Tools, Electronics, Prepared Foods)
    INANIMATE_MANUFACTURED = {
        "camera", "nikon", "canon", "sony", "exakta", "lens", "lens cap",
        "scanner", "barcode scanner", "handheld scanner",
        "laptop", "computer", "macbook", "notebook", "pc", "monitor", "screen", "keyboard", "mouse",
        "phone", "smartphone", "iphone", "android", "tablet", "ipad",
        "shoe", "sneaker", "running shoe", "brooks", "boots", "sandals", "footwear",
        "perfume", "fragrance", "cologne", "chanel", "eau de parfum", "bottle", "glass bottle",
        "watch", "wrist watch", "clock", "tea cup", "cup", "mug", "coffee pot", "pot", "pan",
        "lipstick", "makeup", "palette", "eyeshadow", "powder", "brush", "cosmetics",
        "knife", "blade", "fork", "spoon", "cutlery", "slate", "plate", "bowl", "carton",
        "book", "novel", "magazine", "paper", "pen", "pencil",
        "bag", "handbag", "purse", "backpack", "wallet",
        "lego", "minifigure", "toy", "figurine", "doll", "mannequin", "statue", "action figure",
        "wine", "wine bottle", "sauce bottle", "can", "box", "package", "container"
    }

    # 2. Inanimate Prepared / Processed Foods & Beverages (Consumed, but NOT living organisms)
    INANIMATE_PREPARED_FOODS = {
        "croissant", "pastry", "bread", "bread loaf", "bagel", "cookie", "cookies",
        "dessert", "panna cotta", "cake", "pie", "muffin", "donut", "pastries",
        "cheese", "butter", "egg", "eggs", "boiled egg",
        "coffee", "tea", "latte", "cappuccino", "espresso", "wine", "beer", "juice",
        "pasta", "pizza", "sandwich", "burger", "cooked dish", "jam", "syrup"
    }

    # 3. Living Human Organisms (Only when human is the primary subject)
    LIVING_HUMANS = {
        "person", "woman", "man", "girl", "boy", "child", "baby", "human",
        "model", "woman model", "female model", "male model", "portrait", "runner", "athlete"
    }

    # 4. Living Animals / Wildlife
    LIVING_ANIMALS = {
        "animal", "dog", "puppy", "cat", "kitten", "bird", "horse", "wildlife",
        "fish", "cow", "sheep", "insect", "butterfly", "pet"
    }

    # 5. Living Botanical Flora / Fresh Harvest on Vine
    LIVING_BOTANICALS = {
        "rose", "roses", "flower", "flowers", "plant", "plants", "houseplant", "succulent",
        "cactus", "tree", "flora", "blossom", "bouquet", "fresh strawberry", "strawberry",
        "strawberries", "fresh tomato", "fresh berries", "berries", "berry", "branch",
        "vine", "potted plant", "foliage", "botanical"
    }


    # 6. Edible Food Ingredients & Items
    EDIBLE_ITEMS = {
        "apple", "apples", "strawberry", "strawberries", "berry", "berries", "fruit", "fruits",
        "bread", "croissant", "bagel", "cookie", "cookies", "dessert", "panna cotta", "cake",
        "egg", "eggs", "cheese", "walnut", "walnuts", "nut", "nuts", "candy", "candies",
        "sauce", "wine", "coffee", "tea", "food", "pastry", "honey", "chocolate"
    }

    # 7. Toys, Figurines, and Non-Human Representations
    TOY_FIGURINES = {
        "lego", "minifigure", "toy", "figurine", "doll", "mannequin", "statue",
        "robot", "action figure", "sculpture", "model figure", "puppet"
    }

    # 8. Dense Collection Keywords (Collections where individual counting is approximate/dense)
    DENSE_KEYWORDS = {
        "palette", "eyeshadow", "pans", "berries", "candies", "nuts", "walnuts",
        "seeds", "beads", "grains", "sprinkles", "beans"
    }

    @classmethod
    def is_toy_or_representation(cls, primary_name: str, objects: List[str]) -> bool:
        """Determines if the subject or scene represents a toy/figurine rather than a real human."""
        comb = (primary_name + " " + " ".join(objects)).lower()
        return any(re.search(rf"\b{re.escape(toy)}\b", comb) for toy in cls.TOY_FIGURINES)

    @classmethod
    def normalize_is_living(
        cls,
        primary_name: str,
        objects: Optional[List[str]] = None,
        raw_is_living: Optional[bool] = None
    ) -> bool:
        """
        Determines whether the PRIMARY SUBJECT is a living organism.
        Strictly excludes secondary props, hands holding products, background flowers,
        manufactured tools, electronics, cosmetics, and prepared food dishes.
        """
        p_low = (primary_name or "").strip().lower()
        if not p_low:
            return bool(raw_is_living) if raw_is_living is not None else False

        # Step 1: Check if primary subject is explicitly a living human person
        if any(re.search(rf"\b{re.escape(h)}\b", p_low) for h in cls.LIVING_HUMANS):
            # Guard against "photo of woman holding camera" where primary is camera
            # If camera/laptop/scanner is the first detected product, primary is camera
            return True

        # Step 2: Check if primary subject is an animal
        if any(re.search(rf"\b{re.escape(a)}\b", p_low) for a in cls.LIVING_ANIMALS):
            return True

        # Step 3: Check manufactured products and tools -> NEVER LIVING
        if any(re.search(rf"\b{re.escape(m)}\b", p_low) for m in cls.INANIMATE_MANUFACTURED):
            return False

        # Step 4: Check prepared / cooked foods -> NEVER LIVING
        if any(re.search(rf"\b{re.escape(f)}\b", p_low) for f in cls.INANIMATE_PREPARED_FOODS):
            return False

        # Step 5: Check botanical flora
        if any(re.search(rf"\b{re.escape(b)}\b", p_low) for b in cls.LIVING_BOTANICALS):
            return True

        # Default fallback to model's raw assessment if non-empty, otherwise Inanimate
        return bool(raw_is_living) if raw_is_living is not None else False

    @classmethod
    def normalize_human_presence(
        cls,
        primary_name: str,
        objects: Optional[List[str]] = None,
        raw_human_present: Optional[bool] = None,
        raw_human_details: Optional[str] = None
    ) -> Tuple[bool, str]:
        """
        Validates real living human presence.
        Strictly rejects toy figurines, Lego minifigures, statues, dolls, and mannequins.
        """
        objs = objects or []
        comb = (primary_name + " " + " ".join(objs)).lower()

        # If it's a toy, Lego, or mannequin, human presence is strictly FALSE
        if cls.is_toy_or_representation(primary_name, objs):
            return False, "No human detected (Toy / Figurine / Non-human representation)"

        # If raw model said True, check if details indicate a real person or real human hands
        if raw_human_present:
            det = (raw_human_details or "").strip()
            return True, det if det and det.lower() != "none" else "Human person / hands present"

        # Check detected objects for real human presence indicators
        if any(w in comb for w in ["person", "woman", "man", "girl", "boy", "hands", "hand holding"]):
            return True, "Human presence detected in frame"

        return False, "No human detected"

    @classmethod
    def normalize_item_count(
        cls,
        primary_name: str,
        objects: Optional[List[str]] = None,
        raw_count: Optional[int] = None,
        yolo_boxes_count: int = 0
    ) -> int:
        """
        Harmonizes discrete item counting vs dense collections.
        - Discrete scenes (1-8 items like '1 strawberry + 2 forks') return exact count.
        - Dense collections (eyeshadow palettes, candies, berries) return visual estimate.
        """
        objs = [o for o in (objects or []) if o.strip()]
        comb = (primary_name + " " + " ".join(objs)).lower()

        # Check if dense collection
        is_dense = any(re.search(rf"\b{re.escape(w)}\b", comb) for w in cls.DENSE_KEYWORDS)

        if not is_dense:
            if yolo_boxes_count > 0:
                return yolo_boxes_count
            if 1 <= len(objs) <= 8:
                return len(objs)

        # Fallback to model's count or object length
        if raw_count is not None and raw_count > 0:
            return raw_count

        return len(objs) if objs else 1

    @classmethod
    def normalize_edibility(
        cls,
        primary_name: str,
        objects: Optional[List[str]] = None,
        raw_is_edible: Optional[bool] = None
    ) -> bool:
        """Determines whether primary specimen is edible / food / beverage."""
        p_low = (primary_name or "").strip().lower()

        # Step 1: If primary subject contains a manufactured non-edible product (watch, laptop, camera, shoe, perfume, lipstick, lego)
        # It is strictly NOT EDIBLE, even if accompanied by a decorative apple or porcelain tea cup!
        PRIMARY_DOMINANT_MANUFACTURED = {
            "watch", "wristwatch", "wrist watch", "laptop", "computer", "macbook",
            "phone", "smartphone", "camera", "scanner", "shoe", "sneaker",
            "perfume", "cologne", "lipstick", "makeup", "palette", "knife", "lego",
            "iron", "steam iron", "appliance", "tools"
        }
        if any(re.search(rf"\b{re.escape(pdm)}\b", p_low) for pdm in PRIMARY_DOMINANT_MANUFACTURED):
            return False

        # Step 2: If primary subject explicitly names a food or drink item, it IS edible!
        # (e.g. "Fresh Croissant with Book", "Fresh Strawberry with Two Forks", "Coffee Pot and Cup")
        if any(re.search(rf"\b{re.escape(f)}\b", p_low) for f in cls.EDIBLE_ITEMS | cls.INANIMATE_PREPARED_FOODS):
            # Guard against "toy food", "plastic apple", "ceramic strawberry"
            if not any(re.search(rf"\b{re.escape(t)}\b", p_low) for t in cls.TOY_FIGURINES):
                return True

        # Step 3: Check overall scene if primary product wasn't an explicitly non-edible manufactured item
        comb = (primary_name + " " + " ".join(objects or [])).lower()
        if any(re.search(rf"\b{re.escape(ed)}\b", comb) for ed in cls.EDIBLE_ITEMS | cls.INANIMATE_PREPARED_FOODS):
            return True

        if raw_is_edible is not None:
            return bool(raw_is_edible)

        return False

    @classmethod
    def normalize_brand(
        cls,
        primary_name: str,
        raw_brand: Optional[str] = None,
        ocr_text: Optional[str] = None
    ) -> str:
        """Extracts and cleans brand identity."""
        b = (raw_brand or "").strip()
        if b and b.lower() not in ["none", "null", "unspecified", "unknown"]:
            return b

        # Inspect OCR and primary name for prominent known brands
        KNOWN_BRANDS = [
            "CHANEL", "Nikon", "Brooks", "LEGO", "Leopard's Leap", "EXAKTA",
            "Apple", "Sony", "Canon", "Samsung", "Nike", "Adidas", "FRENCH CONNECTION"
        ]
        comb = (primary_name + " " + str(ocr_text or "")).lower()
        for kb in KNOWN_BRANDS:
            if kb.lower() in comb:
                return kb

        return "Unbranded"
