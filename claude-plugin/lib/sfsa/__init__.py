"""
SFSA — Standard Framework for Scientific Advancement
====================================================
A universal, domain-neutral computational framework for accelerated scientific research.

Architectural Engines (39 engines; see README for the full table). Core:
1.  MATE — Multi-dimensional memoization, trajectory projection, and early-abort evaluation.
2.  TRIADA — 3-stage protocol (T1 In-situ inventory, T2 Analytical solver, T3 Verification).
3.  Autocomplete — Autonomous model gap detection and conceptual connection synthesis.
4.  FLN — Framework Layer Network (reactive DAG for multi-layer model propagation).
5.  ICR — In-Frame Computer Reduction (computational optimization & loop pruning).
6.  ParetoPath — Multi-objective transition pathfinder & Pareto frontier optimization.
7.  LayerConsistencyProjector — Cross-layer coupling & parameter consistency projector.
8.  AMF — Adaptive Multi-Fidelity Engine (cheap vs. intermediate vs. expensive model routing).
9.  ASG — Adaptive Sampling & Experimentation Engine (information-theoretic parameter acquisition).
10. SRA — Sensitivity & Reduction Analyzer (active subspace identification & FLN branch pruning).
11. UAS — Uncertainty-Aware Stopping Engine (scientific conclusion early stopping).
12. CPE — Computational Provenance & Reuse Engine (lineage tracking & approximate reuse).
13. CAE — Constraint Awareness Engine (implicit bounds inference & feasible domain cuts).
14. DIE — Discrepancy Intelligence Engine (multi-solver conflict diagnosis & reconciliation).
15. TBE — Temporal Budget Engine (dynamic computational time-slice management).
16. PKE — Partial Knowledge Engine (intermediate state & bound harvesting).
17. LSE — Landscape Structure Engine (coarse topological & response surface mapping).
18. RFE — Result Forgetting Engine (cost-weighted cache eviction & hygiene).
19. AIE — Assumption Integrity Engine (regime transition & model premise auditing).
20. CQE — Query Compression Engine (batch query clustering & centroid interpolation).
21. STE — Scientific Thematic Engine (model self-awareness & domain coverage mapping).
22. LKE — Literature & Knowledge Engine (typed scientific source retrieval & proposals).
23. TIL — Tag Index & Linking Engine (living operational taxonomy & search profiles).

Skills:
- Full 85-Skills Catalog via `session.skills` or `session.execute_skill()`.

Author & Protocol Creator: Alejo Malia
License: CC BY 4.0
Version: 0.2.0
"""

from __future__ import annotations

from sfsa.mate import (
    MATEEngine,
    MATEResult,
    MATEStatus,
    ReuseLevel,
    MechanismStatus,
    MechanismCard,
    SpeculativeResult,
)
from sfsa.triada import TriadaEngine, TriadaProtocol, TriadaStage, TriadaExecutionReport
from sfsa.autocomplete import AutocompleteEngine, Gap, GapType, ConnectionCandidate
from sfsa.fln import FrameworkLayerNetwork, FrameworkLayer, LayerDependency
from sfsa.icr import ICREngine, ReductionProfile, OptimizationLevel
from sfsa.path import ParetoPathEngine, TransitionStep, Pathway
from sfsa.projection import (
    LayerConsistencyProjector,
    LayerConsistencyReport,
    ParameterCoupling,
    InconsistencyConflict,
)
from sfsa.amf import AdaptiveMultiFidelityEngine, FidelityLevel, FidelityDecision
from sfsa.asg import AdaptiveSamplingEngine, SampleCandidate, SamplingCampaign
from sfsa.sra import SensitivityReductionAnalyzer, SensitivityProfile, DimensionalReduction
from sfsa.uas import UncertaintyAwareStoppingEngine, StoppingEvaluation
from sfsa.cpe import ComputationalProvenanceEngine, ProvenanceRecord, ReuseAssessment, ReuseType
from sfsa.cae import ConstraintAwarenessEngine, InferredConstraint, FeasibleDomainCut
from sfsa.die import DiscrepancyIntelligenceEngine, DiscrepancyAnalysis, DiscrepancyCause
from sfsa.tbe import TemporalBudgetEngine, BudgetAllocation, BudgetStrategy
from sfsa.pke import PartialKnowledgeEngine, PartialKnowledge
from sfsa.lse import LandscapeStructureEngine, LandscapeFeature, LandscapeTopology
from sfsa.rfe import ResultForgettingEngine, RetentionScore
from sfsa.aie import AssumptionIntegrityEngine, ModelAssumption, AssumptionViolation
from sfsa.cqe import QueryCompressionEngine, RepresentativeQuery, CompressedBatchResult
from sfsa.ste import ScientificThematicEngine, ThematicReport
from sfsa.lke import LiteratureKnowledgeEngine, ScientificSource, EvidenceProposal, SourceType
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
from sfsa.skills import SkillRegistry, SkillMetadata, SKILL_DEFINITIONS
from sfsa.session import SFSASession, SFSASessionReport

