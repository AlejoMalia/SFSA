"""
sfsa.mate — MATE Engine (Multi-Dimensional Acceleration & Trajectory Estimation)
=================================================================================
Generic scientific memoization, projection, and early-abort engine.
Prevents executing calculations to the end when intermediate states or boundary
conditions already dictate feasibility or convergence.

Part of SFSA (Standard Framework for Scientific Advancement)
Author & TRIADA Protocol Creator: Alejo Malia
License: CC BY 4.0
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Tuple
import hashlib
import json
import math
import time


class MATEStatus(str, Enum):
    """Execution status resulting from MATE analysis."""
    R1_EXACT = "R1_EXACT"          # Solved exactly or retrieved from memoized cache
    R2_PROJECTED = "R2_PROJECTED"  # Projected via closed-form approximation without dense iteration
    R3_INFEASIBLE = "R3_INFEASIBLE" # Aborted early: physical, mathematical, or boundary constraint violated


@dataclass
class MATEResult:
    """Outcome of a MATE-evaluated computation."""
    status: MATEStatus
    value: Any
    cached: bool = False
    compute_time_saved_pct: float = 0.0
    elapsed_seconds: float = 0.0
    diagnostic_message: str = ""
    intermediate_checkpoints: List[Dict[str, Any]] = field(default_factory=list)


class MATEEngine:
    """
    Domain-neutral MATE computation engine.
    Combines semantic invariant caching with early-abort boundary evaluators.
    """

    def __init__(self, cache_precision_decimals: int = 6) -> None:
        self.cache_precision = cache_precision_decimals
        self._cache: Dict[str, Any] = {}
        self._metrics = {
            "total_queries": 0,
            "cache_hits": 0,
            "early_aborts": 0,
            "full_computes": 0,
            "estimated_cpu_seconds_saved": 0.0,
        }

    def _hash_key(self, namespace: str, *args: Any, **kwargs: Any) -> str:
        """Generates a deterministic hash for any combination of scientific arguments."""
        def normalize(obj: Any) -> Any:
            if isinstance(obj, float):
                if math.isnan(obj) or math.isinf(obj):
                    return str(obj)
                return round(obj, self.cache_precision)
            if isinstance(obj, (int, str, bool)) or obj is None:
                return obj
            if isinstance(obj, (list, tuple)):
                return [normalize(x) for x in obj]
            if isinstance(obj, dict):
                return {str(k): normalize(v) for k, v in sorted(obj.items())}
            if hasattr(obj, "__dict__"):
                return normalize(obj.__dict__)
            return str(obj)

        normalized_data = {
            "ns": namespace,
            "args": [normalize(a) for a in args],
            "kwargs": {str(k): normalize(v) for k, v in sorted(kwargs.items())}
        }
        serialized = json.dumps(normalized_data, sort_keys=True, default=str)
        return hashlib.sha256(serialized.encode("utf-8")).hexdigest()

    def memoized_get(self, key: str) -> Optional[Any]:
        """Retrieves a cached result if present."""
        return self._cache.get(key)

    def memoized_set(self, key: str, value: Any) -> None:
        """Stores a computed result in cache."""
        self._cache[key] = value

    def compute_projected(
        self,
        task_id: str,
        inputs: Dict[str, Any],
        solver: Callable[[Dict[str, Any]], Any],
        boundary_validator: Optional[Callable[[Dict[str, Any]], Tuple[bool, str]]] = None,
        intermediate_check: Optional[Callable[[Dict[str, Any]], Tuple[bool, str]]] = None,
        estimated_heavy_cost_s: float = 0.05,
    ) -> MATEResult:
        """
        Executes a calculation with MATE optimization:
        1. Boundary Pre-check: Abort before running if boundary is violated.
        2. Memoization: Return in O(1) if already computed.
        3. Intermediate Guard: Verify mid-state without running to completion.
        4. Solve & Cache: Execute solver and store.
        """
        t0 = time.perf_counter()
        self._metrics["total_queries"] += 1

        # 1. Boundary Pre-Check (Early Exit R3)
        if boundary_validator is not None:
            is_valid, reason = boundary_validator(inputs)
            if not is_valid:
                self._metrics["early_aborts"] += 1
                self._metrics["estimated_cpu_seconds_saved"] += estimated_heavy_cost_s
                return MATEResult(
                    status=MATEStatus.R3_INFEASIBLE,
                    value=None,
                    cached=False,
                    compute_time_saved_pct=99.9,
                    elapsed_seconds=time.perf_counter() - t0,
                    diagnostic_message=f"Early abort by boundary validator: {reason}",
                )

        # 2. Cache Lookup (O(1) Exact R1)
        cache_key = self._hash_key(task_id, inputs)
        cached_val = self.memoized_get(cache_key)
        if cached_val is not None:
            self._metrics["cache_hits"] += 1
            self._metrics["estimated_cpu_seconds_saved"] += estimated_heavy_cost_s
            return MATEResult(
                status=MATEStatus.R1_EXACT,
                value=cached_val,
                cached=True,
                compute_time_saved_pct=99.5,
                elapsed_seconds=time.perf_counter() - t0,
                diagnostic_message="Value retrieved from MATE invariant cache",
            )

        # 3. Intermediate Feasibility Check
        if intermediate_check is not None:
            is_feasible, reason = intermediate_check(inputs)
            if not is_feasible:
                self._metrics["early_aborts"] += 1
                self._metrics["estimated_cpu_seconds_saved"] += (estimated_heavy_cost_s * 0.8)
                return MATEResult(
                    status=MATEStatus.R3_INFEASIBLE,
                    value=None,
                    cached=False,
                    compute_time_saved_pct=80.0,
                    elapsed_seconds=time.perf_counter() - t0,
                    diagnostic_message=f"Aborted at intermediate checkpoint: {reason}",
                )

        # 4. Actual Solver Execution
        self._metrics["full_computes"] += 1
        result_value = solver(inputs)
        self.memoized_set(cache_key, result_value)

        elapsed = time.perf_counter() - t0
        return MATEResult(
            status=MATEStatus.R1_EXACT,
            value=result_value,
            cached=False,
            compute_time_saved_pct=0.0,
            elapsed_seconds=elapsed,
            diagnostic_message="Computed freshly and cached in MATE index",
        )

    def clear_cache(self) -> None:
        """Empties the cache."""
        self._cache.clear()

    @property
    def metrics(self) -> Dict[str, Any]:
        """Performance and compute reduction metrics."""
        return dict(self._metrics)
