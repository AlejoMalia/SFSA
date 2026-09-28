"""
SFSA — Standard Framework for Scientific Advancement
====================================================
A universal, domain-neutral computational framework for accelerated scientific research.

Engines:
1. MATE Engine: Multi-dimensional memoization, trajectory projection, and early-abort evaluation.
2. TRIADA Engine: 3-stage protocol (T1 In-situ inventory, T2 Analytical solver, T3 Projection).
3. Autocomplete Engine: Autonomous model gap detection and conceptual connection synthesis.
4. FLN Engine: Framework Layer Network (reactive DAG for multi-layer model propagation).
5. ICR Engine: In-Frame Computer Reduction (computational optimization & pass pruning).
6. ParetoPath Engine: Multi-objective transition pathfinder & Pareto frontier optimization.
7. Dimensional Projection Engine: Manifold subspace intersection & latent constraint discovery.

Author & Protocol Creator: Alejo Malia
License: CC BY 4.0
Version: 0.1.0
"""

from __future__ import annotations

from sfsa.mate import MATEEngine, MATEResult, MATEStatus
from sfsa.triada import TriadaEngine, TriadaProtocol, TriadaStage, TriadaExecutionReport
from sfsa.autocomplete import AutocompleteEngine, Gap, GapType, ConnectionCandidate
from sfsa.fln import FrameworkLayerNetwork, FrameworkLayer, LayerDependency
from sfsa.icr import ICREngine, ReductionProfile, OptimizationLevel
from sfsa.path import ParetoPathEngine, TransitionStep, Pathway
from sfsa.projection import (
    DimensionalProjectionEngine,
    LatentCoupling,
    ManifoldIntersectionReport,
    LayerConsistencyProjector,
    LayerConsistencyReport,
    ParameterCoupling,
    InconsistencyConflict,
)
from sfsa.session import SFSASession, SFSASessionReport

__version__ = "0.1.0"
__author__ = "Alejo Malia"
__license__ = "CC BY 4.0"

__all__ = [
    # MATE
    "MATEEngine",
    "MATEResult",
    "MATEStatus",
    # TRIADA
    "TriadaEngine",
    "TriadaProtocol",
    "TriadaStage",
    "TriadaExecutionReport",
    # Autocomplete
    "AutocompleteEngine",
    "Gap",
    "GapType",
    "ConnectionCandidate",
    # FLN
    "FrameworkLayerNetwork",
    "FrameworkLayer",
    "LayerDependency",
    # ICR
    "ICREngine",
    "ReductionProfile",
    "OptimizationLevel",
    # ParetoPath
    "ParetoPathEngine",
    "TransitionStep",
    "Pathway",
    # Layer Consistency / Dimensional Projection
    "LayerConsistencyProjector",
    "LayerConsistencyReport",
    "ParameterCoupling",
    "InconsistencyConflict",
    "DimensionalProjectionEngine",
    "LatentCoupling",
    "ManifoldIntersectionReport",
    # Session
    "SFSASession",
    "SFSASessionReport",
]
