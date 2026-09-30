"""
sfsa.session — Unified SFSA Session Orchestrator
===============================================
Coordinates the complete suite of 39 SFSA scientific engines and provides direct execution
access to the 85-Skills Catalog for researchers and AI coding agents.

Core Engines:
1. MATE — Multi-dimensional memoization, trajectory projection, and early abort
2. TRIADA — 3-stage protocol (T1 In-situ inventory, T2 Analytical solver, T3 Verification)
3. Autocomplete — Model gap detection and conceptual connection synthesis
4. FLN — Framework Layer Network (reactive DAG for multi-layer propagation)
5. ICR — In-Frame Computer Reduction (computational optimization & loop pruning)
6. ParetoPath — Multi-objective transition pathfinder & Pareto frontier optimization
7. LayerConsistencyProjector — Cross-layer coupling & parameter consistency projector
8. AMF — Adaptive Multi-Fidelity Engine
9. ASG — Adaptive Sampling & Experimentation Engine
10. SRA — Sensitivity & Reduction Analyzer
11. UAS — Uncertainty-Aware Stopping Engine
12. CPE — Computational Provenance & Reuse Engine
13. CAE — Constraint Awareness Engine
14. DIE — Discrepancy Intelligence Engine
15. TBE — Temporal Budget Engine
16. PKE — Partial Knowledge Engine
17. LSE — Landscape Structure Engine
18. RFE — Result Forgetting Engine
19. AIE — Assumption Integrity Engine
20. CQE — Query Compression Engine
21. STE — Scientific Thematic Engine
22. LKE — Literature & Knowledge Engine
23. TIL — Tag Index & Linking Engine

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
from sfsa.projection import LayerConsistencyProjector, LayerConsistencyReport
from sfsa.amf import AdaptiveMultiFidelityEngine, FidelityDecision
from sfsa.asg import AdaptiveSamplingEngine, SampleCandidate
from sfsa.sra import SensitivityReductionAnalyzer, DimensionalReduction
from sfsa.uas import UncertaintyAwareStoppingEngine, StoppingEvaluation
from sfsa.cpe import ComputationalProvenanceEngine, ReuseAssessment
from sfsa.cae import ConstraintAwarenessEngine
from sfsa.die import DiscrepancyIntelligenceEngine, DiscrepancyAnalysis
from sfsa.tbe import TemporalBudgetEngine, BudgetAllocation
from sfsa.pke import PartialKnowledgeEngine, PartialKnowledge
from sfsa.lse import LandscapeStructureEngine, LandscapeFeature
from sfsa.rfe import ResultForgettingEngine
from sfsa.aie import AssumptionIntegrityEngine, AssumptionViolation
from sfsa.cqe import QueryCompressionEngine, CompressedBatchResult
from sfsa.ste import ScientificThematicEngine, ThematicReport
from sfsa.lke import LiteratureKnowledgeEngine, EvidenceProposal
from sfsa.til import TagIndexLinkingEngine, Tag, TagType, SearchProfile
from sfsa.uqe import UncertaintyPropagationEngine, UncertaintyInterval
from sfsa.ude import UnitDimensionalEngine, DimensionVector
from sfsa.sme import SurrogateModelingEngine, SurrogateModel
from sfsa.dae import DataAssimilationEngine, CalibrationResult
from sfsa.sye import SymbolicEquivalenceEngine, SimplifiedExpression
from sfsa.pbe import ParallelBatchEngine, BatchExecutionSummary
from sfsa.rte import RobustnessTestingEngine, RobustnessReport
from sfsa.rme import ReproducibilityManifestEngine, ReproducibilityManifest
from sfsa.ldr import LaboratoryDataRepository, DatasetTable
from sfsa.ore import OrchestrationRoutingEngine, PipelinePlan, QueryArchetype
from sfsa.voi import ValueInformationEngine, VOIAssessment
from sfsa.txe import TransferExperienceEngine, TransferredPrior, ExperienceSnapshot
from sfsa.ele import ExperimentLoopEngine, ExperimentProposal, LoopIterationResult
from sfsa.mre import ModelRiskEngine, ModelRiskReport
from sfsa.xxe import ExplanationAuditEngine, DecisionRecord, QueryExplanation
from sfsa.sre import ScheduleResourceEngine, ScheduledTask, CampaignSchedule
from sfsa.skills import SkillRegistry


@dataclass
class SFSASessionReport:
    """Consolidated summary report of an SFSA research session."""
    session_name: str
    active_layers_count: int
    total_queries: int
    cache_hits: int
    operations_eliminated: int
    gaps_resolved_count: int
    active_engines_count: int
    estimated_compute_saved_pct: float
    skills_executed_count: int


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
        
        # 1-7. Foundational Engines
        self.mate = MATEEngine()
        self.triada = TriadaEngine(mate_engine=self.mate)
        self.autocomplete = AutocompleteEngine()
        self.fln = FrameworkLayerNetwork()
        self.icr = ICREngine(level=optimization_level)
        self.path = ParetoPathEngine()
        self.projector = LayerConsistencyProjector()
        
        # 8-20. Computational Decision & Execution Engines
        self.amf = AdaptiveMultiFidelityEngine()
        self.asg = AdaptiveSamplingEngine()
        self.sra = SensitivityReductionAnalyzer()
        self.uas = UncertaintyAwareStoppingEngine()
        self.cpe = ComputationalProvenanceEngine()
        self.cae = ConstraintAwarenessEngine()
        self.die = DiscrepancyIntelligenceEngine()
        self.tbe = TemporalBudgetEngine()
        self.pke = PartialKnowledgeEngine()
        self.lse = LandscapeStructureEngine()
        self.rfe = ResultForgettingEngine()
        self.aie = AssumptionIntegrityEngine()
        self.cqe = QueryCompressionEngine()
        
        # 21-23. Thematic, Knowledge & Living Taxonomy Engines
        self.ste = ScientificThematicEngine()
        self.lke = LiteratureKnowledgeEngine()
        self.til = TagIndexLinkingEngine()

        # 24-32. Extended Scientific Verification, Acceleration & Data Projections
        self.uqe = UncertaintyPropagationEngine()
        self.ude = UnitDimensionalEngine()
        self.sme = SurrogateModelingEngine()
        self.dae = DataAssimilationEngine()
        self.sye = SymbolicEquivalenceEngine()
        self.pbe = ParallelBatchEngine()
        self.rte = RobustnessTestingEngine()
        self.rme = ReproducibilityManifestEngine()
        self.ldr = LaboratoryDataRepository()

        # 33-39. Meta-Orchestration, Progress & Experimental Engines
        self.ore = OrchestrationRoutingEngine()
        self.voi = ValueInformationEngine()
        self.txe = TransferExperienceEngine()
        self.ele = ExperimentLoopEngine()
        self.mre = ModelRiskEngine()
        self.xxe = ExplanationAuditEngine()
        self.sre = ScheduleResourceEngine()

        # 85-Skills Registry
        self.skills = SkillRegistry(self)

    # --------------------------------------------------------------------------
    # FLN: Layer Management
    # --------------------------------------------------------------------------

    def register_layer(
        self,
        layer_id: str,
        initial_state: Optional[Dict[str, Any]] = None,
        name: Optional[str] = None,
    ) -> FrameworkLayer:
        """Adds a theoretical layer to the framework network and registers TIL tags."""
        layer = self.fln.register_layer(layer_id, initial_state, name)
        self.til.add_or_update_tag(
            tag_id=f"layer_{layer_id}",
            label=name or layer_id,
            tag_type=TagType.DOMAIN,
            weight_increment=0.2,
            source=f"layer:{layer_id}",
        )
        return layer

    def connect_layers(
        self,
        source_layer_id: str,
        target_layer_id: str,
        transformer: Callable[[Dict[str, Any], Dict[str, Any]], Dict[str, Any]],
        description: str = "",
    ) -> None:
        """Establishes a reactive dependency link between two layers."""
        self.fln.connect_layers(source_layer_id, target_layer_id, transformer, description)

    def update_layer(self, layer_id: str, new_state: Dict[str, Any]) -> List[str]:
        """Updates parameters of a layer and propagates deltas across dependent layers."""
        # Check model assumptions prior to propagation
        self.aie.audit_state(new_state)
        return self.fln.update_layer(layer_id, new_state)

    # --------------------------------------------------------------------------
    # Computation Pipeline: TRIADA + MATE + ICR + CAE + CPE
    # --------------------------------------------------------------------------

    def compute(
        self,
        task_id: str,
        inventory: Dict[str, Any],
        solver: Callable[[Dict[str, Any]], Any],
        boundary_validator: Optional[Callable[[Dict[str, Any]], Tuple[bool, str]]] = None,
        analytical_shortcut: Optional[Callable[[Dict[str, Any]], Any]] = None,
        estimated_dense_ops: int = 100,
        invariants: Optional[List[Callable[[Any], bool]]] = None,
        analytical_candidate: Optional[Callable[[Dict[str, Any]], Any]] = None,
        bounds: Optional[Dict[str, Tuple[float, float]]] = None,
        approximate_reuse_tolerance: Optional[float] = None,
    ) -> MATEResult:
        """
        Executes a scientific task through the full SFSA optimization pipeline:
        1. Constraint Awareness pre-checks (CAE)
        2. T1 Inventory Validation (TRIADA / boundary_validator)
        3. MATE Cache & Trajectory Projection Lookup
        4. In-Frame Computer Reduction (ICR)
        5. T2 Execution (Analytical preferred, then Solver)
        6. Provenance Registration (CPE) & Cache Track (RFE)
        7. T3 Bounded Verification (TRIADA)
        """
        # 1. CAE Pre-check
        valid_constraints, fail_reason = self.cae.validate_inputs(inventory)
        if not valid_constraints:
            self.mate.record_early_abort()
            raise ValueError(f"Constraint Awareness Engine (CAE) abort: {fail_reason}")

        # 1b. Explicit parameter bounds (T1 inventory limits)
        for key, (lo, hi) in (bounds or {}).items():
            val = inventory.get(key)
            if isinstance(val, (int, float)) and not (lo <= val <= hi):
                self.mate.record_early_abort()
                raise ValueError(f"Bounds abort: {key}={val} outside [{lo}, {hi}]")

        # 2. Approximate reuse is opt-in: a nearby result is only returned when the caller states the
        #    relative tolerance it accepts (and only for results produced by the current model version).
        approx = None
        if approximate_reuse_tolerance is not None:
            approx = self.cpe.assess_reuse(
                task_id, inventory,
                required_model_version=self.cpe_model_version(),
                custom_tolerance=approximate_reuse_tolerance,
            )
        if approx is not None and approx.reuse_type.value == "APPROXIMATE_REUSE":
            return MATEResult(
                status=MATEStatus.R1_EXACT,
                value=approx.value,
                cached=True,
                compute_time_saved_pct=95.0,
                diagnostic_message=f"Reused approximate provenance result: {approx.rationale}",
            )

        # 3. Solver through MATE with ICR analytical shortcuts
        active_solver = solver
        chosen_analytical = analytical_shortcut or analytical_candidate
        if chosen_analytical is not None:
            active_solver = chosen_analytical
            self.icr.total_operations_avoided += estimated_dense_ops

        res = self.mate.compute_projected(
            task_id=task_id,
            inputs=inventory,
            solver=active_solver,
            boundary_validator=boundary_validator,
            approximate_tolerance=approximate_reuse_tolerance or 0.0,
        )

        # 3b. T3 invariants: a result violating them is never kept in any cache
        if res.value is not None and invariants:
            failed = []
            for inv in invariants:
                try:
                    ok = inv(res.value)
                except Exception:
                    ok = False
                if not ok:
                    failed.append(getattr(inv, "__name__", "invariant"))
            if failed:
                self.mate._cache.pop(self.mate._hash_key(task_id, inventory), None)
                self.cae.record_infeasibility(inventory)
                self.mate._approximate_records = [
                    r for r in self.mate._approximate_records
                    if not (r.get("task_id") == task_id and r.get("inputs") == dict(inventory))
                ]
                return MATEResult(
                    status=MATEStatus.R3_INFEASIBLE,
                    value=None,
                    cached=False,
                    compute_time_saved_pct=0.0,
                    diagnostic_message=f"T3 invariant violated: {', '.join(failed)}",
                )

        # 4. Log provenance and cache tracking
        if res.value is not None:
            self.cae.record_feasibility(inventory)
            self.cpe.register_result(
                task_id=task_id, inputs=inventory, output=res.value, model_version=self.cpe_model_version()
            )
            self.rfe.track_entry(key=f"{task_id}_{self.mate._hash_key(task_id, inventory)[:12]}")

        return res

    def cpe_model_version(self) -> str:
        """Model version stamped on provenance records; tracks MATE so invalidation also retires reuse."""
        return self.mate.model_version

    def session_report(self) -> SFSASessionReport:
        """Returns consolidated session metrics (backward-compatible alias)."""
        return self.generate_report()

    # --------------------------------------------------------------------------
    # Projector & Multi-Objective Pareto Paths
    # --------------------------------------------------------------------------

    def project_layers(self, layer_a_id: str, layer_b_id: str) -> LayerConsistencyReport:
        """Evaluates coupling, normalized distance, and inconsistency conflicts between two layers."""
        layer_a = self.fln.get_layer(layer_a_id)
        layer_b = self.fln.get_layer(layer_b_id)
        if not layer_a or not layer_b:
            raise KeyError(f"One or both layers '{layer_a_id}', '{layer_b_id}' not found.")
        return self.projector.project_and_intersect(
            layer_a.layer_id, layer_a.state, layer_b.layer_id, layer_b.state
        )

    def find_pareto_pathways(
        self,
        initial_state: Dict[str, float],
        target_state: Dict[str, float],
        max_depth: int = 5,
    ) -> List[Pathway]:
        """Discovers non-dominated Pareto pathways between initial and target states."""
        return self.path.find_pathways(initial_state, target_state, max_steps=max_depth)

    # --------------------------------------------------------------------------
    # Thematic Analysis & Literature Exploration
    # --------------------------------------------------------------------------

    def analyze_themes(self) -> ThematicReport:
        """Performs semantic analysis across all active layers and formulas."""
        layer_names = [l.name for l in self.fln.layers.values()]
        variables = []
        for l in self.fln.layers.values():
            variables.extend(l.state.keys())
        return self.ste.analyze_model(layer_names=layer_names, variable_names=variables)

    def search_literature(self, domains: Optional[List[str]] = None, limit: int = 5) -> List[EvidenceProposal]:
        """Proposes relevant papers and data repositories aligned with active domains."""
        if not domains:
            thematic = self.analyze_themes()
            domains = [t[0] for t in thematic.primary_themes] or ["multidisciplinary"]
        return self.lke.propose_resources(primary_domains=domains, limit=limit)

    # --------------------------------------------------------------------------
    # Skills Dispatcher
    # --------------------------------------------------------------------------

    def execute_skill(self, skill_name_or_number: Any, **kwargs: Any) -> Any:
        """Executes one of the 85 SFSA skills uniformly."""
        return self.skills.execute(skill_name_or_number, **kwargs)

    # --------------------------------------------------------------------------
    # LDR: Laboratory Data Repository & Reference Dataset Projections
    # --------------------------------------------------------------------------

    def synthesize_dataset(
        self,
        table_id: str,
        name: str,
        model_fn: Callable[[Dict[str, float]], Dict[str, Any]],
        parameter_sweeps: Dict[str, List[float]],
        description: str = "",
    ) -> DatasetTable:
        """Projects a multi-dimensional reference table from parameter sweeps into LDR."""
        return self.ldr.synthesize_reference_table(
            table_id=table_id,
            name=name,
            model_fn=model_fn,
            parameter_sweeps=parameter_sweeps,
            description=description,
        )

    def get_dataset(self, table_id: str) -> Optional[DatasetTable]:
        """Retrieves a stored reference dataset from the Laboratory Data Repository."""
        return self.ldr.get_table(table_id)

    # --------------------------------------------------------------------------
    # Reporting
    # --------------------------------------------------------------------------

    def generate_report(self) -> SFSASessionReport:
        """Generates operational summary of the active session."""
        mate_stats = self.mate.stats()
        fln_layers = len(self.fln.layers)
        gaps = len(self.autocomplete.detect_gaps(self.fln.layers))

        total_queries = mate_stats.total_lookups
        hits = mate_stats.cache_hits
        eliminated = mate_stats.operations_avoided

        saved_pct = (hits / total_queries * 100.0) if total_queries > 0 else 0.0

        return SFSASessionReport(
            session_name=self.name,
            active_layers_count=fln_layers,
            total_queries=total_queries,
            cache_hits=hits,
            operations_eliminated=eliminated,
            gaps_resolved_count=max(0, fln_layers - gaps),
            active_engines_count=39,
            estimated_compute_saved_pct=saved_pct,
            skills_executed_count=len(self.skills.execution_log),
        )
