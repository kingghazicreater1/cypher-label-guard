# ==============================================================================
# 🔒 SACRED FILE 4 OF 4: core/orchestrator.py
# RULE 8: orchestrator.py IS SACRED.
# Main Conductor — coordinates context bus through feature pipelines.
# RULE 9: Circuit Breaker — 3 failures = 30s cooldown, 5 = isolate feature.
# RULE 10: Graceful Degradation — Parliament -> Solo -> Rule-based fallback.
# RULE 11: Adaptive Timeout per API call.
# RULE 12: Tiered Depth Scaling (Fast 2s, Standard 8s, Deep 20s).
# RULE 13: Zero-Retention Purge at conclusion.
# ==============================================================================

import asyncio
import logging
import time
from typing import Any, Callable, Coroutine, Dict, List, Optional

from core.context import ExecutionContext
from core.registry import FeatureRegistry, registry

logger = logging.getLogger("CYPHER_LABEL_GUARD.Orchestrator")


class CircuitBreaker:
    """
    Implements Rule 9:
    - 3 failures = 30s cooldown (STATE: OPEN)
    - 5 failures = Feature shutdown (STATE: ISOLATED)
    - System never crashes.
    """
    def __init__(self, target_id: str, cooldown_seconds: float = 30.0, max_failures: int = 5):
        self.target_id = target_id
        self.cooldown_seconds = cooldown_seconds
        self.max_failures = max_failures
        self.failure_count = 0
        self.last_failure_time = 0.0
        self.state = "CLOSED"  # CLOSED, OPEN (cooldown), ISOLATED (shutdown)

    def record_success(self):
        if self.state in ("OPEN", "HALF_OPEN", "ISOLATED"):
            logger.info(f"Circuit Breaker for {self.target_id} recovered to CLOSED (State was {self.state}).")
        self.failure_count = 0
        self.state = "CLOSED"

    def record_failure(self):
        self.failure_count += 1
        self.last_failure_time = time.time()
        if self.failure_count >= self.max_failures:
            self.state = "ISOLATED"
            logger.critical(f"Circuit Breaker ISOLATED for {self.target_id} (5 consecutive failures). Entering extended cooldown.")
        elif self.failure_count >= 3:
            self.state = "OPEN"
            logger.warning(f"Circuit Breaker OPEN for {self.target_id}. Entering 30s cooldown.")

    def is_available(self) -> bool:
        if self.state == "ISOLATED":
            # Self-healing: After extended cooldown (60s), allow a HALF_OPEN trial request
            if time.time() - self.last_failure_time > (self.cooldown_seconds * 2):
                self.state = "HALF_OPEN"
                logger.info(f"Circuit Breaker for {self.target_id} entering HALF_OPEN trial after isolation cooldown.")
                return True
            return False
        if self.state == "OPEN":
            if time.time() - self.last_failure_time > self.cooldown_seconds:
                self.state = "HALF_OPEN"
                return True
            return False
        return True


