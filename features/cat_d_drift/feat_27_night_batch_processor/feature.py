from typing import Any, Dict, List
from core.base_feature import BaseFeature
from core.context import ExecutionContext


class NightBatchReProcessingFeature(BaseFeature):
    """
    Feature 27: Night Batch Re-Processing
    Enqueues drift-marked items into an in-memory batch spool for off-peak reprocessing.
    """

    def __init__(self, manifest: Dict[str, Any]):
        super().__init__(manifest)
        self.night_spool: List[str] = []

    async def execute(self, context: ExecutionContext) -> ExecutionContext:
        is_drift_a = context.flags.get("drift_type_a", False)
        is_drift_b = context.flags.get("drift_type_b", False)

        enqueued = False
        if is_drift_a or is_drift_b:
            self.night_spool.append(context.trace_id)
            enqueued = True

        metadata = dict(context.metadata)
        metadata["night_batch_enqueued"] = enqueued
        metadata["night_spool_depth"] = len(self.night_spool)

        new_flags = dict(context.flags)
        new_flags["queued_for_night_batch"] = enqueued

        return context.evolve(
            metadata=metadata,
            flags=new_flags,
        )
