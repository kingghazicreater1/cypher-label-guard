from typing import Any, Dict
from core.base_feature import BaseFeature
from core.context import ExecutionContext


class MultiModalRouterFeature(BaseFeature):
    """
    Feature 34: Multi-Modal Router
    Auto-detects payload format (Text, Image, Audio, Video) and sets the routing targets.
    """

    async def execute(self, context: ExecutionContext) -> ExecutionContext:
        payload = context.input_payload

        has_media = any(k in payload for k in ["video", "video_frames", "video_url", "audio", "audio_bytes", "audio_url", "image", "image_bytes", "image_url"])
        text_str = str(payload.get("text") or "").strip()
        # Non-generic meaningful text
        has_text = bool(text_str and not text_str.startswith("Visual payload:") and not text_str.startswith("Video container payload:"))

        req_mod = str(payload.get("modality") or "").upper().strip()
        if req_mod in ["VISION", "IMAGE"]:
            modality = "VISION"
        elif req_mod == "AUDIO":
            modality = "AUDIO"
        elif req_mod == "VIDEO":
            modality = "VIDEO"
        elif req_mod in ["MULTI_MODAL", "MIXED"]:
            modality = "MULTI_MODAL"
        elif has_media and has_text:
            modality = "MULTI_MODAL"
        elif "video" in payload or "video_frames" in payload or "video_url" in payload:
            modality = "VIDEO"
        elif "audio" in payload or "audio_bytes" in payload or "audio_url" in payload:
            modality = "AUDIO"
        elif "image" in payload or "image_bytes" in payload or "image_url" in payload:
            modality = "VISION"
        else:
            modality = "TEXT"

        metadata = dict(context.metadata)
        metadata["detected_modality"] = modality

        new_flags = dict(context.flags)
        new_flags["modality"] = modality

        return context.evolve(
            metadata=metadata,
            flags=new_flags,
        )
