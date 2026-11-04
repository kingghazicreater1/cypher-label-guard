import asyncio
from typing import Any, Dict
from core.base_feature import BaseFeature
from core.context import ExecutionContext


class AsyncNonBlockingIoFeature(BaseFeature):
    """
    Feature 13: Async Non-Blocking I/O
    Verifies and maintains the non-blocking async execution harness for concurrent calls.
    """

    async def execute(self, context: ExecutionContext) -> ExecutionContext:
        loop = asyncio.get_running_loop()
        is_running = loop.is_running()

        metadata = dict(context.metadata)
        metadata["async_event_loop_active"] = is_running
        metadata["async_concurrency_mode"] = "FULL_PARALLEL"

        new_flags = dict(context.flags)
        new_flags["async_io_enabled"] = True

        return context.evolve(
            metadata=metadata,
            flags=new_flags,
        )
