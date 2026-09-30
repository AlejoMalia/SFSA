"""
sfsa.amf — Adaptive Multi-Fidelity Engine (AMF)
==============================================
Decides and routes computations across varying model fidelity levels (cheap vs. intermediate vs. expensive).
Accepts lower-fidelity approximations when estimated uncertainty is within calibrated scientific tolerances,
escalating to high-fidelity solvers only when required.

Part of SFSA (Standard Framework for Scientific Advancement)
Author & Protocol Creator: Alejo Malia
License: CC BY 4.0
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Dict, List, Optional
import time


class FidelityLevel(str, Enum):
    CHEAP = "CHEAP"               # Low computational cost, surrogate or closed-form approximation
    INTERMEDIATE = "INTERMEDIATE" # Balanced numerical simulation or reduced-order model
    HIGH = "HIGH"                 # Full-physics / dense numerical integration or fine mesh


@dataclass
class FidelityDecision:
    """Record of a multi-fidelity routing decision and its outcome."""
    task_id: str
    selected_level: FidelityLevel
    escalated: bool
    estimated_uncertainty: float
    uncertainty_tolerance: float
    execution_time_ms: float
    value: Any
    compute_saved_ratio: float    # Relative savings compared to high-fidelity benchmark
    rationale: str


class AdaptiveMultiFidelityEngine:
    """
    AMF Engine manages hierarchical fidelity execution to avoid wasteful high-cost evaluations.
    Integrates directly with FLN, MATE, ICR, and TRIADA.
    """

    def __init__(self, default_tolerance: float = 0.05) -> None:
        self.default_tolerance = default_tolerance
        self.history: List[FidelityDecision] = []
        self.total_evaluations: int = 0
        self.cheap_accepted_count: int = 0
        self.escalations_count: int = 0

    def evaluate(
        self,
        task_id: str,
        inputs: Dict[str, Any],
        cheap_solver: Callable[[Dict[str, Any]], Tuple[Any, float]],       # Returns (value, uncertainty)
        expensive_solver: Callable[[Dict[str, Any]], Any],                  # High-fidelity ground truth
        intermediate_solver: Optional[Callable[[Dict[str, Any]], Tuple[Any, float]]] = None,
        tolerance: Optional[float] = None,
        benchmark_cost_factor: float = 100.0,                              # Expected cost ratio of expensive / cheap
    ) -> FidelityDecision:
        """
        Executes multi-fidelity evaluation with adaptive uncertainty gating.
        """
        tol = tolerance if tolerance is not None else self.default_tolerance
        self.total_evaluations += 1

        t0 = time.perf_counter()
        cheap_val, cheap_unc = cheap_solver(inputs)
        t_cheap = (time.perf_counter() - t0) * 1000.0

        if cheap_unc <= tol:
            self.cheap_accepted_count += 1
            savings = 1.0 - (1.0 / max(benchmark_cost_factor, 1.0))
            decision = FidelityDecision(
                task_id=task_id,
                selected_level=FidelityLevel.CHEAP,
                escalated=False,
                estimated_uncertainty=cheap_unc,
                uncertainty_tolerance=tol,
                execution_time_ms=t_cheap,
                value=cheap_val,
                compute_saved_ratio=savings,
                rationale=f"Cheap approximation uncertainty ({cheap_unc:.4f}) within tolerance ({tol:.4f})",
            )
            self.history.append(decision)
            return decision

        # If intermediate solver exists, try intermediate before full high-fidelity
        if intermediate_solver is not None:
            t_int0 = time.perf_counter()
            int_val, int_unc = intermediate_solver(inputs)
            t_int = (time.perf_counter() - t_int0) * 1000.0 + t_cheap
            if int_unc <= tol:
                self.cheap_accepted_count += 1
                savings = 1.0 - (benchmark_cost_factor * 0.2 / max(benchmark_cost_factor, 1.0))
                decision = FidelityDecision(
                    task_id=task_id,
                    selected_level=FidelityLevel.INTERMEDIATE,
                    escalated=True,
                    estimated_uncertainty=int_unc,
                    uncertainty_tolerance=tol,
                    execution_time_ms=t_int,
                    value=int_val,
                    compute_saved_ratio=max(0.0, savings),
                    rationale=f"Escalated to intermediate level. Uncertainty ({int_unc:.4f}) accepted",
                )
                self.history.append(decision)
                return decision

        # Escalate to high fidelity
        self.escalations_count += 1
        t_exp0 = time.perf_counter()
        exp_val = expensive_solver(inputs)
        t_total = (time.perf_counter() - t_exp0) * 1000.0 + t_cheap

        decision = FidelityDecision(
            task_id=task_id,
            selected_level=FidelityLevel.HIGH,
            escalated=True,
            estimated_uncertainty=0.0,
            uncertainty_tolerance=tol,
            execution_time_ms=t_total,
            value=exp_val,
            compute_saved_ratio=0.0,
            rationale=f"Escalated to high fidelity. Cheap model uncertainty ({cheap_unc:.4f}) exceeded tolerance ({tol:.4f})",
        )
        self.history.append(decision)
        return decision

    def summary(self) -> Dict[str, Any]:
        """Provides operational statistics on multi-fidelity routing."""
        ratio = (self.cheap_accepted_count / self.total_evaluations) if self.total_evaluations > 0 else 0.0
        return {
            "total_evaluations": self.total_evaluations,
            "cheap_accepted": self.cheap_accepted_count,
            "escalations": self.escalations_count,
            "acceptance_ratio": ratio,
        }
