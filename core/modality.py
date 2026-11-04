import re
from typing import Optional

def derive_modality(
    filename: Optional[str],
    mime_type: Optional[str] = None,
    has_both_media_and_text: bool = False,
) -> str:
    """
    Canonical, state-independent modality derivation.
    Returns: 'VIDEO' | 'AUDIO' | 'IMAGE' | 'MULTI_MODAL' | 'TEXT'
    """
    if has_both_media_and_text:
        return "MULTI_MODAL"

    name_clean = (filename or "").strip().lower()
    mime_clean = (mime_type or "").strip().lower()

    if "multi-modal" in name_clean or "claim vs evidence" in name_clean or "mixed modality" in name_clean:
        return "MULTI_MODAL"

    if (
        mime_clean.startswith("video/")
        or "video container payload:" in name_clean
        or re.search(r"\.(mp4|mov|avi|mkv|webm|m4v|3gp|flv|wmv)\b", name_clean)
    ):
        return "VIDEO"

    if (
        mime_clean.startswith("audio/")
        or "audio track payload:" in name_clean
        or re.search(r"\.(mp3|wav|ogg|m4a|aac|flac)\b", name_clean)
    ):
        return "AUDIO"

    if (
        mime_clean.startswith("image/")
        or "visual payload:" in name_clean
        or re.search(r"\.(png|jpe?g|webp|gif|svg|bmp|ico|tiff)\b", name_clean)
    ):
        return "IMAGE"

    return "TEXT"
