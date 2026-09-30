"""
sfsa.uas — Uncertainty-Aware Stopping Engine (UAS)
=================================================
Prevents wasteful iterative computation by asking whether residual numerical error or epistemic
uncertainty can alter the scientific conclusion. Stops iterative algorithms once confidence
bounds guarantee invariant qualitative decisions, avoiding superfluous convergence steps.

Part of SFSA (Standard Framework for Scientific Advancement)
Author & Protocol Creator: Alejo Malia
License: CC BY 4.0
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional
import math


@dataclass
class StoppingEvaluation:
    """Outcome of assessing early termination for an iterative process."""
    iteration: int
    current_value: float
    current_residual: float
    current_uncertainty: float
    target_tolerance: float
    should_stop: bool
    iterations_saved: int
    rationale: str


class UncertaintyAwareStoppingEngine:
    """
    UAS Engine evaluates iteration health and aborts once scientific significance is established.
    """

    def __init__(self, target_tolerance: float = 1e-4, min_iterations_before_stop: int = 3) -> None:
        self.target_tolerance = target_tolerance
        self.min_iterations_before_stop = min_iterations_before_stop

    def evaluate_step(
        self,
        iteration: int,
        current_value: float,
        previous_value: Optional[float],
        max_planned_iterations: int,
        scientific_threshold: Optional[float] = None,       # Critical boundary for hypothesis (e.g. phase change)
        estimated_uncertainty: Optional[float] = None,
        custom_tolerance: Optional[float] = None,
    ) -> StoppingEvaluation:
        """
        Assesses whether an ongoing iterative loop can stop early with scientific rigor.
        """
        tol = custom_tolerance if custom_tolerance is not None else self.target_tolerance
        residual = abs(current_value - previous_value) if previous_value is not None else 1.0
        unc = estimated_uncertainty if estimated_uncertainty is not None else residual

        # 1. Do not stop before minimum baseline steps
        if iteration < self.min_iterations_before_stop:
            return StoppingEvaluation(
                iteration=iteration,
                current_value=current_value,
                current_residual=residual,
                current_uncertainty=unc,
                target_tolerance=tol,
                should_stop=False,
                iterations_saved=0,
                rationale="Under minimum initial iterations threshold",
            )

        # 2. Check if residual is already below scientific tolerance
        if residual <= tol and unc <= tol:
            saved = max(0, max_planned_iterations - iteration)
            return StoppingEvaluation(
                iteration=iteration,
                current_value=current_value,
                current_residual=residual,
                current_uncertainty=unc,
                target_tolerance=tol,
                should_stop=True,
                iterations_saved=saved,
                rationale=f"Tolerance satisfied: residual {residual:.2e} <= {tol:.2e}",
            )

        # 3. Check hypothesis threshold stability (e.g., value is safely far from critical threshold)
        if scientific_threshold is not None:
            distance_to_threshold = abs(current_value - scientific_threshold)
            # If distance to threshold is much greater than uncertainty (e.g. 5x), conclusion cannot change
            if distance_to_threshold > 5.0 * unc and residual < 10.0 * tol:
                saved = max(0, max_planned_iterations - iteration)
                return StoppingEvaluation(
                    iteration=iteration,
                    current_value=current_value,
                    current_residual=residual,
                    current_uncertainty=unc,
                    target_tolerance=tol,
                    should_stop=True,
                    iterations_saved=saved,
                    rationale=(
                        f"Scientific conclusion invariant: distance to critical boundary ({distance_to_threshold:.3f}) "
                        f"exceeds 5x uncertainty ({unc:.3f})"
                    ),
                )

        return StoppingEvaluation(
            iteration=iteration,
            current_value=current_value,
            current_residual=residual,
            current_uncertainty=unc,
            target_tolerance=tol,
            should_stop=False,
            iterations_saved=0,
            rationale=f"Continuing: residual ({residual:.2e}) > target tolerance ({tol:.2e})",
        )
