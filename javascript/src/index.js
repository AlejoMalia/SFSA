/**
 * SFSA — Standard Framework for Scientific Advancement (JavaScript / ESM)
 * =======================================================================
 * A universal, domain-neutral computational framework for accelerated scientific research.
 *
 * Author & Protocol Creator: Alejo Malia
 * License: CC BY 4.0
 * Version: 0.2.0
 */

// 1-7. Foundational Engines
export { MATEEngine, MATEStatus, ReuseLevel, MechanismStatus, MechanismCard, SpeculativeResult } from './mate.js';
export { TriadaEngine, TriadaProtocol, TriadaStage } from './triada.js';
export { AutocompleteEngine, Gap, GapType, ConnectionCandidate } from './autocomplete.js';
export { FrameworkLayerNetwork, FrameworkLayer } from './fln.js';
export { ICREngine, OptimizationLevel } from './icr.js';
export { ParetoPathEngine, TransitionStep, Pathway } from './path.js';
export { LayerConsistencyProjector, LayerConsistencyReport } from './projection.js';

// 8-20. Computational Decision & Execution Engines
export { AdaptiveMultiFidelityEngine, FidelityLevel } from './amf.js';
export { AdaptiveSamplingEngine } from './asg.js';
export { SensitivityReductionAnalyzer } from './sra.js';
export { UncertaintyAwareStoppingEngine } from './uas.js';
export { ComputationalProvenanceEngine, ReuseType } from './cpe.js';
export { ConstraintAwarenessEngine } from './cae.js';
export { DiscrepancyIntelligenceEngine, DiscrepancyCause } from './die.js';
export { TemporalBudgetEngine } from './tbe.js';
export { PartialKnowledgeEngine } from './pke.js';
export { LandscapeStructureEngine, LandscapeTopology } from './lse.js';
export { ResultForgettingEngine } from './rfe.js';
export { AssumptionIntegrityEngine } from './aie.js';
export { QueryCompressionEngine } from './cqe.js';

// 21-23. Thematic, Knowledge & Living Taxonomy Engines
export { ScientificThematicEngine, DOMAIN_TAXONOMY } from './ste.js';
export { LiteratureKnowledgeEngine, SourceType, DEFAULT_SOURCES } from './lke.js';
export { TagIndexLinkingEngine, TagType } from './til.js';

// 24-32. Extended Scientific Verification, Acceleration & Projections
export { UncertaintyPropagationEngine, UncertaintyInterval } from './uqe.js';
export { UnitDimensionalEngine, DimensionVector, CANONICAL_DIMENSIONS } from './ude.js';
export { SurrogateModelingEngine, SurrogateModel } from './sme.js';
export { DataAssimilationEngine } from './dae.js';
export { SymbolicEquivalenceEngine } from './sye.js';
export { ParallelBatchEngine } from './pbe.js';
export { RobustnessTestingEngine } from './rte.js';
export { ReproducibilityManifestEngine } from './rme.js';
export { LaboratoryDataRepository, DatasetTable } from './ldr.js';

// 33-39. Meta-Orchestration, Progress & Experimental Engines
export { OrchestrationRoutingEngine, QueryArchetype } from './ore.js';
export { ValueInformationEngine, VOIAssessment } from './voi.js';
export { TransferExperienceEngine, TransferredPrior, ExperienceSnapshot } from './txe.js';
export { ExperimentLoopEngine, ExperimentProposal, LoopIterationResult } from './ele.js';
export { ModelRiskEngine, ModelRiskReport } from './mre.js';
export { ExplanationAuditEngine, DecisionRecord, QueryExplanation } from './xxe.js';
export { ScheduleResourceEngine, ScheduledTask, CampaignSchedule } from './sre.js';

// Skills Catalog & Session
export { SkillRegistry, SKILL_DEFINITIONS } from './skills.js';
export { SFSASession } from './session.js';



export const VERSION = '0.2.0';
