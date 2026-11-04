from typing import Any, Dict
from core.base_feature import BaseFeature
from core.context import ExecutionContext


class TieredDepthScalingFeature(BaseFeature):
    """
    Feature 11: Tiered Depth Scaling
    Fast (2s), Standard (8s), Deep (15-20s).
    Auto-escalates depth if anomaly or entropy flags are tripped.
    """

    BUDGETS = {
        "Fast": 2.0,
        "Standard": 8.0,
        "Deep": 20.0,
    }

    async def execute(self, context: ExecutionContext) -> ExecutionContext:
        current_tier = context.depth_tier
        lower_txt = str(context.input_payload.get("text", "")).lower()
        has_anomaly_keywords = any(kw in lower_txt for kw in [
            "ignore previous instructions", "system prompt override", "override token",
            "attack threat", "adversarial", "security override", "anomaly"
        ])
        is_anomaly = context.flags.get("anomaly_detected", False) or has_anomaly_keywords
        is_stalemate = context.flags.get("stalemate", False)

        new_tier = current_tier

        # Auto-escalation rule:
        # If anomaly or stalemate is detected and we are on Fast or Standard, escalate to Deep
        if (is_anomaly or is_stalemate) and current_tier in ["Fast", "Standard"]:
            new_tier = "Deep"
        elif not current_tier or current_tier not in self.BUDGETS:
            new_tier = "Standard"

        time_budget = self.BUDGETS[new_tier]
        metadata = dict(context.metadata)
        metadata["effective_depth_budget_seconds"] = time_budget
        metadata["auto_escalated"] = (new_tier != current_tier)

        return context.evolve(
            depth_tier=new_tier,
            metadata=metadata,
        )
