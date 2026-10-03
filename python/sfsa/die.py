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
    NUMERICAL_DISCRETIZATION = "NUMERICAL_DISCRETIZATION"  # Truncation error of the same model (step size, mesh, Euler vs RK4)
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
        same_model: bool = False,
        discretization_error: Optional[float] = None,
    ) -> DiscrepancyAnalysis:
        """
        Diagnoses root discrepancy mechanism between two computed outputs.

        A difference between two solutions of the *same* equations (``same_model=True``: different step size,
        mesh, or integrator such as Euler vs RK4) is discretization error, not a modeling assumption. It is
        also classified as discretization when the gap is within ``discretization_error`` (an absolute error
        estimate for the less accurate value, e.g. from :meth:`richardson`). Without either hint the previous
        behavior is unchanged.
        """
        if discretization_error is not None and not discretization_error >= 0:
            raise ValueError("discretization_error must be >= 0")
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

        # 1b. Same equations, different discretization: truncation error, not a different model
        within_estimate = discretization_error is not None and abs(value_a - value_b) <= discretization_error
        if (same_model and rel_diff <= self.severe_threshold) or within_estimate:
            return DiscrepancyAnalysis(
                source_a=source_a,
                source_b=source_b,
                value_a=value_a,
                value_b=value_b,
                relative_discrepancy=rel_diff,
                probable_cause=DiscrepancyCause.NUMERICAL_DISCRETIZATION,
                recommended_action=(
                    "Same model, different discretization: refine the step/mesh or extrapolate (Richardson); "
                    "prefer the higher-order / finer solution."
                ),
                reconciled_value=None,
                confidence=0.85 if within_estimate else 0.70,
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

    @staticmethod
    def richardson(value_coarse: float, value_fine: float, order: float, step_ratio: float = 2.0) -> Tuple[float, float]:
        """Richardson extrapolation for a method of convergence ``order`` run at steps ``h`` and ``h / step_ratio``.

        Returns ``(extrapolated_value, estimated_error_of_value_fine)``:
        ``v* = v_fine + (v_fine - v_coarse) / (r^p - 1)``; the error estimate is ``|v* - v_fine|``.
        Euler has ``order = 1``, RK4 ``order = 4``, central differences ``order = 2``.
        """
        if not order > 0 or not step_ratio > 1:
            raise ValueError("order must be > 0 and step_ratio > 1")
        extrapolated = value_fine + (value_fine - value_coarse) / (step_ratio ** order - 1.0)
        return extrapolated, abs(extrapolated - value_fine)

    def analyze_refinement(
        self,
        source_coarse: str,
        value_coarse: float,
        source_fine: str,
        value_fine: float,
        order: float,
        step_ratio: float = 2.0,
    ) -> DiscrepancyAnalysis:
        """Compare the same model at two resolutions and reconcile with Richardson extrapolation.

        The discrepancy is, by construction, discretization error: it is reported as such, with the
        extrapolated value as the reconciled result and the estimated error of the fine solution in the action.
        """
        extrapolated, err = self.richardson(value_coarse, value_fine, order, step_ratio)
        denom = max(abs(value_coarse), abs(value_fine), 1e-9)
        small = err / max(abs(extrapolated), 1e-9) <= self.numerical_epsilon
        return DiscrepancyAnalysis(
            source_a=source_coarse,
            source_b=source_fine,
            value_a=value_coarse,
            value_b=value_fine,
            relative_discrepancy=abs(value_coarse - value_fine) / denom,
            probable_cause=DiscrepancyCause.NUMERICAL_DISCRETIZATION,
            recommended_action=(
                f"Richardson extrapolation (order {order:g}, ratio {step_ratio:g}): estimated error of '{source_fine}' "
                f"is {err:.3g}" + ("; resolved to the numerical tolerance." if small else "; refine further.")
            ),
            reconciled_value=extrapolated,
            confidence=0.90 if small else 0.65,
        )
