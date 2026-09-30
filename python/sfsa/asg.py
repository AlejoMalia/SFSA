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

    def __init__(self, min_euclidean_distance: float = 0.05, uncertainty_weight: float = 0.6) -> None:
        self.min_euclidean_distance = min_euclidean_distance
        self.uncertainty_weight = uncertainty_weight
        self.evaluated_points: List[Dict[str, float]] = []
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
        """
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
    ) -> List[Dict[str, float]]:
        """
        Filters a dense candidate grid down to only the most informative points.
        """
        selected: List[Dict[str, float]] = []
        for cand in candidate_grid:
            assessment = self.evaluate_candidate(cand)
            if not assessment.skip_recommended:
                selected.append(cand)
                self.record_evaluation(cand, 0.0) # Mark as sampled in draft
            if max_budget and len(selected) >= max_budget:
                break
        return selected
