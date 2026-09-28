"""
sfsa.session — Unified SFSA Session Orchestrator
===============================================
Coordinates the 5 SFSA scientific engines:
- MATE Engine (Multi-dimensional memoization & early-abort projection)
- TRIADA Engine (3-stage inventory, solver, and verification method)
- Autocomplete Engine (Gap detection & model connection synthesizer)
- FLN Engine (Framework Layer Network for reactive DAG propagation)
- ICR Engine (In-Frame Computer Reduction for computational optimization)

Part of SFSA (Standard Framework for Scientific Advancement)
Author & Protocol Creator: Alejo Malia
License: CC BY 4.0
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, Tuple

from sfsa.mate import MATEEngine, MATEResult, MATEStatus
from sfsa.triada import TriadaEngine, TriadaExecutionReport, TriadaStage
from sfsa.autocomplete import AutocompleteEngine, ConnectionCandidate, Gap
from sfsa.fln import FrameworkLayerNetwork, FrameworkLayer
from sfsa.icr import ICREngine, ReductionProfile, OptimizationLevel
from sfsa.path import ParetoPathEngine, Pathway, TransitionStep
from sfsa.projection import DimensionalProjectionEngine, ManifoldIntersectionReport


@dataclass
class SFSASessionReport:
    """Consolidated summary report of an SFSA research session."""
    session_name: str
    active_layers_count: int
    total_queries: int
    cache_hits: int
    operations_eliminated: int
    gaps_resolved_count: int
    estimated_compute_saved_pct: float


class SFSASession:
    """
    High-level orchestrator for research teams and AI agents applying SFSA.
    Provides a unified API to construct, compute, and synchronize theoretical frameworks.
    """

    def __init__(
        self,
        name: str = "Default_Scientific_Framework",
        optimization_level: OptimizationLevel = OptimizationLevel.O2_ANALYTICAL,
    ) -> None:
        self.name = name
        self.mate = MATEEngine()
        self.triada = TriadaEngine(mate_engine=self.mate)
        self.autocomplete = AutocompleteEngine()
        self.fln = FrameworkLayerNetwork()
        self.icr = ICREngine(level=optimization_level)
        self.path = ParetoPathEngine()
        self.projection = DimensionalProjectionEngine()

    def register_layer(
        self,
        layer_id: str,
        initial_state: Optional[Dict[str, Any]] = None,
        name: Optional[str] = None,
    ) -> FrameworkLayer:
        """Adds a theoretical layer to the framework network."""
        return self.fln.register_layer(layer_id, initial_state, name)

    def connect_layers(
        self,
        source_layer_id: str,
        target_layer_id: str,
        transformer: Callable[[Dict[str, Any], Dict[str, Any]], Dict[str, Any]],
        description: str = "",
    ) -> None:
        """Establishes a reactive dependency link between two layers."""
        self.fln.connect_layers(source_layer_id, target_layer_id, transformer, description)

    def update_layer(
        self,
        layer_id: str,
        patch: Dict[str, Any],
        propagate: bool = True,
    ) -> Dict[str, int]:
        """Modifies a layer and reactively updates all downstream dependencies."""
        return self.fln.update_layer(layer_id, patch, propagate)

    def compute(
        self,
        task_id: str,
        inventory: Dict[str, Any],
        solver: Callable[[Dict[str, Any]], Any],
        boundary_validator: Optional[Callable[[Dict[str, Any]], Tuple[bool, str]]] = None,
        analytical_shortcut: Optional[Callable[[Dict[str, Any]], Any]] = None,
        estimated_dense_ops: int = 1000,
    ) -> MATEResult:
        """
        Executes a task combining MATE memoization with In-Frame Computer Reduction.
        """
        # If analytical shortcut is available, wrap solver through ICR
        def optimized_solver(inputs: Dict[str, Any]) -> Any:
            res, _ = self.icr.optimize_and_execute(
                task_id=task_id,
                input_params=inputs,
                exact_solver=solver,
                analytical_shortcut=analytical_shortcut,
                estimated_dense_ops=estimated_dense_ops,
            )
            return res

        return self.mate.compute_projected(
            task_id=task_id,
            inputs=inventory,
            solver=optimized_solver,
            boundary_validator=boundary_validator,
        )

    def compute_triada(
        self,
        task_name: str,
        inventory_input: Dict[str, Any],
        t1_inventory_validator: Callable[[Dict[str, Any]], Tuple[bool, List[str]]],
        t2_analytical_solver: Callable[[Dict[str, Any]], Any],
        t3_projection_verifier: Callable[[Any, Dict[str, Any]], Tuple[bool, List[str]]],
    ) -> TriadaExecutionReport:
        """
        Executes a workflow following the strict 3-stage TRIADA protocol.
        """
        return self.triada.run_pipeline(
            task_name=task_name,
            inventory_input=inventory_input,
            t1_inventory_validator=t1_inventory_validator,
            t2_analytical_solver=t2_analytical_solver,
            t3_projection_verifier=t3_projection_verifier,
        )

    def auto_fill_layer(
        self,
        layer_id: str,
        required_schema: Dict[str, Any],
        min_confidence: float = 0.70,
    ) -> List[ConnectionCandidate]:
        """
        Detects missing variables in a specific layer and resolves them using the Autocomplete engine.
        """
        layer = self.fln.get_layer(layer_id)
        if layer is None:
            raise KeyError(f"Layer '{layer_id}' not found.")

        updated_state, applied_cands = self.autocomplete.auto_fill(
            current_state=layer.state,
            required_schema=required_schema,
            min_confidence=min_confidence,
        )
        if applied_cands:
            self.fln.update_layer(layer_id, updated_state, propagate=True)
        return applied_cands

    def find_pareto_pathways(
        self,
        initial_state: Dict[str, float],
        target_state: Dict[str, float],
        max_steps: int = 4,
        tolerance: float = 0.05,
    ) -> List[Pathway]:
        """Discovers the optimal non-dominated Pareto frontier connecting initial to target state."""
        return self.path.find_pathways(initial_state, target_state, max_steps, tolerance)

    def project_layers(
        self,
        layer_a_id: str,
        layer_b_id: str,
        known_bounds: Optional[Dict[str, Tuple[float, float]]] = None,
    ) -> ManifoldIntersectionReport:
        """Projects two framework layers as dimensional manifolds to uncover latent constraints and collisions."""
        layer_a = self.fln.get_layer(layer_a_id)
        layer_b = self.fln.get_layer(layer_b_id)
        if layer_a is None or layer_b is None:
            raise KeyError(f"Layers '{layer_a_id}' or '{layer_b_id}' not found.")
        return self.projection.project_and_intersect(
            layer_a_id=layer_a_id,
            layer_a_state=layer_a.state,
            layer_b_id=layer_b_id,
            layer_b_state=layer_b.state,
            known_bounds=known_bounds,
        )

    def session_report(self) -> SFSASessionReport:
        """Compiles an overall performance and compute reduction summary."""
        mate_m = self.mate.metrics
        total_q = mate_m.get("total_queries", 0)
        cache_h = mate_m.get("cache_hits", 0)
        saved_pct = (cache_h / total_q * 100.0) if total_q > 0 else 0.0

        return SFSASessionReport(
            session_name=self.name,
            active_layers_count=len(self.fln.layers),
            total_queries=total_q,
            cache_hits=cache_h,
            operations_eliminated=self.icr.total_operations_avoided,
            gaps_resolved_count=len(self.autocomplete.resolution_history),
            estimated_compute_saved_pct=saved_pct,
        )
