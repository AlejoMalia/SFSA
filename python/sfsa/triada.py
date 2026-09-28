"""
sfsa.triada — TRIADA 3-Stage Scientific Method Engine
====================================================
Formal implementation of the TRIADA Protocol (Alejo Malia):
T1: Strict In-Situ Inventory & Boundary Verification
T2: Exact Analytical, Closed-Form & Stoichiometric Solvers
T3: Bounded Projection, MATE Invariant Check & Convergence

Eliminates computational waste by verifying preconditions and using closed forms
prior to invoking any numerical approximation.

Part of SFSA (Standard Framework for Scientific Advancement)
Author & Protocol Creator: Alejo Malia
License: CC BY 4.0
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Tuple
import time

from sfsa.mate import MATEEngine, MATEResult, MATEStatus


class TriadaStage(str, Enum):
    """The three canonical stages of the TRIADA protocol."""
    T1_INVENTORY = "T1_INVENTORY"
    T2_ANALYTICAL_SOLVER = "T2_ANALYTICAL_SOLVER"
    T3_PROJECTION_VERIFICATION = "T3_PROJECTION_VERIFICATION"


@dataclass
class TriadaStepOutcome:
    """Diagnostic outcome of an individual TRIADA stage."""
    stage: TriadaStage
    passed: bool
    data: Any
    elapsed_seconds: float
    notes: List[str] = field(default_factory=list)


@dataclass
class TriadaExecutionReport:
    """Full execution report across all 3 TRIADA stages."""
    success: bool
    task_name: str
    final_output: Any
    failed_at_stage: Optional[TriadaStage] = None
    total_elapsed_seconds: float = 0.0
    mate_status: MATEStatus = MATEStatus.R1_EXACT
    t1_outcome: Optional[TriadaStepOutcome] = None
    t2_outcome: Optional[TriadaStepOutcome] = None
    t3_outcome: Optional[TriadaStepOutcome] = None
    diagnostics: List[str] = field(default_factory=list)


class TriadaEngine:
    """
    Standard TRIADA Protocol Engine.
    Executes tasks structured as (T1 Inventory, T2 Analytical Solver, T3 Projection).
    """

    def __init__(self, mate_engine: Optional[MATEEngine] = None) -> None:
        self.mate = mate_engine or MATEEngine()

    def run_pipeline(
        self,
        task_name: str,
        inventory_input: Dict[str, Any],
        t1_inventory_validator: Callable[[Dict[str, Any]], Tuple[bool, List[str]]],
        t2_analytical_solver: Callable[[Dict[str, Any]], Any],
        t3_projection_verifier: Callable[[Any, Dict[str, Any]], Tuple[bool, List[str]]],
    ) -> TriadaExecutionReport:
        """
        Executes a scientific workflow under the full TRIADA protocol:
        - T1: Verifies all variables and conservation limits exist. If fail, stops immediately.
        - T2: Solves using analytical/exact methods via MATE caching.
        - T3: Verifies physical/operational invariants of the computed result.
        """
        start_time = time.perf_counter()
        diagnostics: List[str] = []

        # ========================================================
        # STAGE T1: In-Situ Inventory Check
        # ========================================================
        t1_start = time.perf_counter()
        t1_valid, t1_reasons = t1_inventory_validator(inventory_input)
        t1_duration = time.perf_counter() - t1_start

        t1_outcome = TriadaStepOutcome(
            stage=TriadaStage.T1_INVENTORY,
            passed=t1_valid,
            data=inventory_input,
            elapsed_seconds=t1_duration,
            notes=t1_reasons,
        )

        if not t1_valid:
            diagnostics.extend([f"T1_FAIL: {r}" for r in t1_reasons])
            total_duration = time.perf_counter() - start_time
            return TriadaExecutionReport(
                success=False,
                task_name=task_name,
                final_output=None,
                failed_at_stage=TriadaStage.T1_INVENTORY,
                total_elapsed_seconds=total_duration,
                mate_status=MATEStatus.R3_INFEASIBLE,
                t1_outcome=t1_outcome,
                diagnostics=diagnostics,
            )

        # ========================================================
        # STAGE T2: Analytical & Stoichiometric Solver (MATE guarded)
        # ========================================================
        t2_start = time.perf_counter()
        mate_res = self.mate.compute_projected(
            task_id=task_name,
            inputs=inventory_input,
            solver=t2_analytical_solver,
        )
        t2_duration = time.perf_counter() - t2_start

        t2_outcome = TriadaStepOutcome(
            stage=TriadaStage.T2_ANALYTICAL_SOLVER,
            passed=(mate_res.status != MATEStatus.R3_INFEASIBLE),
            data=mate_res.value,
            elapsed_seconds=t2_duration,
            notes=[mate_res.diagnostic_message],
        )

        if mate_res.status == MATEStatus.R3_INFEASIBLE:
            diagnostics.append(f"T2_FAIL: Solver aborted by MATE guard: {mate_res.diagnostic_message}")
            total_duration = time.perf_counter() - start_time
            return TriadaExecutionReport(
                success=False,
                task_name=task_name,
                final_output=None,
                failed_at_stage=TriadaStage.T2_ANALYTICAL_SOLVER,
                total_elapsed_seconds=total_duration,
                mate_status=MATEStatus.R3_INFEASIBLE,
                t1_outcome=t1_outcome,
                t2_outcome=t2_outcome,
                diagnostics=diagnostics,
            )

        # ========================================================
        # STAGE T3: Bounded Projection & Global Invariant Verification
        # ========================================================
        t3_start = time.perf_counter()
        t3_valid, t3_reasons = t3_projection_verifier(mate_res.value, inventory_input)
        t3_duration = time.perf_counter() - t3_start

        t3_outcome = TriadaStepOutcome(
            stage=TriadaStage.T3_PROJECTION_VERIFICATION,
            passed=t3_valid,
            data={"output": mate_res.value, "verified": t3_valid},
            elapsed_seconds=t3_duration,
            notes=t3_reasons,
        )

        if not t3_valid:
            diagnostics.extend([f"T3_FAIL: {r}" for r in t3_reasons])
            total_duration = time.perf_counter() - start_time
            return TriadaExecutionReport(
                success=False,
                task_name=task_name,
                final_output=mate_res.value,
                failed_at_stage=TriadaStage.T3_PROJECTION_VERIFICATION,
                total_elapsed_seconds=total_duration,
                mate_status=MATEStatus.R3_INFEASIBLE,
                t1_outcome=t1_outcome,
                t2_outcome=t2_outcome,
                t3_outcome=t3_outcome,
                diagnostics=diagnostics,
            )

        total_duration = time.perf_counter() - start_time
        diagnostics.append("TRIADA protocol executed successfully through T1, T2, and T3.")

        return TriadaExecutionReport(
            success=True,
            task_name=task_name,
            final_output=mate_res.value,
            failed_at_stage=None,
            total_elapsed_seconds=total_duration,
            mate_status=mate_res.status,
            t1_outcome=t1_outcome,
            t2_outcome=t2_outcome,
            t3_outcome=t3_outcome,
            diagnostics=diagnostics,
        )


# Alias
TriadaProtocol = TriadaEngine
