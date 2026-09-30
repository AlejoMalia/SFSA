/**
 * sfsa.session — Unified SFSA Session Orchestrator (JavaScript)
 * ==============================================================
 * Coordinates the complete suite of 39 SFSA scientific engines and provides direct execution
 * access to the 85-Skills Catalog for researchers and AI coding agents.
 *
 * Part of SFSA (Standard Framework for Scientific Advancement)
 * Author & Protocol Creator: Alejo Malia
 * License: CC BY 4.0
 */

import { MATEEngine, MATEStatus, MATEResult } from './mate.js';
import { TriadaEngine } from './triada.js';
import { AutocompleteEngine } from './autocomplete.js';
import { FrameworkLayerNetwork } from './fln.js';
import { ICREngine } from './icr.js';
import { ParetoPathEngine } from './path.js';
import { LayerConsistencyProjector } from './projection.js';
import { AdaptiveMultiFidelityEngine } from './amf.js';
import { AdaptiveSamplingEngine } from './asg.js';
import { SensitivityReductionAnalyzer } from './sra.js';
import { UncertaintyAwareStoppingEngine } from './uas.js';
import { ComputationalProvenanceEngine } from './cpe.js';
import { ConstraintAwarenessEngine } from './cae.js';
import { DiscrepancyIntelligenceEngine } from './die.js';
import { TemporalBudgetEngine } from './tbe.js';
import { PartialKnowledgeEngine } from './pke.js';
import { LandscapeStructureEngine } from './lse.js';
import { ResultForgettingEngine } from './rfe.js';
import { AssumptionIntegrityEngine } from './aie.js';
import { QueryCompressionEngine } from './cqe.js';
import { ScientificThematicEngine } from './ste.js';
import { LiteratureKnowledgeEngine } from './lke.js';
import { TagIndexLinkingEngine, TagType } from './til.js';
import { UncertaintyPropagationEngine } from './uqe.js';
import { UnitDimensionalEngine } from './ude.js';
import { SurrogateModelingEngine } from './sme.js';
import { DataAssimilationEngine } from './dae.js';
import { SymbolicEquivalenceEngine } from './sye.js';
import { ParallelBatchEngine } from './pbe.js';
import { RobustnessTestingEngine } from './rte.js';
import { ReproducibilityManifestEngine } from './rme.js';
import { LaboratoryDataRepository } from './ldr.js';
import { OrchestrationRoutingEngine, QueryArchetype } from './ore.js';
import { ValueInformationEngine, VOIAssessment } from './voi.js';
import { TransferExperienceEngine, TransferredPrior, ExperienceSnapshot } from './txe.js';
import { ExperimentLoopEngine, ExperimentProposal, LoopIterationResult } from './ele.js';
import { ModelRiskEngine, ModelRiskReport } from './mre.js';
import { ExplanationAuditEngine, DecisionRecord, QueryExplanation } from './xxe.js';
import { ScheduleResourceEngine, ScheduledTask, CampaignSchedule } from './sre.js';
import { SkillRegistry } from './skills.js';

