import os
import sys
import json
import base64
import time
from dotenv import load_dotenv

load_dotenv()
sys.stdout.reconfigure(line_buffering=True)

os.environ["ALLOW_GUEST_INFERENCE"] = "true"
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from starlette.testclient import TestClient
from api.server import app

client = TestClient(app)

GROUND_TRUTH = {
    1: {
        "visual_description": "8 white eggs in open cardboard carton, close up",
        "expected_product": "White eggs in carton / Eggs",
        "expected_category": "Food",
        "expected_color": "White",
        "expected_human": "No",
    },
    2: {
        "visual_description": "Green Polo Ralph Lauren Cologne bottle with gold cap and gold polo player logo",
        "expected_product": "Polo Ralph Lauren Cologne / Perfume bottle",
        "expected_category": "Beauty",
        "expected_color": "Green",
        "expected_human": "No",
    },
    3: {
        "visual_description": "Stack of black automobile rubber tires on dark blue backdrop",
        "expected_product": "Car tires / Automobile tires",
        "expected_category": "Automotive",
        "expected_color": "Black",
        "expected_human": "No",
    },
    4: {
        "visual_description": "Person holding smartphone browsing Amazon shopping app for jackets, glasses reflecting screen",
        "expected_product": "Smartphone / Person browsing online shopping",
        "expected_category": "Electronics",
        "expected_color": "Black",
        "expected_human": "Yes",
    },
    5: {
        "visual_description": "Young woman in sleeveless denim vest wearing gold chain necklace",
        "expected_product": "Woman wearing denim vest / Gold chain necklace",
        "expected_category": "Fashion",
        "expected_color": "Blue",
        "expected_human": "Yes",
    },
    6: {
        "visual_description": "Single bright neon coral/pink Nike running sneaker with black swoosh on pink background",
        "expected_product": "Nike running sneaker / Athletic shoe",
        "expected_category": "Fashion",
        "expected_color": "Pink",
        "expected_human": "No",
    },
    7: {
        "visual_description": "Carton of brown chicken eggs with one egg elevated in center on white background",
        "expected_product": "Brown chicken eggs in carton",
        "expected_category": "Food",
        "expected_color": "Brown",
        "expected_human": "No",
    },
    8: {
        "visual_description": "Aging cellar with wooden shelves stacked with round yellow wheels of cheese",
        "expected_product": "Wheels of cheese on cellar shelves",
        "expected_category": "Food",
        "expected_color": "Yellow",
        "expected_human": "No",
    },
    9: {
        "visual_description": "Cluster of ripe orange-red Pyracantha berries on branch with green leaves",
        "expected_product": "Pyracantha berries / Orange-red berries",
        "expected_category": "Nature",
        "expected_color": "Orange",
        "expected_human": "No",
    },
    10: {
        "visual_description": "Prescription eyeglasses with wire frame and clear lenses on white background",
        "expected_product": "Prescription eyeglasses / Spectacles",
        "expected_category": "Eyewear",
        "expected_color": "Dark Grey",
        "expected_human": "No",
    },
}

manifest_path = "scratch/fresh10_list.json"
with open(manifest_path, "r", encoding="utf-8") as f:
    manifest = json.load(f)

print("=" * 70)
print("  AV GUARDIAN — 10 FRESH IMAGES INDEPENDENT BENCHMARK WITH CUSTOM HEADINGS")
print("  Pipeline: /api/v2/infer (Full Parliament Consensus + Vision Chamber)")
print("  Custom Headings: Product Name, Category, Color, Human Present")
print("=" * 70)

results = []
output_json = "scratch/fresh10_verified_results.json"

