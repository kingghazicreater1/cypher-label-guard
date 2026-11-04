from typing import Any, Dict
from core.base_feature import BaseFeature
from core.context import ExecutionContext


class ThreeTierHumanOptionsFeature(BaseFeature):
    """
    Feature 29: Three-Tier Human Options
    Triage system directing borderline items into:
    - Quick Review (1-Click)
    - Batch Review (Clustered)
    - Full Manual Review (Forensic)
    """

    async def execute(self, context: ExecutionContext) -> ExecutionContext:
        is_review_needed = context.flags.get("human_review_required", False)
        is_stalemate = context.flags.get("stalemate", False)
        is_adversarial = context.flags.get("adversarial_injection_flagged", False)

        if is_adversarial:
            human_tier = "Tier 3: Full Manual Review"
        elif is_stalemate:
            human_tier = "Tier 2: Batch Review"
        elif is_review_needed:
            human_tier = "Tier 1: Quick Review"
        else:
            human_tier = "AUTOMATED_CLEAR"

        metadata = dict(context.metadata)
        metadata["human_review_tier"] = human_tier

        new_flags = dict(context.flags)
        new_flags["human_assigned_tier"] = human_tier

        return context.evolve(
            metadata=metadata,
            flags=new_flags,
        )
