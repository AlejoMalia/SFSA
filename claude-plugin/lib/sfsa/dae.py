"""
sfsa.dae — Data Assimilation & Calibration Engine (DAE)
======================================================
Solves the scientific inverse problem: calibrates unknown theoretical parameters by assimilating
empirical lab observations, sensor logs, or benchmark tables without brute-force grid searches.
Applies bounded coordinate descent / Nelder-Mead optimization to minimize discrepancy against real data.

Part of SFSA (Standard Framework for Scientific Advancement)
Author & Protocol Creator: Alejo Malia
License: CC BY 4.0
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, Tuple
import math


@dataclass
class CalibrationResult:
    """Outcome of calibrating model parameters against empirical data."""
    calibrated_parameters: Dict[str, float]
    initial_rmse: float
    final_rmse: float
    r_squared: float
    iterations_used: int
    converged: bool
    residuals: List[float] = field(default_factory=list)


class DataAssimilationEngine:
    """
    DAE bridges the gap between theoretical models and laboratory measurements.
    """

    def __init__(self, tolerance: float = 1e-4, max_iterations: int = 100) -> None:
        self.tolerance = tolerance
        self.max_iterations = max_iterations

    def calibrate(
        self,
        experimental_data: List[Dict[str, float]], # List of rows with input keys and an 'observed' key
        model_fn: Callable[[Dict[str, float], Dict[str, float]], float], # (inputs, params) -> prediction
        initial_params: Dict[str, float],
        target_key: str = "observed",
        param_bounds: Optional[Dict[str, Tuple[float, float]]] = None,
    ) -> CalibrationResult:
        """
        Calibrates model parameters using iterative bounded coordinate descent.
        """
        params = dict(initial_params)
        bounds = param_bounds or {}

        def compute_rmse(curr_params: Dict[str, float]) -> Tuple[float, List[float]]:
            residuals = []
            for row in experimental_data:
                inputs = {k: v for k, v in row.items() if k != target_key}
                y_true = row[target_key]
                y_pred = model_fn(inputs, curr_params)
                residuals.append(y_true - y_pred)
            mse = sum(r**2 for r in residuals) / len(residuals) if residuals else 0.0
            return math.sqrt(mse), residuals

        initial_rmse, _ = compute_rmse(params)
        prev_rmse = initial_rmse
        converged = False
        step_size = 0.1

        for it in range(self.max_iterations):
            improved = False
            for p_name in list(params.keys()):
                orig_val = params[p_name]
                step = max(abs(orig_val) * step_size, 1e-4)

                # Try positive step
                params[p_name] = orig_val + step
                if p_name in bounds:
                    params[p_name] = max(bounds[p_name][0], min(bounds[p_name][1], params[p_name]))
                rmse_pos, _ = compute_rmse(params)

                # Try negative step
                params[p_name] = orig_val - step
                if p_name in bounds:
                    params[p_name] = max(bounds[p_name][0], min(bounds[p_name][1], params[p_name]))
                rmse_neg, _ = compute_rmse(params)

                best_val = orig_val
                best_rmse = prev_rmse

                if rmse_pos < best_rmse:
                    best_val = orig_val + step
                    best_rmse = rmse_pos
                    improved = True

                if rmse_neg < best_rmse:
                    best_val = orig_val - step
                    best_rmse = rmse_neg
                    improved = True

                params[p_name] = best_val
                prev_rmse = best_rmse

            if abs(initial_rmse - prev_rmse) < self.tolerance or not improved:
                step_size *= 0.5
                if step_size < 1e-5:
                    converged = True
                    break

        final_rmse, final_residuals = compute_rmse(params)

        # Compute R-squared
        y_vals = [row[target_key] for row in experimental_data]
        y_mean = sum(y_vals) / len(y_vals) if y_vals else 1.0
        ss_tot = sum((y - y_mean) ** 2 for y in y_vals)
        ss_res = sum(r ** 2 for r in final_residuals)
        r2 = 1.0 - (ss_res / ss_tot) if ss_tot > 1e-12 else 1.0

        return CalibrationResult(
            calibrated_parameters=params,
            initial_rmse=initial_rmse,
            final_rmse=final_rmse,
            r_squared=max(0.0, r2),
            iterations_used=it + 1,
            converged=converged,
            residuals=final_residuals,
        )
