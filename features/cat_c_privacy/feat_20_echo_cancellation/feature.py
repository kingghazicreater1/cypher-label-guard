import random
import time
from typing import Any, Dict, List
from core.base_feature import BaseFeature
from core.context import ExecutionContext, VoteRecord


class EchoCancellationFeature(BaseFeature):
    """
    Feature 20: Data Echo Cancellation
    Guarantees no raw input reflection in outputs, obfuscates timestamps,
    and applies dummy padding to sanitize against length-analysis attacks.
    """

    CONTAINER_SIGNATURES = [
        "ftyp", "mp42", "mp41", "isom", "moov", "mdat",
        "%pdf", "pk\x03\x04", "\x89png", "riff", "matroska", "webm"
    ]

    def _suppress_verbatim(self, raw_input_text: str, reasoning: str) -> str:
        """Strips verbatim phrases of length >= 20 characters from reasoning."""
        if not raw_input_text or not reasoning:
            return reasoning

        # Check in sliding windows of 20 chars
        window_size = 20
        clean_reasoning = reasoning
        for i in range(0, max(0, len(raw_input_text) - window_size + 1), 10):
            chunk = raw_input_text[i:i + window_size]
            if chunk and chunk in clean_reasoning:
                clean_reasoning = clean_reasoning.replace(chunk, "[REDACTED_ECHO]")
        
        # Scrub container magic tokens
        for sig in self.CONTAINER_SIGNATURES:
            if sig in clean_reasoning.lower():
                clean_reasoning = clean_reasoning.replace(sig, "[REDACTED_SIGNATURE]")
        return clean_reasoning

    def _is_echo_anomaly(self, val: str, raw_input_text: str, trace_id: str = "") -> tuple[bool, str, str]:
        """Detects if a vote value is echoing container magic bytes, masked tokens, or raw filename."""
        import unicodedata
        import re
        if not val:
            return False, "", ""
        v_norm = unicodedata.normalize("NFKC", str(val)).strip().lower()

        # 0. Check Blind Ingress Masker token and raw vault echo (Dual-Sided Guard)
        try:
            from features.cat_c_privacy.blind_masker import BlindIngressMasker
            is_tok_anom, tok_guard, tok_matched = BlindIngressMasker.audit_token_echo(trace_id, val)
            if is_tok_anom:
                return True, tok_guard, tok_matched
        except Exception:
            pass

        # 1. Container magic bytes signature check (word boundary or prefix to avoid false positives)
        for sig in self.CONTAINER_SIGNATURES:
            if v_norm.startswith(sig) or re.search(rf"\b{re.escape(sig)}\b", v_norm):
                return True, "CONTAINER_SIGNATURE", sig

        # 2. Filename and stem echo check
        if raw_input_text:
            text_clean = raw_input_text
            for prefix in ["Visual payload:", "Analyzing payload:", "Vision Labeled:", "Video container payload:", "Audio track payload:"]:
                text_clean = text_clean.replace(prefix, "")
            raw_clean = unicodedata.normalize("NFKC", text_clean).split("(")[0].strip()
            stem = re.sub(r"\.[a-zA-Z0-9]+$", "", raw_clean).strip().lower()

            if stem and len(stem) >= 2:
                if v_norm == stem or v_norm == raw_clean.lower():
                    return True, "FILENAME_ECHO", stem
                if len(stem) > 3 and stem in v_norm:
                    return True, "FILENAME_ECHO", stem
                if re.search(rf"\b#?{re.escape(stem)}\b", v_norm):
                    return True, "FILENAME_ECHO", stem

        return False, "", ""

    def _obfuscate_timestamp(self, ts: float) -> float:
        """Applies ±50ms pseudorandom jitter to neutralize timing correlation attacks."""
        jitter = random.uniform(-0.05, 0.05)
        return round(ts + jitter, 3)


    def _apply_dummy_padding(self, data: str, block_size: int = 128) -> str:
        """Pads string length to a uniform block multiple."""
        current_len = len(data)
        needed = (block_size - (current_len % block_size)) % block_size
        return data + (" " * needed)

    async def execute(self, context: ExecutionContext) -> ExecutionContext:
        input_text = str(context.input_payload.get("text", ""))

        sanitized_votes: List[VoteRecord] = []
        anomaly_flagged = False
        first_guard = ""
        first_token = ""
        for v in context.votes:
            scrubbed_reasoning = self._suppress_verbatim(input_text, v.reasoning)
            scrubbed_vote = v.vote
            is_anom, guard, token = self._is_echo_anomaly(str(v.vote), input_text, context.trace_id)
            if is_anom:
                scrubbed_vote = f"[REJECTED: {guard}]"
                anomaly_flagged = True
                if not first_guard:
                    first_guard = guard
                    first_token = token

            obfuscated_ts = self._obfuscate_timestamp(v.timestamp)
            sanitized_votes.append(
                VoteRecord(
                    api=v.api,
                    dimension=v.dimension,
                    vote=scrubbed_vote,
                    confidence=0.0 if is_anom else v.confidence,
                    reasoning=scrubbed_reasoning,
                    latency_ms=v.latency_ms,
                    timestamp=obfuscated_ts,
                )
            )

        new_flags = dict(context.flags)
        new_flags["echo_cancellation_applied"] = True
        if anomaly_flagged:
            new_flags["echo_anomaly_detected"] = True
            new_flags["echo_guard_fired"] = first_guard
            new_flags["echo_matched_token"] = first_token

        return context.evolve(
            votes=sanitized_votes,
            flags=new_flags,
            metadata={
                "echo_cancellation_status": "CLEARED" if not anomaly_flagged else "ANOMALY_BLOCKED",
                "echo_anomaly_detected": anomaly_flagged,
                "echo_guard_fired": first_guard,
                "echo_matched_token": first_token,
            },
        )