export class SFSASession {
  constructor(options = {}) {
    this.name = options.name || "Default_Scientific_Framework";

    // 1-7. Foundational Engines
    this.mate = new MATEEngine();
    this.triada = new TriadaEngine({ mateEngine: this.mate });
    this.autocomplete = new AutocompleteEngine();
    this.fln = new FrameworkLayerNetwork();
    this.icr = new ICREngine({ level: options.optimizationLevel || 'O2_ANALYTICAL' });
    this.path = new ParetoPathEngine();
    this.projector = new LayerConsistencyProjector();

    // 8-20. Computational Decision & Execution Engines
    this.amf = new AdaptiveMultiFidelityEngine();
    this.asg = new AdaptiveSamplingEngine();
    this.sra = new SensitivityReductionAnalyzer();
    this.uas = new UncertaintyAwareStoppingEngine();
    this.cpe = new ComputationalProvenanceEngine();
    this.cae = new ConstraintAwarenessEngine();
    this.die = new DiscrepancyIntelligenceEngine();
    this.tbe = new TemporalBudgetEngine();
    this.pke = new PartialKnowledgeEngine();
    this.lse = new LandscapeStructureEngine();
    this.rfe = new ResultForgettingEngine();
    this.aie = new AssumptionIntegrityEngine();
    this.cqe = new QueryCompressionEngine();

    // 21-23. Thematic, Knowledge & Living Taxonomy
    this.ste = new ScientificThematicEngine();
    this.lke = new LiteratureKnowledgeEngine();
    this.til = new TagIndexLinkingEngine();

    // 24-32. Extended Scientific Verification, Acceleration & Projections
    this.uqe = new UncertaintyPropagationEngine();
    this.ude = new UnitDimensionalEngine();
    this.sme = new SurrogateModelingEngine();
    this.dae = new DataAssimilationEngine();
    this.sye = new SymbolicEquivalenceEngine();
    this.pbe = new ParallelBatchEngine();
    this.rte = new RobustnessTestingEngine();
    this.rme = new ReproducibilityManifestEngine();
    this.ldr = new LaboratoryDataRepository();

    // 33-39. Meta-Orchestration, Progress & Experimental Engines
    this.ore = new OrchestrationRoutingEngine();
    this.voi = new ValueInformationEngine();
    this.txe = new TransferExperienceEngine();
    this.ele = new ExperimentLoopEngine();
    this.mre = new ModelRiskEngine();
    this.xxe = new ExplanationAuditEngine();
    this.sre = new ScheduleResourceEngine();

    // 85-Skills Catalog
    this.skills = new SkillRegistry(this);
  }

  registerLayer(layerId, initialState = {}, name = null) {
    const layer = this.fln.registerLayer(layerId, initialState, name);
    this.til.addOrUpdateTag(`layer_${layerId}`, name || layerId, TagType.DOMAIN, 0.2);
    return layer;
  }

  connectLayers(sourceId, targetId, transformer, description = "") {
    this.fln.connectLayers(sourceId, targetId, transformer, description);
  }

  updateLayer(layerId, newState) {
    this.aie.auditState(newState);
    return this.fln.updateLayer(layerId, newState);
  }

  compute({
    taskId,
    inventory,
    solver,
    boundaryValidator = null,
    analyticalShortcut = null,
    estimatedDenseOps = 100,
    invariants = [],
    analyticalCandidate = null,
    bounds = {},
    approximateReuseTolerance = null
  }) {
    const [ok, err] = this.cae.validateInputs(inventory);
    if (!ok) {
      this.mate.recordEarlyAbort();
      throw new Error(`CAE pre-abort: ${err}`);
    }

    for (const [key, range] of Object.entries(bounds || {})) {
      const val = inventory[key];
      if (typeof val === 'number' && !(val >= range[0] && val <= range[1])) {
        this.mate.recordEarlyAbort();
        throw new Error(`Bounds abort: ${key}=${val} outside [${range[0]}, ${range[1]}]`);
      }
    }

    // Approximate reuse is opt-in: only when the caller states the relative tolerance it accepts,
    // and only for results produced by the current model version.
    const approx = approximateReuseTolerance !== null
      ? this.cpe.assessReuse(taskId, inventory, approximateReuseTolerance, this.mate.modelVersion)
      : null;
    if (approx && approx.reuseType === 'APPROXIMATE_REUSE') {
      return {
        taskId,
        status: MATEStatus.R1_EXACT,
        value: approx.value,
        cached: true,
        diagnostic: approx.rationale
      };
    }

    let activeSolver = solver;
    const chosenAnalytical = analyticalShortcut || analyticalCandidate;
    if (chosenAnalytical) {
      activeSolver = chosenAnalytical;
      this.icr.totalOperationsAvoided += estimatedDenseOps;
    }

    const res = this.mate.computeProjected({
      taskId,
      inputs: inventory,
      solver: activeSolver,
      boundaryValidator,
      approximateTolerance: approximateReuseTolerance ?? 0.0
    });

    // T3 invariants: a result violating them is never kept in any cache
    if (res.value !== null && res.value !== undefined && invariants && invariants.length > 0) {
      const failed = [];
      for (const inv of invariants) {
        let ok;
        try { ok = inv(res.value); } catch { ok = false; }
        if (!ok) failed.push(inv.name || 'invariant');
      }
      if (failed.length > 0) {
        this.cae.recordInfeasibility(inventory);
        this.mate._cache.delete(this.mate._hashKey(taskId, inventory));
        const sig = JSON.stringify(inventory);
        this.mate._approximateRecords = this.mate._approximateRecords.filter(
          (r) => !(r.taskId === taskId && JSON.stringify(r.inputs) === sig)
        );
        return new MATEResult({
          status: MATEStatus.R3_INFEASIBLE,
          value: null,
          cached: false,
          diagnosticMessage: `T3 invariant violated: ${failed.join(', ')}`,
        });
      }
    }

    if (res.value !== null && res.value !== undefined) {
      this.cae.recordFeasibility(inventory);
      this.cpe.registerResult({ taskId, inputs: inventory, output: res.value, modelVersion: this.mate.modelVersion });
      this.rfe.trackEntry(`${taskId}_${this.mate._hashKey(taskId, inventory).slice(0, 12)}`);
    }

    return res;
  }

