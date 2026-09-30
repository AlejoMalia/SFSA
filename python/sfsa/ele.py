"""
sfsa.ele — Experiment Loop Engine (ELE / Lab-in-the-Loop)
========================================================
Closes the scientific discovery loop between theoretical simulations and physical laboratory data.
Iterates the complete scientific cycle:
    Theoretical Model -> Prediction -> Experiment Design (DoE) -> Lab Measurement (LDR) ->
    Data Assimilation (DAE) -> Updated State & Residual Uncertainty.

Part of SFSA (Standard Framework for Scientific Advancement)
Author & Protocol Creator: Alejo Malia
License: CC BY 4.0
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, Tuple
import math
import time


@dataclass
class ExperimentProposal:
    """Design of Experiment (DoE) proposal for the next wet-lab or physical sensor test."""
    experiment_id: str
    target_parameters: Dict[str, float]
    predicted_theoretical_output: float
    expected_information_gain: float
    rationale: str


@dataclass
class LoopIterationResult:
    """Outcome of closing an experimental loop iteration."""
    iteration_index: int
    proposal: ExperimentProposal
    measured_lab_value: float
    theoretical_prediction: float
    discrepancy_delta: float
    recalibrated_parameters: Dict[str, float]
    residual_rmse: float


class ExperimentLoopEngine:
    """
    ELE coordinates the active dialogue between computational theory and empirical experiments.
    """

    def __init__(self) -> None:
        self.iterations: List[LoopIterationResult] = []

    def propose_next_experiment(
        self,
        candidate_space: List[Dict[str, float]],
        theory_model: Callable[[Dict[str, float]], float],
        uncertainty_estimator: Callable[[Dict[str, float]], float],
    ) -> ExperimentProposal:
        """
        Identifies the candidate experimental setup that maximizes epistemic information gain.
        """
        best_candidate = None
        max_info = -1.0
        best_pred = 0.0

        for idx, cand in enumerate(candidate_space):
            unc = uncertainty_estimator(cand)
            if unc > max_info:
                max_info = unc
                best_candidate = cand
                best_pred = theory_model(cand)

        exp_id = f"exp_doe_{len(self.iterations) + 1}"
        return ExperimentProposal(
            experiment_id=exp_id,
            target_parameters=best_candidate or {},
            predicted_theoretical_output=best_pred,
            expected_information_gain=max_info,
            rationale=f"Maximizes epistemic uncertainty ({max_info:.3f}) across parameter space",
        )

    def close_loop(
        self,
        proposal: ExperimentProposal,
        measured_lab_value: float,
        session: Any,
        parameter_bounds: Optional[Dict[str, Tuple[float, float]]] = None,
    ) -> LoopIterationResult:
        """
        Assimilates a real lab measurement:
        1. Compares with theoretical prediction.
        2. Recalibrates parameters using session.dae.
        3. Records baseline into session.ldr.
        """
        discrepancy = abs(measured_lab_value - proposal.predicted_theoretical_output)

        # Prepare calibration row
        calib_row = dict(proposal.target_parameters)
        calib_row["observed"] = measured_lab_value

        calibrated_params = {}
        rmse = discrepancy

        if hasattr(session, "dae"):
            res = session.dae.calibrate(
                experimental_data=[calib_row],
                model_fn=lambda inp, p: sum(p.get(k, 1.0) * inp.get(k, 1.0) for k in inp),
                initial_params={k: 1.0 for k in proposal.target_parameters},
                target_key="observed",
                param_bounds=parameter_bounds,
            )
            calibrated_params = res.calibrated_parameters
            rmse = res.final_rmse

        # Record to LDR if available
        if hasattr(session, "ldr"):
            session.ldr.synthesize_reference_table(
                table_id=f"ele_run_{len(self.iterations) + 1}",
                name="Experiment Loop Baseline",
                model_fn=lambda p: {"lab_measured": measured_lab_value, "pred": proposal.predicted_theoretical_output},
                parameter_sweeps={k: [v] for k, v in proposal.target_parameters.items()},
            )

        result = LoopIterationResult(
            iteration_index=len(self.iterations) + 1,
            proposal=proposal,
            measured_lab_value=measured_lab_value,
            theoretical_prediction=proposal.predicted_theoretical_output,
            discrepancy_delta=discrepancy,
            recalibrated_parameters=calibrated_params,
            residual_rmse=rmse,
        )
        self.iterations.append(result)
        return result
