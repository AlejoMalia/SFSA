/**
 * SFSA — Standard Framework for Scientific Advancement (JavaScript)
 * =================================================================
 * Universal, domain-neutral computational framework for accelerated scientific research.
 *
 * Engines:
 * 1. MATE Engine: Memoization, trajectory projection, and early-abort evaluation.
 * 2. TRIADA Engine: 3-stage protocol (T1 Inventory, T2 Solver, T3 Verification).
 * 3. Autocomplete Engine: Gap detection & model connection synthesis.
 * 4. FLN Engine: Framework Layer Network (reactive DAG for multi-layer synchronization).
 * 5. ICR Engine: In-Frame Computer Reduction (computational optimization & pruning).
 * 6. ParetoPath Engine: Multi-objective transition pathfinder & Pareto frontier optimization.
 * 7. LayerConsistency Engine: Cross-layer coupling, consistency projector, and parameter conflict check.
 *
 * Author & Protocol Creator: Alejo Malia
 * License: CC BY 4.0
 * Version: 0.1.0
 */

export { MATEEngine, MATEResult, MATEStatus } from './mate.js';
export { TriadaEngine, TriadaProtocol, TriadaStage, TriadaStepOutcome, TriadaExecutionReport } from './triada.js';
export { AutocompleteEngine, Gap, GapType, ConnectionCandidate } from './autocomplete.js';
export { FrameworkLayerNetwork, FrameworkLayer, LayerDependency } from './fln.js';
export { ICREngine, ReductionProfile, OptimizationLevel } from './icr.js';
export { ParetoPathEngine, TransitionStep, Pathway } from './path.js';
export {
  LayerConsistencyProjector,
  LayerConsistencyReport,
  ParameterCoupling,
  InconsistencyConflict,
  DimensionalProjectionEngine,
  LatentCoupling,
  ManifoldIntersectionReport,
} from './projection.js';
export { SFSASession, SFSASessionReport } from './session.js';
