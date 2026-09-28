/**
 * sfsa.session — Unified SFSA Session Orchestrator for JavaScript
 * ===============================================================
 * Coordinates the 7 SFSA scientific engines in JavaScript:
 * - MATE Engine (Memoization & early-abort evaluation)
 * - TRIADA Engine (3-stage inventory, solver, and verification method)
 * - Autocomplete Engine (Gap detection & connection synthesizer)
 * - FLN Engine (Framework Layer Network for reactive DAG propagation)
 * - ICR Engine (In-Frame Computer Reduction for computational optimization)
 * - ParetoPath Engine (Multi-objective transition & pathway optimizer)
 * - Dimensional Projection Engine (Manifold subspace intersection & latent constraints)
 *
 * Part of SFSA (Standard Framework for Scientific Advancement)
 * Author & Protocol Creator: Alejo Malia
 * License: CC BY 4.0
 */

import { MATEEngine } from './mate.js';
import { TriadaEngine } from './triada.js';
import { AutocompleteEngine } from './autocomplete.js';
import { FrameworkLayerNetwork } from './fln.js';
import { ICREngine, OptimizationLevel } from './icr.js';
import { ParetoPathEngine } from './path.js';
import { DimensionalProjectionEngine } from './projection.js';

export class SFSASessionReport {
  constructor({
    sessionName,
    activeLayersCount,
    totalQueries,
    cacheHits,
    operationsEliminated,
    gapsResolvedCount,
    estimatedComputeSavedPct,
  }) {
    this.sessionName = sessionName;
    this.activeLayersCount = activeLayersCount;
    this.totalQueries = totalQueries;
    this.cacheHits = cacheHits;
    this.operationsEliminated = operationsEliminated;
    this.gapsResolvedCount = gapsResolvedCount;
    this.estimatedComputeSavedPct = estimatedComputeSavedPct;
  }
}

export class SFSASession {
  constructor({
    name = "Default_Scientific_Framework",
    optimizationLevel = OptimizationLevel.O2_ANALYTICAL,
  } = {}) {
    this.name = name;
    this.mate = new MATEEngine();
    this.triada = new TriadaEngine({ mateEngine: this.mate });
    this.autocomplete = new AutocompleteEngine();
    this.fln = new FrameworkLayerNetwork();
    this.icr = new ICREngine({ level: optimizationLevel });
    this.path = new ParetoPathEngine();
    this.projection = new DimensionalProjectionEngine();
  }

  registerLayer(layerId, initialState = {}, name = null) {
    return this.fln.registerLayer(layerId, initialState, name);
  }

  connectLayers(sourceLayerId, targetLayerId, transformer, description = "") {
    return this.fln.connectLayers(sourceLayerId, targetLayerId, transformer, description);
  }

  updateLayer(layerId, patch, propagate = true) {
    return this.fln.updateLayer(layerId, patch, propagate);
  }

  compute({
    taskId,
    inventory,
    solver,
    boundaryValidator = null,
    analyticalShortcut = null,
    estimatedDenseOps = 1000,
  }) {
    const optimizedSolver = (inputs) => {
      const { result } = this.icr.optimizeAndExecute({
        taskId,
        inputParams: inputs,
        exactSolver: solver,
        analyticalShortcut,
        estimatedDenseOps,
      });
      return result;
    };

    return this.mate.computeProjected({
      taskId,
      inputs: inventory,
      solver: optimizedSolver,
      boundaryValidator,
    });
  }

  computeTriada({
    taskName,
    inventoryInput,
    t1InventoryValidator,
    t2AnalyticalSolver,
    t3ProjectionVerifier,
  }) {
    return this.triada.runPipeline({
      taskName,
      inventoryInput,
      t1InventoryValidator,
      t2AnalyticalSolver,
      t3ProjectionVerifier,
    });
  }

  autoFillLayer(layerId, requiredSchema, minConfidence = 0.70) {
    const layer = this.fln.getLayer(layerId);
    if (!layer) {
      throw new Error(`Layer '${layerId}' not found.`);
    }

    const { updatedState, appliedCandidates } = this.autocomplete.autoFill(
      layer.state,
      requiredSchema,
      minConfidence
    );

    if (appliedCandidates.length > 0) {
      this.fln.updateLayer(layerId, updatedState, true);
    }
    return appliedCandidates;
  }

  findParetoPathways({
    initialState,
    targetState,
    maxSteps = 4,
    tolerance = 0.05,
  }) {
    return this.path.findPathways({
      initialState,
      targetState,
      maxSteps,
      tolerance,
    });
  }

  projectLayers(layerAId, layerBId, knownBounds = {}) {
    const layerA = this.fln.getLayer(layerAId);
    const layerB = this.fln.getLayer(layerBId);
    if (!layerA || !layerB) {
      throw new Error(`Layers '${layerAId}' or '${layerBId}' not found.`);
    }

    return this.projection.projectAndIntersect({
      layerAId,
      layerAState: layerA.state,
      layerBId,
      layerBState: layerB.state,
      knownBounds,
    });
  }

  sessionReport() {
    const m = this.mate.metrics;
    const totalQ = m.totalQueries || 0;
    const cacheH = m.cacheHits || 0;
    const savedPct = totalQ > 0 ? (cacheH / totalQ) * 100.0 : 0.0;

    return new SFSASessionReport({
      sessionName: this.name,
      activeLayersCount: this.fln.layers.size,
      totalQueries: totalQ,
      cacheHits: cacheH,
      operationsEliminated: this.icr.totalOperationsAvoided,
      gapsResolvedCount: this.autocomplete.resolutionHistory.length,
      estimatedComputeSavedPct: savedPct,
    });
  }
}
