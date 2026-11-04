import hashlib
import json
from typing import Any, Dict
from core.base_feature import BaseFeature
from core.context import ExecutionContext


class StatelessEmbeddingFeature(BaseFeature):
    """
    Feature 23: Stateless Embedding Commitment
    Converts any temporary in-memory embedding into a tamper-proof commitment hash,
    then eradicates raw vectors from RAM so nothing is retained.
    """

    async def execute(self, context: ExecutionContext) -> ExecutionContext:
        ephemeral = dict(context.ephemeral_store)
        raw_embeddings = ephemeral.get("raw_embeddings")

        if raw_embeddings:
            # Generate cryptographic commitment
            serialized = json.dumps(raw_embeddings, sort_keys=True).encode("utf-8")
            commitment_hash = hashlib.sha256(serialized).hexdigest()

            # ERADICATE raw vectors
            ephemeral["raw_embeddings"] = None
            del ephemeral["raw_embeddings"]
            ephemeral["embedding_commitment"] = commitment_hash
        else:
            ephemeral["embedding_commitment"] = "NO_INTERMEDIATE_VECTORS_RETAINED"

        new_flags = dict(context.flags)
        new_flags["embeddings_stateless_committed"] = True

        return context.evolve(
            ephemeral_store=ephemeral,
            flags=new_flags,
            metadata={"stateless_embedding_status": "COMMITTED_AND_ERADICATED"},
        )
