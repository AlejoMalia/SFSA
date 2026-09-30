"""
sfsa.uqe — Uncertainty Propagation Engine (UQE)
==============================================
Propagates parametric uncertainties, confidence intervals, and error variances through framework
layers and reactive DAGs without demanding brute-force Monte Carlo sampling (10,000 runs).
Applies analytical first-order error propagation (covariance Taylor expansion) and interval arithmetic.

Part of SFSA (Standard Framework for Scientific Advancement)
Author & Protocol Creator: Alejo Malia
License: CC BY 4.0
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, Tuple
import math


@dataclass
class UncertaintyInterval:
    """A scientific parameter with quantified symmetrical or asymmetrical uncertainty."""
    nominal: float
    uncertainty: float                   # Standard error / standard deviation (1-sigma)
    confidence_level: float = 0.95       # Default 95% coverage (approx 2-sigma for normal dist)

    @property
    def lower(self) -> float:
        z = 1.96 if self.confidence_level == 0.95 else 1.0
        return self.nominal - z * self.uncertainty

    @property
    def upper(self) -> float:
        z = 1.96 if self.confidence_level == 0.95 else 1.0
        return self.nominal + z * self.uncertainty

    @property
    def relative_uncertainty(self) -> float:
        return abs(self.uncertainty / max(abs(self.nominal), 1e-12))


@dataclass
class PropagationReport:
    """Outcome of propagating uncertainty through a scientific transfer function."""
    output_interval: UncertaintyInterval
    dominant_contributors: List[Tuple[str, float]] # (parameter_name, relative_variance_fraction)
    formula_derivation: str


class UncertaintyPropagationEngine:
    """
    UQE propagates measurement errors and model variances through computational graphs.
    """

    def __init__(self, default_confidence: float = 0.95) -> None:
        self.default_confidence = default_confidence

    def combine_binary(
        self,
        a: UncertaintyInterval,
        b: UncertaintyInterval,
        operation: str, # '+', '-', '*', '/'
    ) -> UncertaintyInterval:
        """Applies exact Gaussian error propagation to elementary arithmetic operations."""
        if operation == "+":
            nom = a.nominal + b.nominal
            unc = math.sqrt(a.uncertainty**2 + b.uncertainty**2)
        elif operation == "-":
            nom = a.nominal - b.nominal
            unc = math.sqrt(a.uncertainty**2 + b.uncertainty**2)
        elif operation == "*":
            nom = a.nominal * b.nominal
            rel_sq = (a.uncertainty / max(abs(a.nominal), 1e-12))**2 + (b.uncertainty / max(abs(b.nominal), 1e-12))**2
            unc = abs(nom) * math.sqrt(rel_sq)
        elif operation == "/":
            denom = b.nominal if abs(b.nominal) > 1e-12 else 1e-12
            nom = a.nominal / denom
            rel_sq = (a.uncertainty / max(abs(a.nominal), 1e-12))**2 + (b.uncertainty / max(abs(b.nominal), 1e-12))**2
            unc = abs(nom) * math.sqrt(rel_sq)
        else:
            raise ValueError(f"Unsupported operation: {operation}")

        return UncertaintyInterval(nominal=nom, uncertainty=unc, confidence_level=self.default_confidence)

    def propagate_general(
        self,
        function: Callable[[Dict[str, float]], float],
        inputs: Dict[str, UncertaintyInterval],
        finite_difference_step: float = 1e-4,
    ) -> PropagationReport:
        """
        Propagates uncertainty through an arbitrary non-linear black-box function using numerical Jacobian.
        """
        nominal_dict = {k: v.nominal for k, v in inputs.items()}
        base_output = function(nominal_dict)

        variance_sum = 0.0
        contributions: Dict[str, float] = {}

        for k, interval in inputs.items():
            h = max(abs(interval.nominal) * finite_difference_step, finite_difference_step)
            perturbed_plus = dict(nominal_dict)
            perturbed_minus = dict(nominal_dict)
            perturbed_plus[k] += h
            perturbed_minus[k] -= h

            df_dx = (function(perturbed_plus) - function(perturbed_minus)) / (2.0 * h)
            param_variance = (df_dx * interval.uncertainty) ** 2
            variance_sum += param_variance
            contributions[k] = param_variance

        total_sigma = math.sqrt(variance_sum)
        output_int = UncertaintyInterval(nominal=base_output, uncertainty=total_sigma, confidence_level=self.default_confidence)

        # Calculate percentage contribution to variance
        contributors = []
        for k, var in contributions.items():
            fraction = (var / variance_sum) if variance_sum > 0 else 0.0
            contributors.append((k, fraction))
        contributors.sort(key=lambda item: item[1], reverse=True)

        return PropagationReport(
            output_interval=output_int,
            dominant_contributors=contributors,
            formula_derivation=f"First-order Taylor expansion over {len(inputs)} dimensions",
        )
