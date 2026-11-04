import os
from typing import Any, Dict
from core.base_feature import BaseFeature
from core.context import ExecutionContext


class PanicSaltFlushFeature(BaseFeature):
    """
    Feature 21: Panic-Induced Salt Flush
    Emergency routine. If panic is flagged or requested,
    all internal salts, volatile nonces, and session tokens are scrubbed.
    """

    def __init__(self, manifest: Dict[str, Any]):
        super().__init__(manifest)
        self._active_salt = os.urandom(32)

    def trigger_panic_flush(self) -> None:
        """Immediately overwrites internal salt with zeroes."""
        self._active_salt = b"\x00" * 32

    async def execute(self, context: ExecutionContext) -> ExecutionContext:
        is_panic_requested = context.flags.get("panic_flush_requested", False)
        ephemeral = dict(context.ephemeral_store)

        if is_panic_requested:
            self.trigger_panic_flush()
            ephemeral.clear()
            new_flags = dict(context.flags)
            new_flags["panic_flushed"] = True
            new_flags["quarantined"] = True

            return context.evolve(
                ephemeral_store={},
                flags=new_flags,
                metadata={"panic_status": "FLUSH_EXECUTED_ZERO_TRACES"},
            )

        # Standard non-panic pass: rotates salt securely
        self._active_salt = os.urandom(32)
        ephemeral["salt_healthy"] = True
        return context.evolve(ephemeral_store=ephemeral)
