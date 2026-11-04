import math
from collections import Counter
from typing import Any, Dict
from core.base_feature import BaseFeature
from core.context import ExecutionContext


class EntropicCertaintyMaskingFeature(BaseFeature):
    """
    Feature 03: Entropic Certainty Masking
    Computes Shannon Entropy over all parliamentary votes.
    If H(X) exceeds the uncertainty threshold, forces 'Unknown' and trips Epistemic Humility.
    """

    def __init__(self, manifest: Dict[str, Any]):
        super().__init__(manifest)
        self.entropy_threshold = 1.35  # Bits of entropy

    def calculate_entropy(self, labels: list[str]) -> float:
        if not labels:
            return 0.0
        counts = Counter(labels)
        total = len(labels)
        entropy = 0.0
        for count in counts.values():
            p = count / total
            if p > 0:
                entropy -= p * math.log2(p)
        return entropy

    async def execute(self, context: ExecutionContext) -> ExecutionContext:
        votes = context.votes
        category_votes = [v.vote for v in votes if v.dimension == "category"]

        entropy = self.calculate_entropy(category_votes)
        is_uncertain = entropy > self.entropy_threshold

        new_flags = dict(context.flags)
        new_flags["entropy_score"] = round(entropy, 3)
        if is_uncertain:
            new_flags["epistemic_humility"] = True
            new_flags["masked_as_unknown"] = True

        metadata = dict(context.metadata)
        metadata["entropy_bits"] = round(entropy, 4)
        metadata["entropy_threshold"] = self.entropy_threshold

        return context.evolve(
            flags=new_flags,
            metadata=metadata,
        )
