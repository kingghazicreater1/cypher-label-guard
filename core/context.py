# ==============================================================================
# 🔒 SACRED FILE 2 OF 4: core/context.py
# RULE 6: context.py IS SACRED.
# Immutable context bus — once added, it's immutable.
# RULE 13 & 14: Zero-Retention and RAM-Only.
# RULE 15: SHA-256 tamper-proof lineage hash chaining.
# RULE 16: Stateless inference bus.
# ==============================================================================

import copy
import hashlib
import json
import time
import uuid
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass(frozen=True)
class VoteRecord:
    """
    Individual vote record cast by a specific API for a specific dimension.
    Part of the 32-Vote Parliament (4 APIs x 8 Dimensions).
    """
    api: str
    dimension: str
    vote: str
    confidence: float
    reasoning: str = ""
    latency_ms: float = 0.0
    timestamp: float = field(default_factory=time.time)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "api": self.api,
            "dimension": self.dimension,
            "vote": self.vote,
            "confidence": self.confidence,
            "reasoning": self.reasoning,
            "latency_ms": self.latency_ms,
            "timestamp": self.timestamp,
        }


@dataclass(frozen=True)
class LineageEntry:
    """
    Cryptographic lineage entry in the SHA-256 tamper-proof audit chain.
    """
    index: int
    step_name: str
    previous_hash: str
    payload_hash: str
    current_hash: str
    timestamp: float = field(default_factory=time.time)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "index": self.index,
            "step_name": self.step_name,
            "previous_hash": self.previous_hash,
            "payload_hash": self.payload_hash,
            "current_hash": self.current_hash,
            "timestamp": self.timestamp,
        }


