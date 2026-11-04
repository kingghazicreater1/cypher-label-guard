import hashlib
import json
from typing import Any, Dict
from core.base_feature import BaseFeature
from core.context import ExecutionContext


class ImmutableLineageFeature(BaseFeature):
    """
    Feature 22: Immutable Lineage Hashing
    Calculates cryptographic digests of the parliament votes and produces
    the authoritative SHA-256 seal for the 'Prove It' audit trail.
    """

    async def execute(self, context: ExecutionContext) -> ExecutionContext:
        # 1. Compute vote matrix digest
        vote_dicts = [v.to_dict() for v in context.votes]
        vote_matrix_bytes = json.dumps(vote_dicts, sort_keys=True).encode("utf-8")
        vote_matrix_hash = hashlib.sha256(vote_matrix_bytes).hexdigest()

        # 2. Append lineage step with the vote matrix digest
        sealed_context = context.with_lineage_step(
            step_name="VOTE_MATRIX_LINEAGE_SEAL",
            payload_data={
                "total_votes": len(context.votes),
                "vote_matrix_hash": vote_matrix_hash,
                "chain_valid": context.verify_lineage(),
            }
        )

        new_flags = dict(sealed_context.flags)
        new_flags["lineage_sealed"] = True

        return sealed_context.evolve(
            flags=new_flags,
            metadata={"final_lineage_hash": sealed_context.lineage_chain[-1].current_hash},
        )