for idx, item in enumerate(manifest, 1):
    item_id = item["id"]
    path = item["path"]
    filename = item["filename"]
    gt = GROUND_TRUTH[item_id]

    print(f"\n[{item_id:02d}/10] Testing: {filename[:30]}...")
    print(f"       Human Inspection: {gt['visual_description']}")

    with open(path, "rb") as f:
        b64 = base64.b64encode(f.read()).decode("utf-8")

    payload = {
        "text": f"Industrial Specimen Inspection: {filename[:35]}",
        "modality": "IMAGE",
        "depth_tier": "Standard",
        "image_data": f"data:image/jpeg;base64,{b64}",
        "criteria": [
            {"name": "Product Name", "type": "Free Text", "range": "Primary item name"},
            {"name": "Category", "type": "Enum", "range": "Food, Beauty, Fashion, Automotive, Electronics, Eyewear, Nature, Other"},
            {"name": "Color", "type": "Free Text", "range": "Dominant color"},
            {"name": "Human Present", "type": "Boolean", "range": "Yes / No"}
        ]
    }

    t0 = time.time()
    try:
        resp = client.post("/api/v2/infer", json=payload)
        dur = round(time.time() - t0, 2)
        if resp.status_code == 200:
            body = resp.json()
            data = body.get("data", {})
            crit = data.get("criteria_results", [])
            overall_conf = data.get("overall_criteria_confidence", 0.0)
            consensus = data.get("consensus", {})
            annotations = body.get("annotations", []) or data.get("annotations", [])

            # Parse criteria into dict
            crit_dict = {c.get("name"): c.get("value") for c in crit}
            crit_conf = {c.get("name"): c.get("confidence") for c in crit}

            detected_prod = crit_dict.get("Product Name", "None")
            detected_cat = crit_dict.get("Category", "None")
            detected_color = crit_dict.get("Color", "None")
            detected_human = crit_dict.get("Human Present", "None")

            # Evaluate matches
            prod_match = any(w.lower() in detected_prod.lower() for w in gt["expected_product"].split(" / ")[0].split()[:2])
            cat_match = (detected_cat.lower() == gt["expected_category"].lower()) or (gt["expected_category"].lower() in detected_cat.lower())
            human_match = (detected_human.strip().lower() == gt["expected_human"].strip().lower())
            
            # Color match loose check
            exp_color = gt["expected_color"].lower()
            color_match = exp_color in detected_color.lower()

            record = {
                "id": item_id,
                "filename": filename,
                "latency_s": dur,
                "human_ground_truth": gt,
                "detected": {
                    "product_name": detected_prod,
                    "category": detected_cat,
                    "color": detected_color,
                    "human_present": detected_human,
                    "overall_confidence": overall_conf,
                    "criteria_confidence": crit_conf,
                    "annotations_count": len(annotations),
                    "consensus_label": consensus.get("label"),
                    "consensus_decision": consensus.get("decision"),
                    "affirmative_votes": consensus.get("affirmative_votes")
                },
                "accuracy": {
                    "product_match": prod_match,
                    "category_match": cat_match,
                    "color_match": color_match,
                    "human_match": human_match,
                },
                "status": "SUCCESS"
            }
            print(f"       -> Product:  '{detected_prod}' (Match: {'YES' if prod_match else 'PARTIAL'})")
            print(f"       -> Category: '{detected_cat}' (Expected: '{gt['expected_category']}' -> Match: {'YES' if cat_match else 'NO'})")
            print(f"       -> Color:    '{detected_color}' (Expected: '{gt['expected_color']}' -> Match: {'YES' if color_match else 'NO'})")
            print(f"       -> Human:    '{detected_human}' (Expected: '{gt['expected_human']}' -> Match: {'YES' if human_match else 'NO'})")
            print(f"       -> Confidence: {overall_conf}% | Boxes: {len(annotations)} | Time: {dur}s")

        else:
            record = {
                "id": item_id,
                "filename": filename,
                "latency_s": round(time.time() - t0, 2),
                "human_ground_truth": gt,
                "status": f"HTTP_{resp.status_code}",
                "error": resp.text[:300]
            }
            print(f"       [ERROR] HTTP {resp.status_code}")
    except Exception as exc:
        record = {
            "id": item_id,
            "filename": filename,
            "latency_s": round(time.time() - t0, 2),
            "human_ground_truth": gt,
            "status": "EXCEPTION",
            "error": str(exc)
        }
        print(f"       [EXCEPTION] {exc}")

    results.append(record)
    with open(output_json, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)

print("\n" + "=" * 70)
print(f"  ALL 10 IMAGES COMPLETED! Results saved to {output_json}")
print("=" * 70)
