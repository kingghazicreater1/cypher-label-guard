from typing import Any, Dict
from core.base_feature import BaseFeature
from core.context import ExecutionContext


class EpistemicHumilityFeature(BaseFeature):
    """
    Feature 25: Epistemic Humility Flag
    Enforces Rule 21: Courage to say "I don't know".
    If certainty cannot be assured, strips false certainty and declares 'UNKNOWN'.
    """

    async def execute(self, context: ExecutionContext) -> ExecutionContext:
        is_humble = context.flags.get("epistemic_humility", False)
        is_stalemate = context.flags.get("stalemate", False)
        is_human_review = context.flags.get("human_review_required", False)
        overall_crit_conf = float(context.metadata.get("overall_criteria_confidence", 0.0) or 0.0)

        # Do not trip UNKNOWN if criteria evaluation has verified high concordance (>= 90%)
        if overall_crit_conf >= 90.0:
            should_declare_unknown = False
        else:
            should_declare_unknown = is_humble or (is_stalemate and is_human_review)

        metadata = dict(context.metadata)
        if should_declare_unknown:
            metadata["primary_consensus_label"] = "UNKNOWN (Epistemic Humility Applied)"
            metadata["epistemic_humility_declared"] = True

        new_flags = dict(context.flags)
        new_flags["epistemic_humility"] = should_declare_unknown

        return context.evolve(
            metadata=metadata,
            flags=new_flags,
        )
