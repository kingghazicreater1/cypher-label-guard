import hashlib
import json
import re
import secrets
import unicodedata
from typing import Any, Dict, List, Optional, Tuple


class BlindIngressMasker:
    """
    Blind Ingress Masker & Dual-Sided Egress Guard
    Addresses Gaps 2 & 4:
    - Stores token vault & mask policy in volatile RAM only.
    - Policy content is NEVER logged; only sha256(policy) is exposed for lineage hashing.
    - Ephemeral 256-bit nonce prevents cross-job correlation.
    - Dual-sided token echo scanner detects both token reflections and raw vault strings.
    """

    # In-memory ephemeral storage for active jobs: trace_id -> vault_data
    # Volatile memory only — never persisted to SQLite or disk
    _RAM_VAULTS: Dict[str, Dict[str, Any]] = {}

    FORBIDDEN_ECHO_PATTERNS = [
        re.compile(r"\[SPECIMEN_\w+\]", re.IGNORECASE),
        re.compile(r"\[SERIAL_\w+\]", re.IGNORECASE),
        re.compile(r"\[LOC_\w+\]", re.IGNORECASE),
        re.compile(r"\[BRAND_\w+\]", re.IGNORECASE),
        re.compile(r"\[TARGET_\w+\]", re.IGNORECASE),
        re.compile(r"\[WORKSPACE_\w+\]", re.IGNORECASE),
        re.compile(r"TOKEN_[0-9A-F]{4,}", re.IGNORECASE),
    ]

    @classmethod
    def mask_ingress(
        cls,
        trace_id: str,
        raw_text: str,
        modality: str,
        criteria: List[Dict[str, Any]],
        workspace_name: str = "General Workspace"
    ) -> Tuple[str, str, List[Dict[str, Any]]]:
        """
        Masks direct identifiers from raw input payload into abstract specimen tokens.
        Stores the mapping and policy in volatile RAM.
        Returns: (masked_text, policy_hash, masked_criteria)
        """
        # Ephemeral 256-bit nonce and per-job cryptographic salt (Hardening Item 4)
        job_nonce = secrets.token_hex(32)
        job_salt = secrets.token_bytes(32)

        # Build task-aware mask policy in volatile RAM
        policy = {
            "trace_id": trace_id,
            "modality": modality,
            "job_nonce": job_nonce,
            "mask_targets": ["FILENAME", "SERIAL_NUMBER", "WORKSPACE_BRAND", "TIMESTAMPS"],
            "preserve_targets": ["GEOMETRY", "DEFECT_PATTERNS", "SURFACE_TEXTURE"],
            "storage": "VOLATILE_RAM_ONLY",
            "logging_allowed": False
        }

        # Compute salted SHA-256 policy hash: sha256(job_salt || policy_bytes)
        # Guarantees that two jobs with identical policies produce completely uncorrelated lineage hashes
        policy_bytes = json.dumps(policy, sort_keys=True).encode("utf-8")
        policy_hash = f"sha256:{hashlib.sha256(job_salt + policy_bytes).hexdigest()}"

        # For TEXT modality (without media payload prefixes), the text is the document itself.
        # Only mask workspace name and direct metadata, preserving the natural language document.
        is_text_doc = (modality or "").upper() == "TEXT" and not any(
            p in raw_text for p in ["Visual payload:", "Analyzing payload:", "Vision Labeled:", "Video container payload:", "Audio track payload:"]
        )

        ephemeral_spec_id = secrets.token_hex(8).upper()
        ephemeral_ws_id = secrets.token_hex(8).upper()
        specimen_token = f"[SPECIMEN_{ephemeral_spec_id}]"
        workspace_token = f"[WORKSPACE_{ephemeral_ws_id}]"

        if is_text_doc:
            masked_text = raw_text
            if workspace_name and workspace_name != "General Workspace" and workspace_name in masked_text:
                masked_text = masked_text.replace(workspace_name, workspace_token)
            cls._RAM_VAULTS[trace_id] = {
                "trace_id": trace_id,
                "job_nonce": job_nonce,
                "policy": policy,
                "policy_hash": policy_hash,
                "token_map": {workspace_token: workspace_name},
                "raw_strings": [workspace_name] if workspace_name and len(workspace_name) >= 2 else []
            }
            return masked_text, policy_hash, criteria

        # Extract filename / raw asset identifier
        extracted_name = ""
        text_clean = raw_text
        for prefix in ["Visual payload:", "Analyzing payload:", "Vision Labeled:", "Video container payload:", "Audio track payload:"]:
            text_clean = text_clean.replace(prefix, "")
        raw_clean = unicodedata.normalize("NFKC", text_clean).split("(")[0].strip()
        stem = re.sub(r"\.[a-zA-Z0-9]+$", "", raw_clean).strip()
        if stem:
            extracted_name = raw_clean

        # Generate ephemeral anonymous tokens with 64-bit cryptographically secure entropy
        # 64-bit space (1.84 x 10^19) eliminates birthday-bound collisions at production scale
        ephemeral_spec_id = secrets.token_hex(8).upper()
        ephemeral_ws_id = secrets.token_hex(8).upper()
        specimen_token = f"[SPECIMEN_{ephemeral_spec_id}]"
        workspace_token = f"[WORKSPACE_{ephemeral_ws_id}]"

        # Create the masked text representation
        masked_text = raw_text
        if extracted_name and extracted_name in masked_text:
            masked_text = masked_text.replace(extracted_name, specimen_token)
        elif stem and stem in masked_text:
            masked_text = masked_text.replace(stem, specimen_token)
        else:
            masked_text = f"{modality.capitalize()} Specimen Payload: {specimen_token}"

        if workspace_name and workspace_name in masked_text:
            masked_text = masked_text.replace(workspace_name, workspace_token)

        # Store in RAM-only MMAP dictionary
        cls._RAM_VAULTS[trace_id] = {
            "trace_id": trace_id,
            "job_nonce": job_nonce,
            "policy": policy,
            "policy_hash": policy_hash,
            "token_map": {
                specimen_token: extracted_name or stem or "UNKNOWN_ASSET",
                workspace_token: workspace_name
            },
            "raw_strings": [s for s in [extracted_name, stem, workspace_name] if s and len(s) >= 2]
        }

        # Mask criteria headings if they contain direct raw filenames
        masked_criteria = []
        for c in criteria:
            crit_copy = dict(c)
            for raw_val, tok in [(extracted_name, specimen_token), (stem, specimen_token)]:
                if raw_val and raw_val.lower() in crit_copy.get("name", "").lower():
                    crit_copy["name"] = crit_copy["name"].replace(raw_val, tok)
            masked_criteria.append(crit_copy)

        return masked_text, policy_hash, masked_criteria

    @classmethod
    def audit_token_echo(
        cls,
        trace_id: str,
        val: str
    ) -> Tuple[bool, str, str]:
        """
        Dual-sided egress audit (Gap 4 / Token-Echo guard):
        1. Checks for leaked token patterns ([SPECIMEN_...], [SERIAL_...], etc.)
        2. Checks against the original raw vault strings kept in RAM.
        Returns: (is_anomaly, guard_name, matched_token)
        """
        if not val:
            return False, "", ""

        val_norm = unicodedata.normalize("NFKC", str(val)).strip()

        # Check 1: Forbidden Token Pattern Reflection
        for pat in cls.FORBIDDEN_ECHO_PATTERNS:
            match = pat.search(val_norm)
            if match:
                return True, "TOKEN_ECHO", match.group(0)

        # Check 2: Raw Vault Reflection (Even if prompt was masked, did model hallucinate real string?)
        COMMON_SAFE_VOCAB = {
            "laptop", "phone", "smartphone", "apple", "fruit", "shoe", "shoes", "sneaker",
            "sneakers", "watch", "car", "bottle", "cup", "coffee", "mug", "cookie", "cookies",
            "camera", "lens", "bag", "book", "chair", "table", "keyboard", "mouse", "screen",
            "display", "headphone", "headphones", "clothing", "apparel", "food", "produce"
        }
        vault = cls._RAM_VAULTS.get(trace_id)
        if vault:
            for raw_str in vault.get("raw_strings", []):
                raw_norm = raw_str.strip().lower()
                has_code = bool(re.search(r"\d|#|img_|dsc_|vid_|win_|frame_|specimen_", raw_norm))
                if len(raw_norm) >= 2:
                    if val_norm.lower() == raw_norm and raw_norm not in COMMON_SAFE_VOCAB:
                        return True, "FILENAME_ECHO", raw_str
                    if has_code and (raw_norm in val_norm.lower() or re.search(rf"\b#?{re.escape(raw_norm)}\b", val_norm.lower())):
                        return True, "FILENAME_ECHO", raw_str
                    if raw_norm not in COMMON_SAFE_VOCAB and len(raw_norm) > 4 and re.search(rf"\b{re.escape(raw_norm)}\b", val_norm.lower()) and not any(w in raw_norm for w in COMMON_SAFE_VOCAB):
                        return True, "FILENAME_ECHO", raw_str

        return False, "", ""

    @classmethod
    def unmask_egress(cls, trace_id: str, val: str) -> str:
        """
        Re-attaches original identity to the label after egress audit passes.
        """
        vault = cls._RAM_VAULTS.get(trace_id)
        if not vault or not val:
            return val

        unmasked = str(val)
        for token, raw_val in vault.get("token_map", {}).items():
            if token in unmasked:
                unmasked = unmasked.replace(token, raw_val)
        return unmasked

    @classmethod
    def flush_vault(cls, trace_id: str) -> None:
        """
        Zero-retention purge: wipes vault and policy from RAM on completion or panic.
        """
        if trace_id in cls._RAM_VAULTS:
            cls._RAM_VAULTS[trace_id].clear()
            del cls._RAM_VAULTS[trace_id]