class PipelineOrchestrator:
    """
    Main Conductor executing features across categories according to the Golden Flow.
    """

    def __init__(self, feature_registry: Optional[FeatureRegistry] = None):
        self.registry = feature_registry or registry
        self.circuit_breakers: Dict[str, CircuitBreaker] = {}
        self._event_listeners: List[Callable[[str, ExecutionContext], Coroutine[Any, Any, None]]] = []

        # Depth Tier Timeouts (Rule 11 & 12)
        self.depth_budgets = {
            "Fast": 2.0,       # 2 seconds
            "Standard": 8.0,   # 8 seconds
            "Deep": 20.0,      # 15-20 seconds
        }

    def add_event_listener(self, callback: Callable[[str, ExecutionContext], Coroutine[Any, Any, None]]):
        """Allows dashboard / WebSocket services to stream live pipeline telemetry."""
        self._event_listeners.append(callback)

    async def _emit_event(self, event_type: str, context: ExecutionContext):
        for listener in self._event_listeners:
            try:
                await listener(event_type, context)
            except Exception as e:
                logger.error(f"Error in event listener for {event_type}: {e}")

    def get_circuit_breaker(self, target_id: str) -> CircuitBreaker:
        if target_id not in self.circuit_breakers:
            self.circuit_breakers[target_id] = CircuitBreaker(target_id)
        return self.circuit_breakers[target_id]

    async def execute_feature_safe(
        self,
        feature_id: str,
        context: ExecutionContext,
        timeout: Optional[float] = None,
    ) -> ExecutionContext:
        """
        Safely executes an individual feature with circuit breaking, timeout, and lineage hashing.
        """
        feature = self.registry.get_feature(feature_id)
        if not feature or not feature.is_enabled():
            return context

        breaker = self.get_circuit_breaker(feature_id)
        if not breaker.is_available():
            logger.warning(f"Skipping {feature_id}: Circuit breaker is {breaker.state}.")
            return context

        start_time = time.time()
        effective_timeout = timeout or self.depth_budgets.get(context.depth_tier, 8.0)

        try:
            logger.debug(f"Executing feature: {feature_id} (Timeout: {effective_timeout}s)")
            evolved_context = await asyncio.wait_for(feature.execute(context), timeout=effective_timeout)
            breaker.record_success()
            elapsed_ms = (time.time() - start_time) * 1000.0

            # Cryptographically record lineage step
            evolved_context = evolved_context.with_lineage_step(
                step_name=f"FEATURE_EXECUTION_{feature_id}",
                payload_data={"elapsed_ms": elapsed_ms, "status": "SUCCESS"}
            )
            await self._emit_event("FEATURE_COMPLETE", evolved_context)
            return evolved_context

        except asyncio.TimeoutError:
            breaker.record_failure()
            logger.error(f"Feature {feature_id} timed out after {effective_timeout}s.")
            return context.with_lineage_step(
                step_name=f"FEATURE_TIMEOUT_{feature_id}",
                payload_data={"status": "TIMEOUT", "effective_timeout": effective_timeout}
            )
        except Exception as e:
            breaker.record_failure()
            logger.error(f"Feature {feature_id} threw an error: {e}", exc_info=True)
            return context.with_lineage_step(
                step_name=f"FEATURE_ERROR_{feature_id}",
                payload_data={"status": "ERROR", "error": str(e)}
            )

    # Canonical Golden Pipeline Flow (Enforces strict dependency sequencing across all 38 features)
    GOLDEN_PIPELINE_ORDER = [
        # Stage 1: Ingestion & Multi-Modal Routing
        "feat_34_multimodal_router",
        "feat_37_video_sampler",
        "feat_35_vision_connector",
        "feat_36_audio_pipeline",

        # Stage 2: Speed, Pools & Volatile Memory Pre-allocation
        "feat_14_connection_pool",
        "feat_13_async_io",
        "feat_11_tiered_depth",
        "feat_12_adaptive_timeout",
        "feat_15_zerocopy_parser",
        "feat_16_preallocated_memory",
        "feat_17_multitenant",

        # Stage 3: Baseline Calibration & Dimension Profiling
        "feat_01_semantic_saturation",
        "feat_02_nshot_calibration",
        "feat_05_adaptive_dimension",

        # Stage 4: 32-Vote Parliamentary Consensus Execution
        "feat_04_subspace_voting",

        # Stage 5: Entropy Masking, Attribution & Sanity Checks
        "feat_03_entropic_masking",
        "feat_06_token_attribution",
        "feat_07_vector_collapse_guard",
        "feat_08_adversarial_sanity",
        "feat_09_weighted_tiebreak",
        "feat_10_roundtrip_fidelity",

        # Stage 6: Lifecycle, Humility & Drift Witness Marks
        "feat_24_drift_witness_marks",
        "feat_25_epistemic_humility",
        "feat_26_bitwise_reproducibility",
        "feat_27_night_batch_processor",

        # Stage 7: Privacy, Echo Cancellation & Lineage Seal
        "feat_19_ramonly_mmap",
        "feat_20_echo_cancellation",
        "feat_22_immutable_lineage",
        "feat_23_stateless_embedding",
        "feat_21_panic_salt_flush",
        "feat_18_zeroretention_pass",

        # Stage 8: Output Formatting, 4x8 Grid & Prove-It Dossier
        "feat_28_graceful_degradation",
        "feat_30_elastic_scaling",
        "feat_33_anthropological_module",
        "feat_29_threetier_human",
        "feat_31_live_dashboard",
        "feat_32_prove_it_button",
        "feat_38_unified_output",
    ]

    async def run_pipeline(
        self,
        initial_context: ExecutionContext,
        feature_pipeline_order: Optional[List[str]] = None,
    ) -> ExecutionContext:
        """
        Executes the entire end-to-end pipeline through the 6 Categories
        strictly in the Golden Pipeline Order.
        """
        context = initial_context
        pipeline_start = time.time()
        logger.info(f"Starting pipeline execution for Trace ID: {context.trace_id} (Depth: {context.depth_tier})")
        await self._emit_event("PIPELINE_START", context)

        # Use explicitly provided order or the canonical Golden Flow
        pipeline_sequence = feature_pipeline_order or self.GOLDEN_PIPELINE_ORDER

        for feat_id in pipeline_sequence:
            context = await self.execute_feature_safe(feat_id, context)


        # Rule 10: Graceful Degradation Check
        total_votes = len(context.votes)
        if total_votes < 16:
            # Degrade to Rule-Based Fallback if quorum cannot be achieved
            logger.warning(f"Total votes {total_votes} below quorum threshold. Activating Graceful Degradation.")
            new_flags = dict(context.flags)
            new_flags["degradation_tier"] = "Rule-Based Fallback" if total_votes == 0 else "Solo API"
            new_flags["human_review_required"] = True
            context = context.evolve(flags=new_flags)

        total_elapsed = time.time() - pipeline_start
        context = context.evolve(metadata={"total_elapsed_seconds": total_elapsed})
        logger.info(f"Pipeline completed in {total_elapsed:.3f}s. Total Votes Cast: {len(context.votes)}")

        # Seal final lineage hash
        context = context.with_lineage_step(
            step_name="PIPELINE_FINAL_SEAL",
            payload_data={
                "total_votes": len(context.votes),
                "flags": context.flags,
                "total_elapsed": total_elapsed,
            }
        )

        await self._emit_event("PIPELINE_FINISH", context)

        # Rule 13: Zero-Retention Purge (Erases raw payload from RAM)
        purged_context = context.purge()
        logger.info(f"Zero-Retention Purge executed successfully for Trace ID: {context.trace_id}")
        return purged_context


# Global Orchestrator Instance
orchestrator = PipelineOrchestrator()
