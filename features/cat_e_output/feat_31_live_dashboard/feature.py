from typing import Any, Dict, List
from core.base_feature import BaseFeature
from core.context import ExecutionContext


class LiveParliamentDashboardFeature(BaseFeature):
    """
    Feature 31: Live Parliament Dashboard
    Generates the complete 4x8 grid matrix (32 tiles) with color codes:
    - GREEN: High confidence agreement (>= 0.85)
    - YELLOW: Divergence, moderate confidence, or stalemate (0.65 - 0.84)
    - RED: Risk, anomaly, or severe discord (< 0.65)
    """

    def _determine_tile_color(self, vote_val: str, confidence: float, dimension: str) -> str:
        if "HIGH_RISK" in vote_val or "FLAGGED_ANOMALY" in vote_val or confidence < 0.65:
            return "RED"
        elif confidence < 0.85 or "MODERATE" in vote_val:
            return "YELLOW"
        return "GREEN"

    async def execute(self, context: ExecutionContext) -> ExecutionContext:
        grid_tiles: List[Dict[str, Any]] = []

        for v in context.votes:
            color = self._determine_tile_color(v.vote, v.confidence, v.dimension)
            grid_tiles.append({
                "api": v.api,
                "dimension": v.dimension,
                "vote": v.vote,
                "confidence": v.confidence,
                "color": color,
                "latency_ms": v.latency_ms,
            })

        metadata = dict(context.metadata)
        metadata["parliament_grid_4x8"] = grid_tiles

        new_flags = dict(context.flags)
        new_flags["live_dashboard_ready"] = True

        return context.evolve(
            metadata=metadata,
            flags=new_flags,
        )
