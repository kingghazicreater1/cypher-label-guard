import asyncio
import os
import sys

sys.path.insert(0, os.path.abspath("."))
from dotenv import load_dotenv
load_dotenv()
from core.context import ExecutionContext, VoteRecord
from scratch.test_gated_debate import GatedAdversarialDebateFeature

async def test_live_debate():
    feat = GatedAdversarialDebateFeature()

    # Ambiguous specimen: High-end counterfeit watch vs Authentic luxury timepiece
    ctx = ExecutionContext(
        tenant_id="luxury_qc_org",
        input_payload={"text": "Rolex Submariner with misaligned cyclops lens, missing laser-etched crown at 6 o'clock, and lightweight hollow bracelet links."},
        flags={"confirmed": False, "stalemate": True},
        votes=[
            VoteRecord(api="openai_gpt4", dimension="category", vote="Counterfeit / Defect Flagged", confidence=0.88),
            VoteRecord(api="anthropic_claude", dimension="category", vote="Counterfeit / Defect Flagged", confidence=0.92),
            VoteRecord(api="google_gemini", dimension="category", vote="Authentic Luxury Goods", confidence=0.70),
            VoteRecord(api="mistral_large", dimension="category", vote="Authentic Luxury Goods", confidence=0.65),
        ]
    )

    print("[*] Dispatching Gated Adversarial Debate to Live LLM Arbitrator...")
    res = await feat.execute(ctx)
    debate = res.metadata.get("adversarial_debate", {})
    print("\n=== DEBATE VERDICT ===")
    print("Winner:", debate.get("adjudication_winner"))
    print("Rationale:", debate.get("adjudication_rationale"))
    print("Stalemate Cleared:", res.flags.get("stalemate") == False)
    print("Confirmed:", res.flags.get("confirmed") == True)

if __name__ == "__main__":
    asyncio.run(test_live_debate())
