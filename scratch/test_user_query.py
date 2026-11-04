import asyncio, os, sys
sys.path.insert(0, ".")
from dotenv import load_dotenv
load_dotenv()
from core.registry import FeatureRegistry

async def test_user_query():
    reg = FeatureRegistry()
    reg.discover_features()
    reg.load_all_features()
    feat = reg.get_feature('feat_04_subspace_voting')
    
    text = "a donkey reading books"
    criteria = [
        {"name": "animal in sentence", "type": "Free Text", "range": ""},
        {"name": "type of sentence", "type": "Free Text", "range": ""},
        {"name": "what donkey is reading", "type": "Free Text", "range": ""},
    ]
    
    results = await feat._evaluate_dynamic_criteria(criteria, text, text, {})
    print("\n=== LIVE PARLIAMENT CRITERIA RESULTS ===")
    for r in results:
        name = r['name']
        val = r['value']
        conf = r['confidence']
        agree = r['agreement']
        print(f"{name:<26} -> {val:<20} (Conf: {conf}%, Agree: {agree})")
        print(f"   Votes: {r['votes']}")

if __name__ == "__main__":
    asyncio.run(test_user_query())