__version__ = "0.2.0"
__author__ = "Alejo Malia"
__license__ = "CC BY 4.0"

__all__ = [
    # Foundational Engines (1-7)
    "MATEEngine", "MATEResult", "MATEStatus", "ReuseLevel", "MechanismStatus", "MechanismCard", "SpeculativeResult",
    "TriadaEngine", "TriadaProtocol", "TriadaStage", "TriadaExecutionReport",
    "AutocompleteEngine", "Gap", "GapType", "ConnectionCandidate",
    "FrameworkLayerNetwork", "FrameworkLayer", "LayerDependency",
    "ICREngine", "ReductionProfile", "OptimizationLevel",
    "ParetoPathEngine", "TransitionStep", "Pathway",
    "LayerConsistencyProjector", "LayerConsistencyReport", "ParameterCoupling", "InconsistencyConflict",
    # Decision & Execution Engines (8-20)
    "AdaptiveMultiFidelityEngine", "FidelityLevel", "FidelityDecision",
    "AdaptiveSamplingEngine", "SampleCandidate", "SamplingCampaign",
    "SensitivityReductionAnalyzer", "SensitivityProfile", "DimensionalReduction",
    "UncertaintyAwareStoppingEngine", "StoppingEvaluation",
    "ComputationalProvenanceEngine", "ProvenanceRecord", "ReuseAssessment", "ReuseType",
    "ConstraintAwarenessEngine", "InferredConstraint", "FeasibleDomainCut",
    "DiscrepancyIntelligenceEngine", "DiscrepancyAnalysis", "DiscrepancyCause",
    "TemporalBudgetEngine", "BudgetAllocation", "BudgetStrategy",
    "PartialKnowledgeEngine", "PartialKnowledge",
    "LandscapeStructureEngine", "LandscapeFeature", "LandscapeTopology",
    "ResultForgettingEngine", "RetentionScore",
    "AssumptionIntegrityEngine", "ModelAssumption", "AssumptionViolation",
    "QueryCompressionEngine", "RepresentativeQuery", "CompressedBatchResult",
    # Thematic, Knowledge & Living Taxonomy (21-23)
    "ScientificThematicEngine", "ThematicReport",
    "LiteratureKnowledgeEngine", "ScientificSource", "EvidenceProposal", "SourceType",
    "TagIndexLinkingEngine", "Tag", "TagType", "SearchProfile",
    # Extended Scientific Verification, Acceleration & Projections (24-32)
    "UncertaintyPropagationEngine", "UncertaintyInterval",
    "UnitDimensionalEngine", "DimensionVector",
    "SurrogateModelingEngine", "SurrogateModel",
    "DataAssimilationEngine", "CalibrationResult",
    "SymbolicEquivalenceEngine", "SimplifiedExpression",
    "ParallelBatchEngine", "BatchExecutionSummary",
    "RobustnessTestingEngine", "RobustnessReport",
    "ReproducibilityManifestEngine", "ReproducibilityManifest",
    "LaboratoryDataRepository", "DatasetTable",
    # Meta-Orchestration, Progress & Experimental Engines (33-39)
    "OrchestrationRoutingEngine", "PipelinePlan", "QueryArchetype",
    "ValueInformationEngine", "VOIAssessment",
    "TransferExperienceEngine", "TransferredPrior", "ExperienceSnapshot",
    "ExperimentLoopEngine", "ExperimentProposal", "LoopIterationResult",
    "ModelRiskEngine", "ModelRiskReport",
    "ExplanationAuditEngine", "DecisionRecord", "QueryExplanation",
    "ScheduleResourceEngine", "ScheduledTask", "CampaignSchedule",
    # 85-Skills Catalog & Session
    "SkillRegistry", "SkillMetadata", "SKILL_DEFINITIONS",
    "SFSASession", "SFSASessionReport",
]
