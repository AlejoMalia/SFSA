"""
sfsa.die — Discrepancy Intelligence Engine (DIE)
================================================
Analyzes discrepancies when parallel solvers, surrogate approximations, or multi-fidelity pathways
yield conflicting answers. Diagnoses root causes (numerical round-off, physical model divergence,
or regime breakdown) and decides whether to reconcile via low-cost correction or escalate to reference evaluation.

Part of SFSA (Standard Framework for Scientific Advancement)
Author & Protocol Creator: Alejo Malia
License: CC BY 4.0
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Tuple
import math


class DiscrepancyCause(str, Enum):
    NUMERICAL_TOLERANCE = "NUMERICAL_TOLERANCE"     # Residual precision noise / float roundoff (< 1%)
    MODELING_ASSUMPTION = "MODELING_ASSUMPTION"     # Real vs ideal assumptions / constitutive differences
    REGIME_BREAKDOWN = "REGIME_BREAKDOWN"           # Solver operated beyond physical validity window
    ERRONEOUS_CONVERGENCE = "ERRONEOUS_CONVERGENCE" # Iterative loop trapped in local spurious minimum


@dataclass
class DiscrepancyAnalysis:
    """Diagnostic outcome of comparing two distinct solution pathways."""
    source_a: str
    source_b: str
    value_a: float
    value_b: float
    relative_discrepancy: float
    probable_cause: DiscrepancyCause
    recommended_action: str
    reconciled_value: Optional[float]
    confidence: float


class DiscrepancyIntelligenceEngine:
    """
    DIE arbitrates multi-model discrepancies without human intervention.
    """

    def __init__(self, numerical_epsilon: float = 0.01, severe_discrepancy_threshold: float = 0.15) -> None:
        self.numerical_epsilon = numerical_epsilon
        self.severe_threshold = severe_discrepancy_threshold

    def analyze(
        self,
        source_a: str,
        value_a: float,
        source_b: str,
        value_b: float,
        reference_solver: Optional[Callable[[], float]] = None,
    ) -> DiscrepancyAnalysis:
        """
        Diagnoses root discrepancy mechanism between two computed outputs.
        """
        denom = max(abs(value_a), abs(value_b), 1e-9)
        rel_diff = abs(value_a - value_b) / denom

        # 1. Benign numerical round-off
        if rel_diff <= self.numerical_epsilon:
            avg_val = (value_a + value_b) / 2.0
            return DiscrepancyAnalysis(
                source_a=source_a,
                source_b=source_b,
                value_a=value_a,
                value_b=value_b,
                relative_discrepancy=rel_diff,
                probable_cause=DiscrepancyCause.NUMERICAL_TOLERANCE,
                recommended_action="Reconcile via weighted arithmetic mean; no reference recomputation required.",
                reconciled_value=avg_val,
                confidence=0.98,
            )

        # 2. Moderate divergence: likely differing modeling assumptions
        if rel_diff <= self.severe_threshold:
            return DiscrepancyAnalysis(
                source_a=source_a,
                source_b=source_b,
                value_a=value_a,
                value_b=value_b,
                relative_discrepancy=rel_diff,
                probable_cause=DiscrepancyCause.MODELING_ASSUMPTION,
                recommended_action="Apply constitutive correction factor or bounded envelope interval.",
                reconciled_value=(value_a + value_b) / 2.0,
                confidence=0.75,
            )

        # 3. Severe divergence: regime breakdown or solver failure -> trigger reference solver if present
        ref_val = reference_solver() if reference_solver else None
        return DiscrepancyAnalysis(
            source_a=source_a,
            source_b=source_b,
            value_a=value_a,
            value_b=value_b,
            relative_discrepancy=rel_diff,
            probable_cause=DiscrepancyCause.REGIME_BREAKDOWN,
            recommended_action=(
                f"Severe discrepancy ({rel_diff:.1%}). Escalated to reference solver: reconciled={ref_val}"
                if ref_val is not None
                else f"Severe discrepancy ({rel_diff:.1%}). Invalidation advised; escalate to high-fidelity reference."
            ),
            reconciled_value=ref_val if ref_val is not None else max(value_a, value_b),
            confidence=0.95 if ref_val is not None else 0.40,
        )
