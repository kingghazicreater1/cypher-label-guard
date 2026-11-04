import asyncio
import os
import sys
sys.path.insert(0, ".")
import json
from dotenv import load_dotenv
load_dotenv()

from features.cat_a_inference.feat_04_subspace_voting.feature import SubspaceDisagreementVotingFeature

async def run():
    feat = SubspaceDisagreementVotingFeature({"id": "feat_04_subspace_voting"})
    criteria = [
        {"name": "product name", "type": "Free Text", "range": "Open item name"},
        {"name": "color", "type": "Free Text", "range": "Open color description"},
        {"name": "quality description", "type": "Free Text", "range": "Physical surface condition"},
    ]
    text = """Visual payload: coffee_pot_and_cookies_set.jpg (115.0 KB) [VISUAL_INSPECTION: Verified Vision Analysis (google/gemini-2.5-flash): {"primary_product": "Coffee and Cookies Set", "objects": ["Coffee Pot", "Coffee Cup", "Cookies", "Serving Board"], "item_colors": "Coffee Pot (Black), Coffee Cup (White with Dark Coffee), Cookies (Brown), Serving Board (Black)"}]"""
    
    results = await feat._evaluate_dynamic_criteria(criteria, text, text)
    print("RESULTS:")
    print(json.dumps(results, indent=2))

asyncio.run(run())
