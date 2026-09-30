"""
sfsa.ore — Orchestration & Routing Engine (ORE)
==============================================
The meta-brain of the SFSA framework. Analyzes query characteristics, problem dimensionality,
available time budget (TBE), and required precision to compose and dynamically route
the minimal sufficient pipeline of scientific engines, preventing architectural compute bloat.

Part of SFSA (Standard Framework for Scientific Advancement)
Author & Protocol Creator: Alejo Malia
License: CC BY 4.0
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Tuple


class QueryArchetype(str, Enum):
    """Scientific query archetypes driving automated engine routing."""
    EXPLORATORY_SWEEP = "EXPLORATORY_SWEEP"       # Dense multi-dimensional space exploration
    HIGH_PRECISION_SOLVE = "HIGH_PRECISION_SOLVE" # Single or targeted high-fidelity evaluation
    INVERSE_CALIBRATION = "INVERSE_CALIBRATION"   # Assimilating lab data into theoretical parameters
    DAG_PROPAGATION = "DAG_PROPAGATION"           # Cascading delta updates across model layers
    VERIFICATION_AUDIT = "VERIFICATION_AUDIT"     # Formal physical invariant & dimensional checks


@dataclass
class PipelinePlan:
    """The synthesized minimal sufficient pipeline recommended for a scientific query."""
    query_archetype: QueryArchetype
    active_engine_sequence: List[str]
    estimated_compute_reduction_pct: float
    rationale: str
    early_exit_allowed: bool = True
    suggested_fidelity: str = "ADAPTIVE"


class OrchestrationRoutingEngine:
    """
    ORE intelligently selects, orders, and triggers only the necessary SFSA engines
    to solve a specific scientific query without running every engine unconditionally.
    """

    def __init__(self) -> None:
        self.routing_history: List[PipelinePlan] = []

    def plan_pipeline(
        self,
        query_archetype: QueryArchetype,
        input_cardinality: int = 1,
        parameter_dim: int = 2,
        budget_remaining_seconds: float = 60.0,
        tolerance: float = 0.05,
    ) -> PipelinePlan:
        """
        Synthesizes a tailored, minimal sufficient sequence of engines.
        """
        engines: List[str] = []
        rationale_parts: List[str] = []
        est_reduction = 0.0

        if query_archetype == QueryArchetype.EXPLORATORY_SWEEP:
            # High cardinality: Need filtering, clustering, and multi-fidelity
            if input_cardinality > 100:
                engines.append("CQE")  # Query compression
                rationale_parts.append("Cluster queries into centroids")
                est_reduction += 40.0

            if parameter_dim >= 4:
                engines.append("SRA")  # Dimension reduction
                rationale_parts.append(f"Prune insensitive dimensions from {parameter_dim}D")
                est_reduction += 25.0

            engines.extend(["ASG", "CAE", "AMF", "MATE"])
            rationale_parts.append("Filter informative points (ASG), cut unviable domains (CAE), and route multi-fidelity (AMF)")
            est_reduction = min(95.0, est_reduction + 25.0)
            suggested_fidelity = "CHEAP_FIRST"

        elif query_archetype == QueryArchetype.HIGH_PRECISION_SOLVE:
            engines.extend(["MRE", "CAE", "MATE", "TRIADA", "UQE"])
            rationale_parts.append("Check model validity (MRE), bound checks (CAE/MATE), closed-form T2 (TRIADA), and 1-pass uncertainty (UQE)")
            est_reduction = 45.0
            suggested_fidelity = "HIGH"

        elif query_archetype == QueryArchetype.INVERSE_CALIBRATION:
            engines.extend(["DAE", "SME", "RTE", "LDR"])
            rationale_parts.append("Assimilate observations (DAE), fit surrogate (SME), test condition stability (RTE), store baseline (LDR)")
            est_reduction = 85.0
            suggested_fidelity = "ADAPTIVE"

        elif query_archetype == QueryArchetype.DAG_PROPAGATION:
            engines.extend(["FLN", "CPE", "MATE", "AIE"])
            rationale_parts.append("Propagate deltas across layers (FLN), assess reuse (CPE), check invariants (MATE/AIE)")
            est_reduction = 75.0
            suggested_fidelity = "ADAPTIVE"

        elif query_archetype == QueryArchetype.VERIFICATION_AUDIT:
            engines.extend(["UDE", "TRIADA", "RTE", "RME", "XXE"])
            rationale_parts.append("Dimensional check (UDE), physical conservation (TRIADA), stress test (RTE), and audit certificate (RME/XXE)")
            est_reduction = 50.0
            suggested_fidelity = "HIGH"

        plan = PipelinePlan(
            query_archetype=query_archetype,
            active_engine_sequence=engines,
            estimated_compute_reduction_pct=est_reduction,
            rationale=" -> ".join(rationale_parts),
            early_exit_allowed=True,
            suggested_fidelity=suggested_fidelity,
        )
        self.routing_history.append(plan)
        return plan

    def execute_routed_query(
        self,
        session: Any,
        task_id: str,
        inputs: Dict[str, Any],
        heavy_solver: Callable[[Dict[str, Any]], Any],
        archetype: QueryArchetype = QueryArchetype.HIGH_PRECISION_SOLVE,
    ) -> Any:
        """
        Executes a query through the session following the orchestrated pipeline plan.
        """
        plan = self.plan_pipeline(archetype, input_cardinality=1)
        
        # 1. Pre-computation validity & cuts if active
        if "MRE" in plan.active_engine_sequence and hasattr(session, "mre"):
            risk = session.mre.assess_risk(inputs)
            if risk.verdict == "ABORT_INVALID_REGIME":
                raise ValueError(f"MRE Abort: Inputs violate validity domain: {risk.warnings}")

        if "CAE" in plan.active_engine_sequence and hasattr(session, "cae"):
            valid, err = session.cae.validate_inputs(inputs)
            if not valid:
                session.mate.record_early_abort()
                raise ValueError(f"CAE Abort: {err}")

        # 2. Solver execution guarded by MATE & TRIADA
        result = session.compute(
            task_id=task_id,
            inventory=inputs,
            solver=heavy_solver,
        )

        return result
