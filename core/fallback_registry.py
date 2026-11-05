import re
from typing import List, Tuple

class FallbackRegistry:
    """
    Centralized Fallback Registry for CypherLabelGuard.
    Prevents any generic descriptor or fallback string from receiving manufactured high-confidence passes.
    """

    FALLBACK_PATTERNS: List[re.Pattern] = [
        re.compile(r"High-Definition Video Stream Specimen", re.IGNORECASE),
        re.compile(r"Temporal Video Stream Specimen", re.IGNORECASE),
        re.compile(r"Acoustic Signal Processing Specimen", re.IGNORECASE),
        re.compile(r"Precision Industrial (Assembly|Component|Bearing|Specimen)", re.IGNORECASE),
        re.compile(r"(Industrial|Factory) Precision (Bearing |Product |Assembly |Component )?Specimen", re.IGNORECASE),
        re.compile(r"Factory Precision (Assembly|Product|Component)", re.IGNORECASE),
        re.compile(r"Industrial Precision Bearing Assembly", re.IGNORECASE),
        re.compile(r"Precision Industrial Component", re.IGNORECASE),
        re.compile(r"Precision Industrial Assembly", re.IGNORECASE),
        re.compile(r"Target (Media|Visual|Audio|Video) Stream", re.IGNORECASE),
        re.compile(r"Canonical Industry Product Designation", re.IGNORECASE),
        re.compile(r"Generic (Visual|Text|Acoustic|Video) Specimen", re.IGNORECASE),
        re.compile(r"Standard Test Video Sequence", re.IGNORECASE),
        re.compile(r"Synthesized Acoustic Stream", re.IGNORECASE),
        re.compile(r"\[UNVERIFIED", re.IGNORECASE),
        re.compile(r"\[REJECTED", re.IGNORECASE),
        re.compile(r"Verified / Pristine", re.IGNORECASE),
        re.compile(r"no specimen detected", re.IGNORECASE),
    ]

    CANONICAL_UNVERIFIED_VALUE = "[UNVERIFIED: NO SPECIMEN DETECTED]"

    @classmethod
    def is_fallback(cls, value: str) -> Tuple[bool, str]:
        """
        Checks if a value matches any registered fallback pattern.
        Returns: (is_fallback, matched_pattern_str)
        """
        if not value:
            return False, ""
        val_str = str(value).strip()
        for pattern in cls.FALLBACK_PATTERNS:
            if pattern.search(val_str):
                return True, pattern.pattern
        return False, ""

    @classmethod
    def get_all_registered_patterns(cls) -> List[str]:
        return [p.pattern for p in cls.FALLBACK_PATTERNS]
