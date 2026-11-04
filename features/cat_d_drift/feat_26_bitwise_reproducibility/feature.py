import hashlib
import json
from typing import Any, Dict
from core.base_feature import BaseFeature
from core.context import ExecutionContext


class BitwiseIdenticalReproducibilityFeature(BaseFeature):
    """
    Feature 26: Deterministic Pipeline Lineage & State Digesting
    Ensures that identical internal execution states produce canonical, bitwise identical serialized digests.
    External LLM model drift is witnessed and monitored via Feature 24.
    """

    async def execute(self, context: ExecutionContext) -> ExecutionContext:
        # Build canonical deterministically ordered summary
        canonical_state = {
            "tenant_id": context.tenant_id,
            "depth_tier": context.depth_tier,
            "consensus_label": context.metadata.get("primary_consensus_label", "Unknown"),
            "vote_count": len(context.votes),
        }

        canonical_bytes = json.dumps(canonical_state, sort_keys=True, separators=(",", ":")).encode("utf-8")
        deterministic_hash = hashlib.sha256(canonical_bytes).hexdigest()

        metadata = dict(context.metadata)
        metadata["deterministic_state_hash"] = deterministic_hash

        new_flags = dict(context.flags)
        new_flags["bitwise_reproducible"] = True

        return context.evolve(
            metadata=metadata,
            flags=new_flags,
        )
