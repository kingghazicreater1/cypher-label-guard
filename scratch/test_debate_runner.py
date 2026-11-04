import asyncio
import os
import sys

sys.path.insert(0, os.path.abspath("."))
from core.context import ExecutionContext, VoteRecord
from scratch.test_gated_debate import GatedAdversarialDebateFeature

async def run_tests():
    feat = GatedAdversarialDebateFeature()

    # Scenario 1: Gate CLOSED (Unanimous Quorum >= 28 votes)
    ctx1 = ExecutionContext(
        tenant_id="test_org",
        flags={"confirmed": True, "stalemate": False},
        votes=[VoteRecord(api="openai_gpt4", dimension="category", vote="Technology & Software", confidence=0.98)] * 4
    )
    res1 = await feat.execute(ctx1)
    assert not res1.metadata.get("adversarial_debate"), "Gate should be CLOSED for unanimous confirmation!"
    print("[PASS] Scenario 1: Gate remained CLOSED for unanimous quorum.")

    # Scenario 2: Gate OPEN (Stalemate Deadlock: 2 for Medical vs 2 for General)
    ctx2 = ExecutionContext(
        tenant_id="test_org",
        input_payload={"text": "Severe allergic reaction and anaphylaxis following penicillin injection."},
        flags={"confirmed": False, "stalemate": True},
        votes=[
            VoteRecord(api="anthropic_claude", dimension="category", vote="Medical & Healthcare", confidence=0.95),
            VoteRecord(api="openai_gpt4", dimension="category", vote="Medical & Healthcare", confidence=0.90),
            VoteRecord(api="mistral_large", dimension="category", vote="General & Conversational", confidence=0.60),
            VoteRecord(api="google_gemini", dimension="category", vote="General & Conversational", confidence=0.65),
        ]
    )
    res2 = await feat.execute(ctx2)
    assert res2.metadata.get("adversarial_debate"), "Gate should be OPEN for stalemate!"
    debate_info = res2.metadata["adversarial_debate"]
    print("[PASS] Scenario 2: Gate OPENED for stalemate.")
    print("  Winner:", debate_info["adjudication_winner"])
    print("  Rationale:", debate_info["adjudication_rationale"])
    print("  Stalemate flag cleared:", res2.flags["stalemate"] == False)
    print("  Confirmed flag set:", res2.flags["confirmed"] == True)
    assert debate_info["adjudication_winner"] == "Medical & Healthcare", "Specific Medical category should defeat generic conversational!"

if __name__ == "__main__":
    asyncio.run(run_tests())
