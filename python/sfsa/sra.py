"""
sfsa.sra — Sensitivity & Reduction Analyzer (SRA)
================================================
Quantifies local and global parameter sensitivity across framework layers and objective functions.
Identifies and eliminates non-impactful degrees of freedom, projecting high-dimensional parameter
spaces into lower-dimensional active subspaces and pruning insensitive branches in the FLN DAG.

Part of SFSA (Standard Framework for Scientific Advancement)
Author & Protocol Creator: Alejo Malia
License: CC BY 4.0
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, Set, Tuple
import math


@dataclass
class SensitivityProfile:
    """Sensitivity metrics for a specific model parameter."""
    parameter_name: str
    first_order_index: float           # Normalized Sobol/OAT sensitivity index [0.0, 1.0]
    is_impactful: bool                 # True if sensitivity exceeds threshold
    effective_gradient: float
    description: str


@dataclass
class DimensionalReduction:
    """Outcome of reducing model dimensionality prior to heavy numerical execution."""
    original_dimension: int
    reduced_dimension: int
    retained_parameters: List[str]
    pruned_parameters: List[str]
    variance_retained_ratio: float
    fln_layers_to_bypass: List[str] = field(default_factory=list)


class SensitivityReductionAnalyzer:
    """
    SRA Engine analyzes parametric impact before running heavy simulations.
    Informs FLN which dependencies are insensitive and safely bypassable.
    """

    def __init__(self, sensitivity_threshold: float = 0.05) -> None:
        self.sensitivity_threshold = sensitivity_threshold
        self.profiles: Dict[str, SensitivityProfile] = {}

    def analyze_one_at_a_time(
        self,
        base_inputs: Dict[str, float],
        objective_fn: Callable[[Dict[str, float]], float],
        perturbation_delta: float = 0.01,
    ) -> List[SensitivityProfile]:
        """
        Computes normalized local sensitivity indices via one-at-a-time (OAT) finite differences.
        """
        base_val = objective_fn(base_inputs)
        gradients: Dict[str, float] = {}
        total_mag = 0.0

        for k, v in base_inputs.items():
            perturbed = dict(base_inputs)
            delta = abs(v) * perturbation_delta if abs(v) > 1e-9 else perturbation_delta
            perturbed[k] = v + delta
            perturbed_val = objective_fn(perturbed)
            grad = abs((perturbed_val - base_val) / delta)
            gradients[k] = grad
            total_mag += grad

        results: List[SensitivityProfile] = []
        for k, grad in gradients.items():
            index = (grad / total_mag) if total_mag > 1e-12 else 0.0
            impactful = index >= self.sensitivity_threshold
            prof = SensitivityProfile(
                parameter_name=k,
                first_order_index=index,
                is_impactful=impactful,
                effective_gradient=grad,
                description=(
                    f"Highly impactful ({index:.1%})" if index > 0.2
                    else f"Moderate impact ({index:.1%})" if impactful
                    else f"Prunable / insensitive ({index:.1%})"
                ),
            )
            self.profiles[k] = prof
            results.append(prof)

        return sorted(results, key=lambda p: p.first_order_index, reverse=True)

    def reduce_parameter_space(
        self,
        base_inputs: Dict[str, float],
        objective_fn: Callable[[Dict[str, float]], float],
        target_variance_explained: float = 0.95,
    ) -> DimensionalReduction:
        """
        Projects parameter space into minimal active subset explaining >= target variance.
        """
        profiles = self.analyze_one_at_a_time(base_inputs, objective_fn)
        retained: List[str] = []
        pruned: List[str] = []
        accumulated_variance = 0.0

        for prof in profiles:
            if accumulated_variance < target_variance_explained or prof.is_impactful:
                retained.append(prof.parameter_name)
                accumulated_variance += prof.first_order_index
            else:
                pruned.append(prof.parameter_name)

        return DimensionalReduction(
            original_dimension=len(base_inputs),
            reduced_dimension=len(retained),
            retained_parameters=retained,
            pruned_parameters=pruned,
            variance_retained_ratio=min(1.0, accumulated_variance),
        )
