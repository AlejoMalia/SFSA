"""
sfsa.lse — Landscape Structure Engine (LSE)
==========================================
Constructs a coarse-grained topological and structural map of the parameter space without dense sampling.
Identifies flat plateaus, steep gradients, narrow ridges/valleys, and potential discontinuities,
allowing Adaptive Sampling (ASG) and Multi-Fidelity (AMF) engines to focus resources intelligently.

Part of SFSA (Standard Framework for Scientific Advancement)
Author & Protocol Creator: Alejo Malia
License: CC BY 4.0
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Tuple
import math


class LandscapeTopology(str, Enum):
    FLAT_PLATEAU = "FLAT_PLATEAU"           # Near-zero curvature and gradient (can bypass dense sampling)
    SMOOTH_GRADIENT = "SMOOTH_GRADIENT"     # Predictable monotonic variation
    STEEP_VALLEY = "STEEP_VALLEY"           # High directional sensitivity, narrow canyon
    DISCONTINUITY_RISK = "DISCONTINUITY"   # Phase transition boundary or jump detected


@dataclass
class LandscapeFeature:
    """A structural zone identified within parameter space."""
    region_id: str
    centroid: Dict[str, float]
    topology: LandscapeTopology
    estimated_ruggedness: float             # Variance in directional second derivatives [0.0, 1.0]
    recommended_sampling_density: str       # 'MINIMAL', 'STANDARD', 'DENSE'


class LandscapeStructureEngine:
    """
    LSE maps the global contours of scientific response surfaces at minimal evaluation cost.
    """

    def __init__(self, probe_count_per_dim: int = 3) -> None:
        self.probe_count = probe_count_per_dim
        self.mapped_features: List[LandscapeFeature] = []

    def probe_region(
        self,
        bounds: Dict[str, Tuple[float, float]],
        fast_surrogate_or_fn: Callable[[Dict[str, float]], float],
    ) -> LandscapeFeature:
        """
        Rapidly assesses local topology across bounds using sparse orthogonal stencils.
        """
        centroid = {k: (b[0] + b[1]) / 2.0 for k, b in bounds.items()}
        c_val = fast_surrogate_or_fn(centroid)

        deltas = []
        for k, (low, high) in bounds.items():
            span = max(high - low, 1e-6)
            p_plus = dict(centroid)
            p_minus = dict(centroid)
            p_plus[k] = centroid[k] + span * 0.25
            p_minus[k] = centroid[k] - span * 0.25
            v_plus = fast_surrogate_or_fn(p_plus)
            v_minus = fast_surrogate_or_fn(p_minus)

            # Local curvature / variation
            diff = abs(v_plus - c_val) + abs(v_minus - c_val)
            deltas.append(diff / (abs(c_val) + 1e-6))

        mean_delta = sum(deltas) / len(deltas) if deltas else 0.0
        max_delta = max(deltas) if deltas else 0.0

        if max_delta < 0.02:
            topo = LandscapeTopology.FLAT_PLATEAU
            density = "MINIMAL"
            ruggedness = 0.05
        elif max_delta > 0.8:
            topo = LandscapeTopology.DISCONTINUITY_RISK
            density = "DENSE"
            ruggedness = 0.90
        elif (max_delta / max(mean_delta, 1e-6)) > 4.0:
            topo = LandscapeTopology.STEEP_VALLEY
            density = "DENSE"
            ruggedness = 0.70
        else:
            topo = LandscapeTopology.SMOOTH_GRADIENT
            density = "STANDARD"
            ruggedness = 0.35

        feature = LandscapeFeature(
            region_id=f"reg_{len(self.mapped_features) + 1}",
            centroid=centroid,
            topology=topo,
            estimated_ruggedness=ruggedness,
            recommended_sampling_density=density,
        )
        self.mapped_features.append(feature)
        return feature
