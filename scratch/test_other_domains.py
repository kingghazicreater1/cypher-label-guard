import asyncio
import sys
import uuid
sys.path.insert(0, ".")
from dotenv import load_dotenv
load_dotenv()

from core.context import ExecutionContext
from core.orchestrator import orchestrator
from core.registry import registry

registry.load_all_features()
orchestrator.depth_budgets["Standard"] = 75.0

samples = [
    {
        "domain": "Medical",
        "text": "Patient was admitted with acute dyspnea, bilateral pulmonary rales, and oxygen saturation of 88% on ambient air. Administered 40mg IV furosemide and supplemental oxygen via nasal cannula."
    },
    {
        "domain": "Legal",
        "text": "The Contractor shall indemnify, defend, and hold harmless the Client and its officers, directors, and employees against any and all third-party claims, liabilities, or losses arising from breach of warranty."
    },
    {
        "domain": "General / Donkey",
        "text": "a donkey reading books in an open green meadow on a sunny Sunday afternoon."
    }
]

async def main():
    for item in samples:
        ctx = ExecutionContext(
            trace_id=str(uuid.uuid4()),
            tenant_id="universal_multi_domain_test",
            depth_tier="Standard",
            input_payload={"text": item["text"]},
        )
        res = await orchestrator.run_pipeline(ctx)
        print(f"\n--- Testing Domain: {item['domain']} ---")
        print("Expected Topic   :", item["domain"])
        print("Decision         :", res.metadata.get("parliament_decision"))
        print("Consensus Label  :", res.metadata.get("primary_consensus_label"))
        print("Concordant Votes :", res.metadata.get("concordant_votes"), "/ 32")
        print("Entropy Bits     :", res.metadata.get("entropy_bits"))
        print("Humility Declared:", res.flags.get("epistemic_humility"))
        for v in res.votes:
            if v.dimension == "category":
                print(f"  {v.api:18s} -> {v.vote}")

if __name__ == "__main__":
    asyncio.run(main())
