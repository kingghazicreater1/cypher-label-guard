from typing import Any, Dict
from core.base_feature import BaseFeature
from core.context import ExecutionContext


class AdaptiveDimensionSelectorFeature(BaseFeature):
    """
    Feature 05: Adaptive Dimension Selector
    Profiles input payload characteristics to dynamically activate
    and weight the most informative subspace dimensions.
    """

    async def execute(self, context: ExecutionContext) -> ExecutionContext:
        payload = context.input_payload
        text = str(payload.get("text", ""))

        active_dimensions = [
            "category", "confidence", "sub_category", "anomaly",
            "sentiment", "entity_relationship", "temporal_context", "risk_assessment"
        ]

        # Context-dependent dynamic weighting
        weights = {dim: 1.0 for dim in active_dimensions}
        if "risk" in text.lower() or "threat" in text.lower():
            weights["risk_assessment"] = 1.8
            weights["anomaly"] = 1.5
        elif "date" in text.lower() or "timestamp" in text.lower():
            weights["temporal_context"] = 1.6

        ephemeral = dict(context.ephemeral_store)
        ephemeral["adaptive_dimension_weights"] = weights

        metadata = dict(context.metadata)
        metadata["active_dimensions_count"] = len(active_dimensions)

        return context.evolve(
            ephemeral_store=ephemeral,
            metadata=metadata,
        )
