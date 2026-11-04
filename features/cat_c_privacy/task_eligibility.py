import re
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple


class ExecutionPlane(str, Enum):
    BLIND_ELIGIBLE = "BLIND_ELIGIBLE"
    CIRCULAR_TRAP = "CIRCULAR_TRAP"
    ENCLAVE_REQUIRED = "ENCLAVE_REQUIRED"


class TaskEligibilityRouter:
    """
    Task-Eligibility Ingress Router
    Resolves the 4 architectural gaps:
    1. CIRCULAR_TRAP is evaluated FIRST before any identity checks.
    2. Identity-bearing criteria routed to LOCAL_ENCLAVE.
    3. Audio defaults to ENCLAVE_REQUIRED until feasibility spike is verified.
    4. Structural / Defect / Geometry tasks routed to BLIND_ELIGIBLE.
    """

    # Gap 1: Circularity keywords where the task IS detecting PII or sensitive identity
    CIRCULAR_KEYWORDS = [
        r"\bfind\b.*\b(pii|ssn|credit card|phone|email|face|identity)\b",
        r"\bdetect\b.*\b(pii|face|license plate|card number|social security)\b",
        r"\bpii\b",
        r"\bface detection\b",
        r"\bcredit card\b",
        r"\baudit pii\b",
        r"\bcompliance check\b"
    ]

    # Tasks that inherently require identity verification
    IDENTITY_KEYWORDS = [
        r"\bbrand\b",
        r"\blogo\b",
        r"\bwho is\b",
        r"\bidentity\b",
        r"\bserial number ocr\b",
        r"\bspeaker verification\b",
        r"\bface verification\b",
        r"\bacme\b"
    ]

    @classmethod
    def evaluate(
        cls,
        criteria: List[Dict[str, Any]],
        modality: str = "IMAGE"
    ) -> Tuple[ExecutionPlane, str, Dict[str, Any]]:
        """
        Evaluates task headings and criteria to determine the execution plane.
        Returns: (ExecutionPlane, routing_reason, metadata)
        """
        combined_text = " ".join([
            f"{c.get('name', '')} {c.get('type', '')} {c.get('range', '')}"
            for c in criteria
        ]).lower().strip()

        # BRANCH 1 (GAP 1 FIX): Is the task DETECTING / CLASSIFYING identity or PII itself?
        for pattern in cls.CIRCULAR_KEYWORDS:
            if re.search(pattern, combined_text):
                return (
                    ExecutionPlane.CIRCULAR_TRAP,
                    f"Circularity Trap: Task target '{pattern}' is PII/Identity detection itself. "
                    "Cannot mask what the task is tasked to find. Routed to Local Edge Enclave (Zero Masking).",
                    {
                        "masking_applied": False,
                        "execution_environment": "LOCAL_EDGE_ON_PREM",
                        "audit_code": "CIRCULAR_TRAP_LOCAL_EXECUTION"
                    }
                )

        # BRANCH 2: Does labeling require an identity attribute (brand, specific person, serial number)?
        for pattern in cls.IDENTITY_KEYWORDS:
            if re.search(pattern, combined_text):
                return (
                    ExecutionPlane.ENCLAVE_REQUIRED,
                    f"Identity Dependency: Task requires identity attribute '{pattern}'. "
                    "Blind inference cannot label identity-bearing attributes by design. Routed to Local Enclave.",
                    {
                        "masking_applied": False,
                        "execution_environment": "LOCAL_EDGE_ENCLAVE",
                        "audit_code": "IDENTITY_ENCLAVE_REQUIRED"
                    }
                )

        # BRANCH 3 (GAP 3 FIX): Modality check. Audio defaults to ENCLAVE_REQUIRED until feasibility spike.
        norm_modality = str(modality).upper().strip()
        if norm_modality == "AUDIO":
            return (
                ExecutionPlane.ENCLAVE_REQUIRED,
                "Audio Modality: Defaulting to Local Enclave (Feasibility spike pending; "
                "formant-preserving voice anonymization not yet proven on 10-asset spike).",
                {
                    "masking_applied": False,
                    "execution_environment": "LOCAL_EDGE_ENCLAVE",
                    "audit_code": "AUDIO_SPIKE_PENDING_ENCLAVE"
                }
            )

        # BRANCH 4: Structural / Quality / Defect Detection is BLIND_ELIGIBLE
        return (
            ExecutionPlane.BLIND_ELIGIBLE,
            f"Blind Inference Approved: Task focuses on structural/quality attributes for {norm_modality}. "
            "Surgical task-aware masking and RAM-only ephemeral token vault enabled.",
            {
                "masking_applied": True,
                "execution_environment": "PARLIAMENT_BLIND_CLOUD",
                "audit_code": "BLIND_INFERENCE_CLEARED"
            }
        )
