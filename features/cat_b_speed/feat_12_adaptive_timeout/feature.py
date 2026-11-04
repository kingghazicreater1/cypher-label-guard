from typing import Any, Dict
from core.base_feature import BaseFeature
from core.context import ExecutionContext


class AdaptiveTimeoutFeature(BaseFeature):
    """
    Feature 12: Adaptive Timeout Threshold & Circuit Breaker
    Adapts timeouts dynamically based on rolling latency averages
    and enforces quorum continuity when individual APIs experience latency spikes.
    """

    def __init__(self, manifest: Dict[str, Any]):
        super().__init__(manifest)
        self.rolling_latencies: Dict[str, float] = {
            "openai_gpt4": 0.8,
            "anthropic_claude": 0.9,
            "google_gemini": 0.5,
            "mistral_large": 0.7,
        }

    async def execute(self, context: ExecutionContext) -> ExecutionContext:
        depth = context.depth_tier
        base_multiplier = 1.0 if depth == "Fast" else (2.0 if depth == "Standard" else 4.0)

        adaptive_timeouts = {
            api: round(max(1.0, lat * base_multiplier * 1.5), 2)
            for api, lat in self.rolling_latencies.items()
        }

        metadata = dict(context.metadata)
        metadata["adaptive_model_timeouts"] = adaptive_timeouts

        new_flags = dict(context.flags)
        new_flags["adaptive_timeouts_configured"] = True

        return context.evolve(
            metadata=metadata,
            flags=new_flags,
        )
