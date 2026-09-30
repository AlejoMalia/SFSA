"""
sfsa.cpe — Computational Provenance & Reuse Engine (CPE)
=======================================================
Tracks lineage, provenance metadata, numerical configurations, and error budgets for all computed results.
Enables intelligent approximate reuse and warm-starting: when an exact match does not exist in MATE,
CPE assesses whether a nearby prior solution is valid within local sensitivity bounds.

Part of SFSA (Standard Framework for Scientific Advancement)
Author & Protocol Creator: Alejo Malia
License: CC BY 4.0
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple
import math
import time


class ReuseType(str, Enum):
    EXACT_CACHE = "EXACT_CACHE"             # Identical semantic key and parameters
    APPROXIMATE_REUSE = "APPROXIMATE_REUSE" # Within parameter tolerance and low sensitivity
    WARM_START = "WARM_START"               # Initial seed for iterative solver
    FULL_COMPUTATION = "FULL_COMPUTATION"   # Incompatible provenance, recompute required


@dataclass
class ProvenanceRecord:
    """Complete provenance envelope for a scientific calculation."""
    record_id: str
    task_id: str
    model_version: str
    inputs: Dict[str, Any]
    output: Any
    numerical_method: str
    tolerances: Dict[str, float]
    dependencies: List[str]
    context: Dict[str, Any]
    timestamp: float = field(default_factory=time.time)
    reuse_count: int = 0


@dataclass
class ReuseAssessment:
    """Outcome of assessing whether a historical result can be reused."""
    reuse_type: ReuseType
    matched_record_id: Optional[str]
    delta_norm: float
    confidence: float
    value: Any
    rationale: str


class ComputationalProvenanceEngine:
    """
    CPE manages scientific provenance trails and grants approximate reuse permissions.
    """

    def __init__(self, approximate_tolerance: float = 0.02) -> None:
        self.approximate_tolerance = approximate_tolerance
        self.records: Dict[str, ProvenanceRecord] = {}

    def register_result(
        self,
        task_id: str,
        inputs: Dict[str, Any],
        output: Any,
        model_version: str = "1.0.0",
        numerical_method: str = "analytical_or_rk4",
        tolerances: Optional[Dict[str, float]] = None,
        dependencies: Optional[List[str]] = None,
        context: Optional[Dict[str, Any]] = None,
    ) -> ProvenanceRecord:
        """Stores provenance metadata for a verified scientific outcome."""
        rec_id = f"cpe_{task_id}_{len(self.records) + 1}_{int(time.time() * 1000)}"
        record = ProvenanceRecord(
            record_id=rec_id,
            task_id=task_id,
            model_version=model_version,
            inputs=dict(inputs),
            output=output,
            numerical_method=numerical_method,
            tolerances=tolerances or {},
            dependencies=dependencies or [],
            context=context or {},
        )
        self.records[rec_id] = record
        return record

    def assess_reuse(
        self,
        task_id: str,
        target_inputs: Dict[str, Any],
        required_model_version: Optional[str] = None,
        custom_tolerance: Optional[float] = None,
    ) -> ReuseAssessment:
        """
        Determines whether an existing solution can be reused exactly or approximately.
        """
        tol = custom_tolerance if custom_tolerance is not None else self.approximate_tolerance

        # Search existing records for this task
        candidates = [
            r for r in self.records.values()
            if r.task_id == task_id and (required_model_version is None or r.model_version == required_model_version)
        ]

        if not candidates:
            return ReuseAssessment(
                reuse_type=ReuseType.FULL_COMPUTATION,
                matched_record_id=None,
                delta_norm=1.0,
                confidence=0.0,
                value=None,
                rationale="No prior calculation exists for this task ID",
            )

        best_record: Optional[ProvenanceRecord] = None
        min_delta = float("inf")

        for r in candidates:
            # Check numerical similarity of shared keys
            keys = set(target_inputs.keys()).intersection(r.inputs.keys())
            if not keys:
                continue

            diffs = []
            for k in keys:
                v_target = target_inputs[k]
                v_cand = r.inputs[k]
                if isinstance(v_target, (int, float)) and isinstance(v_cand, (int, float)):
                    denom = max(abs(v_cand), 1.0)
                    diffs.append(abs(v_target - v_cand) / denom)
                elif v_target == v_cand:
                    diffs.append(0.0)
                else:
                    diffs.append(1.0)

            delta = max(diffs) if diffs else 1.0
            if delta < min_delta:
                min_delta = delta
                best_record = r

        if best_record is None:
            return ReuseAssessment(
                reuse_type=ReuseType.FULL_COMPUTATION,
                matched_record_id=None,
                delta_norm=1.0,
                confidence=0.0,
                value=None,
                rationale="Incompatible input signatures with prior records",
            )

        # 1. Exact match
        if min_delta < 1e-12:
            best_record.reuse_count += 1
            return ReuseAssessment(
                reuse_type=ReuseType.EXACT_CACHE,
                matched_record_id=best_record.record_id,
                delta_norm=0.0,
                confidence=1.0,
                value=best_record.output,
                rationale=f"Exact provenance match with record {best_record.record_id}",
            )

        # 2. Approximate reuse within tolerance
        if min_delta <= tol:
            best_record.reuse_count += 1
            conf = 1.0 - (min_delta / tol) * 0.2
            return ReuseAssessment(
                reuse_type=ReuseType.APPROXIMATE_REUSE,
                matched_record_id=best_record.record_id,
                delta_norm=min_delta,
                confidence=conf,
                value=best_record.output,
                rationale=f"Approximate reuse valid: delta ({min_delta:.4f}) <= tolerance ({tol:.4f})",
            )

        # 3. Warm start for iterative solvers
        if min_delta <= tol * 5.0:
            return ReuseAssessment(
                reuse_type=ReuseType.WARM_START,
                matched_record_id=best_record.record_id,
                delta_norm=min_delta,
                confidence=0.5,
                value=best_record.output,
                rationale=f"Candidate suitable for warm-starting iterative solver (delta={min_delta:.4f})",
            )

        return ReuseAssessment(
            reuse_type=ReuseType.FULL_COMPUTATION,
            matched_record_id=best_record.record_id,
            delta_norm=min_delta,
            confidence=0.0,
            value=None,
            rationale=f"Delta ({min_delta:.4f}) exceeds allowable tolerance ({tol:.4f})",
        )
