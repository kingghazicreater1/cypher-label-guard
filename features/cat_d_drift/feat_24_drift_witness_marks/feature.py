from typing import Any, Dict
from core.base_feature import BaseFeature
from core.context import ExecutionContext


class DriftWitnessMarksFeature(BaseFeature):
    """
    Feature 24: Drift Witness Marks (Type A + B)
    Type A: External model drift detection (confidence baseline shifts).
    Type B: Internal self-doubt anomaly alarm (inter-subagent discord within single model).
    """

    async def execute(self, context: ExecutionContext) -> ExecutionContext:
        votes = context.votes
        
        # Check Type A: Are confidence scores sinking below 0.65 baseline?
        avg_confidence = (sum(v.confidence for v in votes) / len(votes)) if votes else 0.90
        type_a_drift = avg_confidence < 0.65

        # Check Type B: Disagreement between Category and Risk sub-agents
        risk_votes = [v.vote for v in votes if v.dimension == "risk_assessment"]
        has_high_risk = any("HIGH" in str(r) for r in risk_votes)
        cat_votes = [v.vote for v in votes if v.dimension == "category"]
        has_standard_cat = any("Standard" in str(c) for c in cat_votes)
        type_b_self_doubt = has_high_risk and has_standard_cat

        new_flags = dict(context.flags)
        new_flags["drift_type_a"] = type_a_drift
        new_flags["drift_type_b"] = type_b_self_doubt

        metadata = dict(context.metadata)
        metadata["drift_witness_marks"] = {
            "type_a_model_drift": type_a_drift,
            "type_b_self_doubt": type_b_self_doubt,
            "average_confidence": round(avg_confidence, 3),
        }

        return context.evolve(
            flags=new_flags,
            metadata=metadata,
        )
