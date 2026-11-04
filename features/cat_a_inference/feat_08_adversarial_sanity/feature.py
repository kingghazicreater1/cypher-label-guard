from typing import Any, Dict
from core.base_feature import BaseFeature
from core.context import ExecutionContext


class AdversarialLabelSanityCheckFeature(BaseFeature):
    """
    Feature 08: Adversarial Label Sanity Check
    Scans for adversarial prompt injections, DAN patterns, and contradictory label outputs.
    """

    ADVERSARIAL_TRIGGERS = [
        "ignore previous instructions",
        "ignore all previous instructions",
        "system prompt override",
        "system override",
        "override previous instructions",
        "disregard all instructions",
        "you are now in developer mode",
        "dan mode enabled",
        "jailbreak bypass",
        "unrestricted reasoning mode",
        "paradox alert",
        "reveal developer secret",
        "liar paradox",
        "output \"hacked\"",
        "output 'hacked'",
        "output \"paradox_accepted\"",
    ]

    async def execute(self, context: ExecutionContext) -> ExecutionContext:
        text = str(context.input_payload.get("text", "")).lower()

        # If already flagged at ingress or tripwires triggered in text
        is_adversarial = (
            bool(context.flags.get("adversarial_injection_flagged"))
            or bool(context.metadata.get("adversarial_injection_flagged"))
            or any(trigger in text for trigger in self.ADVERSARIAL_TRIGGERS)
        )

        new_flags = dict(context.flags)
        new_flags["adversarial_injection_flagged"] = is_adversarial

        metadata = dict(context.metadata)
        metadata["adversarial_sanity_passed"] = not is_adversarial

        return context.evolve(
            flags=new_flags,
            metadata=metadata,
        )