  sessionReport() {
    return this.generateReport();
  }

  projectLayers(layerAId, layerBId) {
    const layerA = this.fln.getLayer(layerAId);
    const layerB = this.fln.getLayer(layerBId);
    if (!layerA || !layerB) throw new Error("Layers not found");
    return this.projector.projectAndIntersect({
      layerAId: layerA.layerId, layerAState: layerA.state,
      layerBId: layerB.layerId, layerBState: layerB.state,
    });
  }

  findParetoPathways(initialState, targetState, maxDepth = 5) {
    return this.path.findPathways({ initialState, targetState, maxSteps: maxDepth });
  }

  analyzeThemes() {
    const layers = [...this.fln.layers.values()];
    const layerNames = layers.map(l => l.name);
    const varNames = layers.flatMap(l => Object.keys(l.state));
    return this.ste.analyzeModel({ layerNames, variableNames: varNames });
  }

  searchLiterature(domains = null, limit = 5) {
    if (!domains || domains.length === 0) {
      domains = this.analyzeThemes().primaryThemes.map(t => t[0]);
      if (domains.length === 0) domains = ["multidisciplinary"];
    }
    return this.lke.proposeResources(domains, limit);
  }

  executeSkill(skillNameOrNumber, args = {}) {
    return this.skills.execute(skillNameOrNumber, args);
  }

  // --------------------------------------------------------------------------
  // LDR: Laboratory Data Repository & Reference Dataset Projections
  // --------------------------------------------------------------------------

  synthesizeDataset({ tableId, name, modelFn, parameterSweeps, description = '' }) {
    return this.ldr.synthesizeReferenceTable({
      tableId,
      name,
      modelFn,
      parameterSweeps,
      description
    });
  }

  getDataset(tableId) {
    return this.ldr.getTable(tableId);
  }

  _mergedLayerState() {
    const merged = {};
    for (const l of this.fln.layers.values()) Object.assign(merged, l.state);
    return merged;
  }

  generateReport() {
    const stats = this.mate.stats();
    return {
      sessionName: this.name,
      activeLayersCount: this.fln.layers.size,
      gapsResolvedCount: Math.max(0, this.fln.layers.size - this.autocomplete.detectGaps(this._mergedLayerState()).length),
      totalQueries: stats.totalLookups,
      cacheHits: stats.cacheHits,
      operationsEliminated: stats.operationsAvoided,
      activeEnginesCount: 39,
      skillsExecutedCount: this.skills.executionLog.length
    };
  }
}
