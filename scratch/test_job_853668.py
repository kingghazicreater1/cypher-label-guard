import sys, os, asyncio
from dotenv import load_dotenv
load_dotenv()
sys.path.insert(0, os.path.abspath("."))
from features.cat_a_inference.feat_04_subspace_voting.feature import SubspaceDisagreementVotingFeature

async def run_test():
    engine = SubspaceDisagreementVotingFeature({"id": "feat_04", "name": "Subspace Voting"})
    medical_text = (
        "Patient presents with persistent cough for the past week. "
        "Chest X-ray shows no evidence of pneumonia; ruled out pneumonia. "
        "Patient explicitly denies fever, chills, or shortness of breath."
    )
    criteria = [
        {
            "name": "SYMPTOMS_AND_FINDINGS",
            "type": "Free Text",
            "range": "List symptoms and findings with [CONFIRMED], [RULED_OUT], [NEGATED] tags"
        }
    ]
    res = await engine._evaluate_dynamic_criteria(criteria, medical_text, medical_text)
    print("Results:")
    for r in res:
        print("Name:", r.get("name"))
        print("Value:", r.get("value"))
        print("Confidence:", r.get("confidence"))
        print("Agreement:", r.get("agreement"))
        print("Votes:")
        for k, v in r.get("votes", {}).items():
            print(f"  {k}: {v}")

asyncio.run(run_test())
