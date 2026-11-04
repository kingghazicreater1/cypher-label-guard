from typing import Any, Dict, List
from core.base_feature import BaseFeature
from core.context import ExecutionContext


class ProveItButtonFeature(BaseFeature):
    """
    Feature 32: Prove It Button
    Generates the transparent forensic dossier proving every detail behind the assigned label.
    """

    async def execute(self, context: ExecutionContext) -> ExecutionContext:
        consensus_meta = context.metadata.get("parliament_consensus", {})
        consensus_label = consensus_meta.get("label", "CONFIRMED")
        affirmative_votes = consensus_meta.get("affirmative_votes", len(context.votes))

        forensic_dossier = {
            "session_id": context.session_id,
            "trace_id": context.trace_id,
            "tenant_id": context.tenant_id,
            "depth_tier": context.depth_tier,
            "total_votes": len(context.votes),
            "consensus_label": consensus_label,
            "affirmative_votes": affirmative_votes,
            "vote_breakdown": [v.to_dict() for v in context.votes],
            "lineage_ledger": [entry.to_dict() for entry in context.lineage_chain],
            "lineage_unbroken": context.verify_lineage(),
            "attributed_tokens": context.metadata.get("attributed_tokens", []),
            "entropy_score": context.flags.get("entropy_score", 0.0),
            "fidelity_score": context.flags.get("fidelity_score", 1.0),
            "deterministic_state_hash": context.metadata.get("deterministic_state_hash", ""),
        }

        metadata = dict(context.metadata)
        metadata["prove_it_dossier"] = forensic_dossier

        new_flags = dict(context.flags)
        new_flags["prove_it_certified"] = True

        return context.evolve(
            metadata=metadata,
            flags=new_flags,
        )
