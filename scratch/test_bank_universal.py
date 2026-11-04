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

text = (
    "On March 15, 2024, Mr. Daniel Okafor visited the Lagos branch of FirstTrust Bank to open a savings account. "
    "He presented his national identity card and proof of address, as required by the bank's Know Your Customer (KYC) policy. "
    "The account officer, Ms. Adaeze Nwosu, explained that the account would attract a 4% annual interest rate and a minimum "
    "opening deposit of ₦50,000. Mr. Okafor deposited ₦75,000 and was issued an ATM card. However, he was informed that a "
    "monthly maintenance fee of ₦500 would be deducted if his balance fell below ₦20,000. He also opted for mobile banking, "
    "which required a one-time activation fee of ₦1,000. The transaction was completed at 11:45 AM, and a receipt was issued."
)

async def main():
    ctx = ExecutionContext(
        trace_id=str(uuid.uuid4()),
        tenant_id="tenant_bank_test",
        depth_tier="Standard",
        input_payload={"text": text},
    )
    res = await orchestrator.run_pipeline(ctx)
    
    print("\n=================== UNIVERSAL PIPELINE TEST RESULTS ===================")
    print("Decision                 :", res.metadata.get("parliament_decision"))
    print("Primary Consensus Label  :", res.metadata.get("primary_consensus_label"))
    print("Concordant Votes Cast    :", res.metadata.get("concordant_votes"), "/ 32")
    print("Total Dimensional Votes  :", len(res.votes))
    print("Epistemic Humility Flag  :", res.flags.get("epistemic_humility"))
    print("Shannon Entropy Bits     :", res.metadata.get("entropy_bits"))
    print("Threshold Met            :", res.flags.get("confirmed"))
    print("\nCategory Votes Cast Across 4 Parliamentary Seats:")
    for v in res.votes:
        if v.dimension == "category":
            print(f"  [{v.api:18s}] -> {v.vote:25s} (Conf: {v.confidence}, Latency: {v.latency_ms}ms, Reasoning: {v.reasoning})")
    print("=======================================================================")

if __name__ == "__main__":
    asyncio.run(main())
