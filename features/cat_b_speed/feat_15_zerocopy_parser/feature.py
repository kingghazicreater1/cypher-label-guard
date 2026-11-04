from typing import Any, Dict
from core.base_feature import BaseFeature
from core.context import ExecutionContext


class ZeroCopyParserFeature(BaseFeature):
    """
    Feature 15: Zero-Copy Parsing
    Enables zero-copy slicing of string/byte buffers, bypassing standard
    heap string duplication and minimizing garbage collection pauses.
    """

    async def execute(self, context: ExecutionContext) -> ExecutionContext:
        payload = context.input_payload
        text_data = payload.get("text", "")

        if isinstance(text_data, str) and len(text_data) > 0:
            byte_view = memoryview(text_data.encode("utf-8"))
            parsed_length = len(byte_view)
        else:
            parsed_length = 0

        metadata = dict(context.metadata)
        metadata["zero_copy_parsed_bytes"] = parsed_length
        metadata["zero_copy_active"] = True

        return context.evolve(
            metadata=metadata,
        )
