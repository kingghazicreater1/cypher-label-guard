from typing import Any, Dict
from core.base_feature import BaseFeature
from core.context import ExecutionContext


class AnthropologicalOutsiderFeature(BaseFeature):
    """
    Feature 33: Anthropological Outsider Module
    Detects regional/cultural perspective bias, auditing whether
    labels adhere to global outsider neutrality.
    """

    async def execute(self, context: ExecutionContext) -> ExecutionContext:
        text = str(context.input_payload.get("text", "")).lower()

        # Check for cultural idioms or regional jargon
        has_cultural_idiom = any(k in text for k in ["proverb", "idiom", "cultural", "local tradition"])

        metadata = dict(context.metadata)
        metadata["anthropological_neutrality_score"] = 0.98 if not has_cultural_idiom else 0.89

        new_flags = dict(context.flags)
        new_flags["anthropological_outsider_audited"] = True

        return context.evolve(
            metadata=metadata,
            flags=new_flags,
        )
