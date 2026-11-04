import asyncio, sys, os
sys.path.insert(0, os.path.abspath("."))
from core.registry import FeatureRegistry

async def run_tests():
    reg = FeatureRegistry()
    reg.discover_features()
    reg.load_all_features()
    feat = reg.get_feature('feat_04_subspace_voting')

    headings = [
        {'name': 'product name', 'type': 'Free Text', 'range': ''},
        {'name': 'edible', 'type': 'Boolean', 'range': ''},
        {'name': 'human presence', 'type': 'Boolean', 'range': ''},
        {'name': 'branded', 'type': 'Enum', 'range': 'Branded, Unbranded'},
        {'name': 'text in image', 'type': 'Free Text', 'range': ''},
        {'name': 'item count', 'type': 'Scale', 'range': ''},
        {'name': 'objects in image', 'type': 'Free Text', 'range': ''},
    ]

    print("=== TEST 1: STRAWBERRY ===")
    meta_straw = {
        'visual_primary_product': 'Fresh Strawberry',
        'visual_detected_objects': ['Fresh Strawberry'],
        'visual_item_count': 1,
        'visual_human_present': False,
        'visual_human_details': 'None',
        'visual_is_edible': True,
        'visual_brand': 'Unbranded',
        'visual_visible_text': 'None',
        'visual_dominant_color': 'Red',
    }
    res_straw = await feat._evaluate_dynamic_criteria(headings, 'Visual payload: Strawberry', '', meta_straw)
    for r in res_straw:
        print(f"  {r['name']}: {r['value']} | Conf: {r['confidence']}% | Anomaly: {r['anomaly']}")

    print("\n=== TEST 2: SMARTPHONE ===")
    meta_phone = {
        'visual_primary_product': 'Smartphone',
        'visual_detected_objects': ['Smartphone'],
        'visual_item_count': 1,
        'visual_human_present': False,
        'visual_human_details': 'None',
        'visual_is_edible': False,
        'visual_brand': 'Unbranded',
        'visual_visible_text': '12:45',
        'visual_dominant_color': 'Black',
    }
    res_phone = await feat._evaluate_dynamic_criteria(headings, 'Visual payload: Smartphone', '', meta_phone)
    for r in res_phone:
        print(f"  {r['name']}: {r['value']} | Conf: {r['confidence']}% | Anomaly: {r['anomaly']}")

    print("\n=== TEST 3: HAND WITH SCANNER (WAREHOUSE SCENE) ===")
    meta_scan = {
        'visual_primary_product': 'warehouse inventory scanning',
        'visual_detected_objects': ['hand', 'glove', 'barcode scanner', 'cardboard boxes', 'pallets'],
        'visual_item_count': 5,
        'visual_human_present': True,
        'visual_human_details': 'Hand wearing glove holding scanner',
        'visual_is_edible': False,
        'visual_brand': 'Zebra Scanner',
        'visual_visible_text': 'BARCODE-9941',
        'visual_dominant_color': 'Brown and Black',
    }
    res_scan = await feat._evaluate_dynamic_criteria(headings, 'Visual payload: Hand with Scanner', '', meta_scan)
    for r in res_scan:
        print(f"  {r['name']}: {r['value']} | Conf: {r['confidence']}% | Anomaly: {r['anomaly']}")

    print("\n=== TEST 4: WATCH AND TEA CUP ===")
    meta_watch = {
        'visual_primary_product': 'Watch and Tea Cup',
        'visual_detected_objects': ['watch', 'tea cup', 'saucer', 'wooden table'],
        'visual_item_count': 4,
        'visual_human_present': False,
        'visual_human_details': 'None',
        'visual_is_edible': False,
        'visual_brand': 'Unbranded',
        'visual_visible_text': 'None',
        'visual_dominant_color': 'Brown',
    }
    res_watch = await feat._evaluate_dynamic_criteria(headings, 'Visual payload: Watch and Tea Cup', '', meta_watch)
    for r in res_watch:
        print(f"  {r['name']}: {r['value']} | Conf: {r['confidence']}% | Anomaly: {r['anomaly']}")

if __name__ == "__main__":
    asyncio.run(run_tests())
