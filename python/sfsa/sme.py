"""
sfsa.sme — Surrogate Modeling Engine (SME)
==========================================
Synthesizes lightweight, compact response surface models (Radial Basis Functions / Multiquadric / IDW)
in real-time from evaluated high-fidelity points. Provides the automatic "cheap model" required by AMF,
allowing non-ML researchers to benefit from multi-fidelity acceleration without writing surrogates manually.

Part of SFSA (Standard Framework for Scientific Advancement)
Author & Protocol Creator: Alejo Malia
License: CC BY 4.0
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, Tuple
import math


@dataclass
class SurrogateModel:
    """A fitted lightweight surrogate response surface."""
    feature_names: List[str]
    sample_points: List[Dict[str, float]]
    sample_values: List[float]
    rbf_epsilon: float = 1.0

    def predict(self, point: Dict[str, float]) -> Tuple[float, float]:
        """
        Predicts response value and epistemic uncertainty (distance-to-samples metric).
        Returns (predicted_value, estimated_uncertainty).
        """
        if not self.sample_points:
            return 0.0, 1.0

        # Compute Euclidean distances to all known samples
        distances = []
        for p in self.sample_points:
            sq = sum((point[k] - p[k]) ** 2 for k in self.feature_names if k in point and k in p)
            distances.append(math.sqrt(sq))

        min_dist = min(distances) if distances else 1.0

        # Exact hit on a known sample
        if min_dist < 1e-9:
            idx = distances.index(min_dist)
            return self.sample_values[idx], 0.0

        # Inverse Distance Weighting (IDW) interpolation
        weights = [1.0 / (d ** 2 + 1e-12) for d in distances]
        total_w = sum(weights)
        interpolated = sum(w * val for w, val in zip(weights, self.sample_values)) / total_w

        # Uncertainty scales monotonically with distance to nearest known support point
        uncertainty = min(1.0, min_dist * 0.5)

        return interpolated, uncertainty


class SurrogateModelingEngine:
    """
    SME fits and serves fast in-memory surrogates to automate multi-fidelity compute routing.
    """

    def __init__(self) -> None:
        self.surrogates: Dict[str, SurrogateModel] = {}

    def fit_from_history(
        self,
        model_id: str,
        points: List[Dict[str, float]],
        values: List[float],
    ) -> SurrogateModel:
        """Constructs an IDW/RBF surrogate from an array of computed points."""
        if not points or not values or len(points) != len(values):
            raise ValueError("Points and values must be non-empty and of equal length.")

        features = list(points[0].keys())
        surrogate = SurrogateModel(
            feature_names=features,
            sample_points=[dict(p) for p in points],
            sample_values=list(values),
        )
        self.surrogates[model_id] = surrogate
        return surrogate

    def create_amf_solver(
        self,
        model_id: str,
    ) -> Callable[[Dict[str, float]], Tuple[float, float]]:
        """
        Generates an AMF-compatible cheap solver closure returning (value, uncertainty).
        """
        surrogate = self.surrogates.get(model_id)
        if not surrogate:
            raise KeyError(f"Surrogate '{model_id}' not found.")

        def cheap_solver(inputs: Dict[str, float]) -> Tuple[float, float]:
            return surrogate.predict(inputs)

        return cheap_solver
