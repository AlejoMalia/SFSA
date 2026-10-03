"""
sfsa.asg — Adaptive Sampling & Experimentation Engine (ASG)
==========================================================
Replaces brute-force multidimensional grid sweeps with information-theoretic adaptive sampling.
Prioritizes unexplored parameter subspaces characterized by high gradient, sensitivity, or epistemic
uncertainty, while skipping redundant evaluations in flat or well-characterized regimes.

Part of SFSA (Standard Framework for Scientific Advancement)
Author & Protocol Creator: Alejo Malia
License: CC BY 4.0
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, Tuple
import math


@dataclass
class SampleCandidate:
    """A proposed parameter point with estimated acquisition utility."""
    point: Dict[str, float]
    information_gain: float
    distance_to_nearest: float
    estimated_uncertainty: float
    skip_recommended: bool
    rationale: str


@dataclass
class SamplingCampaign:
    """Summary of an adaptive sampling campaign."""
    total_grid_points_possible: int
    points_evaluated: int
    points_skipped: int
    points_saved_pct: float
    active_samples: List[Dict[str, float]] = field(default_factory=list)


class AdaptiveSamplingEngine:
    """
    ASG Engine samples only where knowledge or dynamics vary significantly.
    Integrates with MATE cache and FLN layer dependencies.
    """

    def __init__(
        self,
        min_euclidean_distance: float = 0.05,
        uncertainty_weight: float = 0.6,
        uncertainty_estimator: Optional[Callable[[Dict[str, float]], float]] = None,
        gradient_estimator: Optional[Callable[[Dict[str, float]], float]] = None,
    ) -> None:
        self.min_euclidean_distance = min_euclidean_distance
        self.uncertainty_weight = uncertainty_weight
        # Default estimators used by evaluate_candidate / filter_grid when none is passed per call.
        self.uncertainty_estimator = uncertainty_estimator
        self.gradient_estimator = gradient_estimator
        self.evaluated_points: List[Dict[str, float]] = []
        # NaN marks a point that was selected but whose response has not been recorded yet.
        self.point_values: List[float] = []

    def record_evaluation(self, point: Dict[str, float], value: float) -> None:
        """Stores an evaluated point and its response value."""
        self.evaluated_points.append(dict(point))
        self.point_values.append(value)

    def _normalize_dist(self, p1: Dict[str, float], p2: Dict[str, float]) -> float:
        """Calculates Euclidean distance over shared normalized keys."""
        shared_keys = set(p1.keys()).intersection(p2.keys())
        if not shared_keys:
            return 1.0
        sq_sum = sum((p1[k] - p2[k]) ** 2 for k in shared_keys)
        return math.sqrt(sq_sum) / math.sqrt(len(shared_keys))

    def evaluate_candidate(
        self,
        candidate_point: Dict[str, float],
        uncertainty_estimator: Optional[Callable[[Dict[str, float]], float]] = None,
        gradient_estimator: Optional[Callable[[Dict[str, float]], float]] = None,
    ) -> SampleCandidate:
        """
        Assesses whether a candidate point merits computational evaluation.

        ``uncertainty_estimator`` / ``gradient_estimator`` default to those given at construction.
        """
        uncertainty_estimator = uncertainty_estimator or self.uncertainty_estimator
        gradient_estimator = gradient_estimator or self.gradient_estimator
        if not self.evaluated_points:
            return SampleCandidate(
                point=candidate_point,
                information_gain=1.0,
                distance_to_nearest=1.0,
                estimated_uncertainty=1.0,
                skip_recommended=False,
                rationale="Initial baseline point in unexplored parameter space",
            )

        # Distance to nearest already sampled point
        min_dist = min(self._normalize_dist(candidate_point, p) for p in self.evaluated_points)

        unc = uncertainty_estimator(candidate_point) if uncertainty_estimator else min(1.0, min_dist * 2.0)
        grad = gradient_estimator(candidate_point) if gradient_estimator else 0.5

        # Acquisition utility combines distance, uncertainty, and expected gradient
        utility = (1.0 - self.uncertainty_weight) * (min_dist * grad) + self.uncertainty_weight * unc

        skip = min_dist < self.min_euclidean_distance and unc < 0.1
        rationale = (
            f"Skip recommended: point is within {min_dist:.4f} < {self.min_euclidean_distance} of known sample with low uncertainty"
            if skip
            else f"Sample required: information gain {utility:.4f} (min_dist={min_dist:.3f}, unc={unc:.3f})"
        )

        return SampleCandidate(
            point=candidate_point,
            information_gain=utility,
            distance_to_nearest=min_dist,
            estimated_uncertainty=unc,
            skip_recommended=skip,
            rationale=rationale,
        )

    def filter_grid(
        self,
        candidate_grid: List[Dict[str, float]],
        max_budget: Optional[int] = None,
        uncertainty_estimator: Optional[Callable[[Dict[str, float]], float]] = None,
        gradient_estimator: Optional[Callable[[Dict[str, float]], float]] = None,
    ) -> List[Dict[str, float]]:
        """
        Filters a dense candidate grid down to only the most informative points.

        The uncertainty and gradient estimators (per call, or the ones given at construction) drive both the
        skip decision and, under a budget, the ranking: without a budget the grid is scanned in order and every
        non-redundant point is kept; with ``max_budget`` the points are chosen greedily by acquisition utility
        (re-evaluated after every pick, so the next pick accounts for the ones already selected). A budget of 0
        selects nothing; a negative budget is an error. Selected points are registered with a NaN response until
        :meth:`record_evaluation` / the caller supplies the real value.
        """
        if max_budget is not None and max_budget < 0:
            raise ValueError("max_budget must be >= 0")
        selected: List[Dict[str, float]] = []
        if max_budget == 0:
            return selected
        if max_budget is None:
            for cand in candidate_grid:
                assessment = self.evaluate_candidate(cand, uncertainty_estimator, gradient_estimator)
                if not assessment.skip_recommended:
                    selected.append(cand)
                    self.record_evaluation(cand, math.nan)
            return selected
        remaining = list(candidate_grid)
        while remaining and len(selected) < max_budget:
            scored = [(self.evaluate_candidate(c, uncertainty_estimator, gradient_estimator), i)
                      for i, c in enumerate(remaining)]
            viable = [(a, i) for a, i in scored if not a.skip_recommended]
            if not viable:
                break
            best, idx = max(viable, key=lambda t: (t[0].information_gain, -t[1]))   # ties: earliest in the grid
            selected.append(remaining.pop(idx))
            self.record_evaluation(best.point, math.nan)
        return selected
