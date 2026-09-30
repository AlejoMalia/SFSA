"""
sfsa.mre — Model Risk & Validity Engine (MRE)
============================================
Audits model epistemic validity and extrapolation safety prior to calculation.
Monitors whether candidate inputs exceed physical validity envelopes, computes
extrapolation risk scores, assesses cumulative assumption fragility (from AIE),
and issues binding recommendations: COMPUTE_SAFE, CAUTION_EXTRAPOLATION, or ABORT_INVALID_REGIME.

Part of SFSA (Standard Framework for Scientific Advancement)
Author & Protocol Creator: Alejo Malia
License: CC BY 4.0
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple
import math


@dataclass
class ModelRiskReport:
    """Diagnostic profile of model risk for a set of inputs."""
    is_safe: bool
    risk_score: float                  # [0.0 (safe) to 1.0 (dangerous/unphysical)]
    verdict: str                       # 'COMPUTE_SAFE', 'CAUTION_EXTRAPOLATION', 'ABORT_INVALID_REGIME'
    extrapolation_parameters: List[str]
    max_extrapolation_ratio: float
    warnings: List[str] = field(default_factory=list)


class ModelRiskEngine:
    """
    MRE unifies validity boundaries and prevents dangerous out-of-domain computations.
    """

    def __init__(self, extrapolation_threshold: float = 0.20) -> None:
        self.extrapolation_threshold = extrapolation_threshold
        self.validity_envelopes: Dict[str, Tuple[float, float]] = {}
        self.hard_limits: Dict[str, Tuple[float, float]] = {}

    def register_envelope(
        self,
        parameter_name: str,
        safe_min: float,
        safe_max: float,
        hard_min: Optional[float] = None,
        hard_max: Optional[float] = None,
    ) -> None:
        """Registers safe and hard physical bounds for a parameter."""
        self.validity_envelopes[parameter_name] = (safe_min, safe_max)
        if hard_min is not None or hard_max is not None:
            self.hard_limits[parameter_name] = (
                hard_min if hard_min is not None else float("-inf"),
                hard_max if hard_max is not None else float("inf"),
            )

    def assess_risk(self, inputs: Dict[str, float]) -> ModelRiskReport:
        """
        Assesses input risk against declared validity envelopes and hard physical limits.
        """
        warnings: List[str] = []
        extrapolated_params: List[str] = []
        max_ratio = 0.0
        abort_triggered = False

        for p_name, val in inputs.items():
            # Check hard limits first
            if p_name in self.hard_limits:
                h_min, h_max = self.hard_limits[p_name]
                if val < h_min or val > h_max:
                    abort_triggered = True
                    warnings.append(f"Hard physical limit violated for '{p_name}': {val} not in [{h_min}, {h_max}]")

            # Check safe envelopes
            if p_name in self.validity_envelopes:
                s_min, s_max = self.validity_envelopes[p_name]
                span = max(abs(s_max - s_min), 1e-6)
                if val < s_min:
                    ratio = (s_min - val) / span
                    max_ratio = max(max_ratio, ratio)
                    extrapolated_params.append(p_name)
                    warnings.append(f"Under-range extrapolation on '{p_name}' by {ratio:.1%}")
                elif val > s_max:
                    ratio = (val - s_max) / span
                    max_ratio = max(max_ratio, ratio)
                    extrapolated_params.append(p_name)
                    warnings.append(f"Over-range extrapolation on '{p_name}' by {ratio:.1%}")

        risk_score = min(1.0, max_ratio)
        if abort_triggered or risk_score > 0.5:
            verdict = "ABORT_INVALID_REGIME"
            is_safe = False
        elif risk_score > self.extrapolation_threshold:
            verdict = "CAUTION_EXTRAPOLATION"
            is_safe = True
        else:
            verdict = "COMPUTE_SAFE"
            is_safe = True

        return ModelRiskReport(
            is_safe=is_safe,
            risk_score=risk_score,
            verdict=verdict,
            extrapolation_parameters=extrapolated_params,
            max_extrapolation_ratio=max_ratio,
            warnings=warnings,
        )
