"""
sfsa.rte — Robustness & Stress-Testing Engine (RTE)
==================================================
Audits model stability and hypothesis fragility under worst-case adversarial perturbations.
Identifies whether a theoretical conclusion is robust or dangerously fragile to small parameter
fluctuations, computing condition numbers and detecting bifurcation risks before publication.

Part of SFSA (Standard Framework for Scientific Advancement)
Author & Protocol Creator: Alejo Malia
License: CC BY 4.0
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, Tuple
import math


@dataclass
class RobustnessReport:
    """Diagnostic profile of model stability under adversarial perturbations."""
    is_robust: bool
    fragility_score: float             # 0.0 (immune to noise) to 1.0 (extremely fragile/chaotic)
    condition_number: float            # Relative output delta / relative input perturbation
    most_sensitive_parameter: str
    safe_perturbation_radius: float    # Max % variation allowed before exceeding tolerance
    diagnostic_details: List[str] = field(default_factory=list)


class RobustnessTestingEngine:
    """
    RTE stress-tests models against adversarial noise to prevent fragile conclusions.
    """

    def __init__(self, tolerance_output_delta: float = 0.10) -> None:
        self.tolerance_output_delta = tolerance_output_delta

    @staticmethod
    def _rel_delta(model_fn: Callable[[Dict[str, float]], float], inputs: Dict[str, float], base_val: float,
                   denom_base: float, p_name: str, pct: float, diagnostics: List[str]) -> float:
        """Relative output change; a crash or non-finite output under perturbation is maximal fragility."""
        try:
            val = model_fn(inputs)
        except Exception as exc:
            diagnostics.append(f"Singularity on '{p_name}' at {pct:.1%} shift: {type(exc).__name__}")
            return float("inf")
        if not math.isfinite(val):
            diagnostics.append(f"Non-finite output on '{p_name}' at {pct:.1%} shift")
            return float("inf")
        return abs(val - base_val) / denom_base

    def stress_test(
        self,
        base_inputs: Dict[str, float],
        model_fn: Callable[[Dict[str, float]], float],
        perturbation_percentages: List[float] = [0.01, 0.05, 0.10],
    ) -> RobustnessReport:
        """
        Applies directional multi-scale perturbations to evaluate sensitivity and stability.
        """
        base_val = model_fn(base_inputs)
        denom_base = max(abs(base_val), 1e-12)

        worst_rel_delta = 0.0
        most_sensitive = "none"
        max_condition_num = 0.0
        diagnostics = []

        for p_name, val in base_inputs.items():
            for pct in perturbation_percentages:
                delta = max(abs(val) * pct, 1e-6)

                # Positive perturbation
                inp_pos = dict(base_inputs)
                inp_pos[p_name] = val + delta
                rel_delta_pos = self._rel_delta(model_fn, inp_pos, base_val, denom_base, p_name, pct, diagnostics)

                # Negative perturbation
                inp_neg = dict(base_inputs)
                inp_neg[p_name] = val - delta
                rel_delta_neg = self._rel_delta(model_fn, inp_neg, base_val, denom_base, p_name, pct, diagnostics)

                local_worst = max(rel_delta_pos, rel_delta_neg)
                cond_num = local_worst / max(pct, 1e-6)

                if cond_num > max_condition_num:
                    max_condition_num = cond_num
                    most_sensitive = p_name

                if local_worst > worst_rel_delta:
                    worst_rel_delta = local_worst

                if local_worst > self.tolerance_output_delta:
                    diagnostics.append(
                        f"Fragility warning on '{p_name}': {pct:.1%} input shift produces {local_worst:.1%} output divergence."
                    )

        # Fragility score maps condition number to [0, 1]
        fragility = min(1.0, max_condition_num / 10.0)
        is_robust = fragility < 0.35

        safe_radius = (self.tolerance_output_delta / max(max_condition_num, 1.0)) * 100.0

        return RobustnessReport(
            is_robust=is_robust,
            fragility_score=fragility,
            condition_number=max_condition_num,
            most_sensitive_parameter=most_sensitive,
            safe_perturbation_radius=round(safe_radius, 2),
            diagnostic_details=diagnostics[:10],
        )