class ExecutionContext:
    """
    The Immutable Context Bus for CypherLabelGuard v2.0.
    
    Adheres strictly to:
    - Immutable State Transitions via .evolve()
    - RAM-Only volatile residency (never written to disk)
    - Zero-Retention Purge capabilities (.purge())
    - Tamper-proof SHA-256 Audit Lineage Chaining
    """

    def __init__(
        self,
        session_id: Optional[str] = None,
        tenant_id: str = "default_tenant",
        trace_id: Optional[str] = None,
        input_payload: Optional[Dict[str, Any]] = None,
        depth_tier: str = "Standard",  # Fast (2s), Standard (8s), Deep (15-20s)
        votes: Optional[List[VoteRecord]] = None,
        lineage_chain: Optional[List[LineageEntry]] = None,
        flags: Optional[Dict[str, Any]] = None,
        ephemeral_store: Optional[Dict[str, Any]] = None,
        metadata: Optional[Dict[str, Any]] = None,
        created_at: Optional[float] = None,
        is_purged: bool = False,
    ):
        self._session_id = session_id or str(uuid.uuid4())
        self._tenant_id = tenant_id
        self._trace_id = trace_id or str(uuid.uuid4())
        self._input_payload = input_payload or {}
        self._depth_tier = depth_tier
        self._votes: List[VoteRecord] = list(votes) if votes else []
        self._lineage_chain: List[LineageEntry] = list(lineage_chain) if lineage_chain else []
        self._flags: Dict[str, Any] = dict(flags) if flags else {
            "epistemic_humility": False,
            "stalemate": False,
            "human_review_required": False,
            "confirmed": False,
            "drift_type_a": False,
            "drift_type_b": False,
            "degradation_tier": "Parliament",  # Parliament -> Solo -> Rule-based
            "entropy_score": 0.0,
            "fidelity_score": 1.0,
        }
        self._ephemeral_store: Dict[str, Any] = dict(ephemeral_store) if ephemeral_store else {}
        self._metadata: Dict[str, Any] = dict(metadata) if metadata else {}
        self._created_at = created_at or time.time()
        self._is_purged = is_purged

        # Initialize root hash if lineage chain is empty
        if not self._lineage_chain:
            root_seed = f"{self._session_id}:{self._trace_id}:{self._created_at}"
            root_hash = hashlib.sha256(root_seed.encode("utf-8")).hexdigest()
            initial_entry = LineageEntry(
                index=0,
                step_name="ROOT_INITIALIZATION",
                previous_hash="0" * 64,
                payload_hash=hashlib.sha256(json.dumps(self._input_payload, sort_keys=True).encode("utf-8")).hexdigest(),
                current_hash=root_hash,
            )
            self._lineage_chain.append(initial_entry)

    # --------------------------------------------------------------------------
    # Read-only Properties (Enforcing Immutability)
    # --------------------------------------------------------------------------
    @property
    def session_id(self) -> str:
        return self._session_id

    @property
    def tenant_id(self) -> str:
        return self._tenant_id

    @property
    def trace_id(self) -> str:
        return self._trace_id

    @property
    def depth_tier(self) -> str:
        return self._depth_tier

    @property
    def input_payload(self) -> Dict[str, Any]:
        return copy.deepcopy(self._input_payload)

    @property
    def votes(self) -> List[VoteRecord]:
        return list(self._votes)

    @property
    def lineage_chain(self) -> List[LineageEntry]:
        return list(self._lineage_chain)

    @property
    def flags(self) -> Dict[str, Any]:
        return copy.deepcopy(self._flags)

    @property
    def ephemeral_store(self) -> Dict[str, Any]:
        return copy.deepcopy(self._ephemeral_store)

    @property
    def metadata(self) -> Dict[str, Any]:
        return copy.deepcopy(self._metadata)

    @property
    def created_at(self) -> float:
        return self._created_at

    @property
    def is_purged(self) -> bool:
        return self._is_purged

    # --------------------------------------------------------------------------
    # Copy-on-Write Evolution Method
    # --------------------------------------------------------------------------
    def evolve(
        self,
        input_payload: Optional[Dict[str, Any]] = None,
        depth_tier: Optional[str] = None,
        votes: Optional[List[VoteRecord]] = None,
        lineage_chain: Optional[List[LineageEntry]] = None,
        flags: Optional[Dict[str, Any]] = None,
        ephemeral_store: Optional[Dict[str, Any]] = None,
        metadata: Optional[Dict[str, Any]] = None,
        is_purged: Optional[bool] = None,
    ) -> "ExecutionContext":
        """
        Creates a new immutable snapshot of the ExecutionContext.
        Preserves past state, chaining forward mutations.
        """
        if self._is_purged:
            raise RuntimeError("Cannot evolve a purged Zero-Retention ExecutionContext.")

        new_flags = dict(self._flags)
        if flags:
            new_flags.update(flags)

        new_ephemeral = dict(self._ephemeral_store)
        if ephemeral_store:
            new_ephemeral.update(ephemeral_store)

        new_metadata = dict(self._metadata)
        if metadata:
            new_metadata.update(metadata)

        return ExecutionContext(
            session_id=self._session_id,
            tenant_id=self._tenant_id,
            trace_id=self._trace_id,
            input_payload=dict(input_payload) if input_payload is not None else dict(self._input_payload),
            depth_tier=depth_tier or self._depth_tier,
            votes=votes if votes is not None else list(self._votes),
            lineage_chain=lineage_chain if lineage_chain is not None else list(self._lineage_chain),
            flags=new_flags,
            ephemeral_store=new_ephemeral,
            metadata=new_metadata,
            created_at=self._created_at,
            is_purged=is_purged if is_purged is not None else self._is_purged,
        )

    # --------------------------------------------------------------------------
    # Parliamentary Voting & Audit Helpers
    # --------------------------------------------------------------------------
    def with_vote(
        self,
        api: str,
        dimension: str,
        vote: str,
        confidence: float,
        reasoning: str = "",
        latency_ms: float = 0.0,
    ) -> "ExecutionContext":
        """
        Appends a parliament vote record and evolves the context.
        """
        new_votes = list(self._votes)
        record = VoteRecord(
            api=api,
            dimension=dimension,
            vote=vote,
            confidence=max(0.0, min(1.0, confidence)),
            reasoning=reasoning,
            latency_ms=latency_ms,
        )
        new_votes.append(record)
        return self.evolve(votes=new_votes)

    def with_votes(self, records: List[VoteRecord]) -> "ExecutionContext":
        """
        Appends a batch of parliament vote records in a single context evolution.
        Eliminates O(N) intermediate context allocations during 32-seat voting.
        """
        if not records:
            return self
        new_votes = list(self._votes)
        for v in records:
            new_votes.append(
                VoteRecord(
                    api=v.api,
                    dimension=v.dimension,
                    vote=v.vote,
                    confidence=max(0.0, min(1.0, v.confidence)),
                    reasoning=v.reasoning,
                    latency_ms=v.latency_ms,
                )
            )
        return self.evolve(votes=new_votes)

    def with_lineage_step(self, step_name: str, payload_data: Any) -> "ExecutionContext":
        """
        Appends a new cryptographically sealed step into the SHA-256 lineage chain.
        Ensures tamper-proof provenance for the Prove-It button.
        """
        latest_entry = self._lineage_chain[-1]
        prev_hash = latest_entry.current_hash
        payload_bytes = json.dumps(payload_data, sort_keys=True, default=str).encode("utf-8")
        payload_hash = hashlib.sha256(payload_bytes).hexdigest()

        combined = f"{prev_hash}:{step_name}:{payload_hash}".encode("utf-8")
        current_hash = hashlib.sha256(combined).hexdigest()

        new_entry = LineageEntry(
            index=len(self._lineage_chain),
            step_name=step_name,
            previous_hash=prev_hash,
            payload_hash=payload_hash,
            current_hash=current_hash,
        )
        new_chain = list(self._lineage_chain) + [new_entry]
        return self.evolve(lineage_chain=new_chain)

    def verify_lineage(self) -> bool:
        """
        Audits and verifies the entire cryptographic chain integrity.
        Returns True if perfectly untampered.
        """
        for i in range(1, len(self._lineage_chain)):
            entry = self._lineage_chain[i]
            prev = self._lineage_chain[i - 1]
            if entry.previous_hash != prev.current_hash:
                return False
            combined = f"{entry.previous_hash}:{entry.step_name}:{entry.payload_hash}".encode("utf-8")
            expected_hash = hashlib.sha256(combined).hexdigest()
            if entry.current_hash != expected_hash:
                return False
        return True

    # --------------------------------------------------------------------------
    # Zero Retention Purge (Rules 13, 14, 21)
    # --------------------------------------------------------------------------
    def purge(self) -> "ExecutionContext":
        """
        Zero-Retention Destructor:
        Overwrites volatile payload data and ephemeral store in RAM immediately.
        Leaves only the cryptographic audit digest and non-sensitive consensus metrics.
        """
        self._input_payload.clear()
        self._ephemeral_store.clear()
        return self.evolve(
            input_payload={"PURGED": True, "REASON": "Zero-Retention Inference Pass Complete"},
            ephemeral_store={},
            is_purged=True,
        )

    def to_summary_dict(self) -> Dict[str, Any]:
        """Produces a clean dictionary for UI / WebSocket inspection without leaking raw payloads."""
        return {
            "session_id": self._session_id,
            "trace_id": self._trace_id,
            "tenant_id": self._tenant_id,
            "depth_tier": self._depth_tier,
            "total_votes_cast": len(self._votes),
            "flags": self._flags,
            "lineage_depth": len(self._lineage_chain),
            "lineage_valid": self.verify_lineage(),
            "latest_lineage_hash": self._lineage_chain[-1].current_hash if self._lineage_chain else None,
            "is_purged": self._is_purged,
        }
