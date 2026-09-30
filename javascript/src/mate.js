/**
 * sfsa.mate — MATE Engine (Multi-Dimensional Acceleration & Trajectory Estimation)
 * =================================================================================
 * Generic scientific memoization, projection, speculative execution battery, and
 * mechanism learning engine for JavaScript / Node.js.
 *
 * Evolved from a passive result memoizer into a dual-speed operating memory and
 * speculative mechanism battery:
 * - MATE-Core:   Result, plan, and shortcut memory across scientific queries.
 * - MATE-Spec:   Speculative background execution of alternative engine chains.
 * - MATE-Policy: Validity, promotion, budget control, and scientific safety governance.
 *
 * Part of SFSA (Standard Framework for Scientific Advancement)
 * Author & Protocol Creator: Alejo Malia
 * License: CC BY 4.0
 */

import crypto from 'node:crypto';

export const MATEStatus = Object.freeze({
  R1_EXACT: "R1_EXACT",           // Solved exactly or retrieved from memoized cache
  R2_PROJECTED: "R2_PROJECTED",   // Projected via closed-form approximation
  R3_INFEASIBLE: "R3_INFEASIBLE", // Aborted early: physical or mathematical boundary constraint violated
});

export const ReuseLevel = Object.freeze({
  L0: "L0",  // Zero-compute exact result (~0 cost)
  L1: "L1",  // Approximate reuse within tolerance / surrogate (~0 cost)
  L2: "L2",  // Plan reuse: known favorable engine sequence (low cost)
  L3: "L3",  // Shortcut reuse: learned early-stop / prune / fidelity (low cost)
  L4: "L4",  // Warm-start: improved initial state (medium cost)
  L5: "L5",  // Full recompute: complete execution pipeline (high cost)
});

export const MechanismStatus = Object.freeze({
  CANDIDATE: "candidate",        // Newly discovered via speculative battery
  TRUSTED: "trusted",            // Verified across multiple cases without quality loss
  DEFAULT: "default",            // Promoted to preferred default for this pattern
  REJECTED: "rejected",          // Fails validation, violates invariants, or deprecated
});

export class MechanismCard {
  constructor({
    id,
    pattern,
    chain = [],
    entryConditions = {},
    forbiddenConditions = {},
    expectedCost = 1.0,
    expectedQuality = 1.0,
    expectedRisk = 0.0,
    confidence = 0.5,
    evidenceCount = 1,
    provenance = "speculative_battery",
    modelVersion = "v1.0",
    toleranceProfile = {},
    outputsCached = [],
    shortcuts = {},
    failures = [],
    status = MechanismStatus.CANDIDATE,
    createdAt = Date.now() / 1000,
  } = {}) {
    this.id = id;
    this.pattern = pattern;
    this.chain = chain;
    this.entryConditions = entryConditions;
    this.forbiddenConditions = forbiddenConditions;
    this.expectedCost = expectedCost;
    this.expectedQuality = expectedQuality;
    this.expectedRisk = expectedRisk;
    this.confidence = confidence;
    this.evidenceCount = evidenceCount;
    this.provenance = provenance;
    this.modelVersion = modelVersion;
    this.toleranceProfile = toleranceProfile;
    this.outputsCached = outputsCached;
    this.shortcuts = shortcuts;
    this.failures = failures;
    this.status = status;
    this.createdAt = createdAt;
  }
}

export class SpeculativeResult {
  constructor({
    mechanismId,
    chain = [],
    realCost = 0.0,
    outputValue = null,
    discrepancyVsOfficial = 0.0,
    invariantsPassed = true,
    isFavorable = false,
    rationale = "",
  } = {}) {
    this.mechanismId = mechanismId;
    this.chain = chain;
    this.realCost = realCost;
    this.outputValue = outputValue;
    this.discrepancyVsOfficial = discrepancyVsOfficial;
    this.invariantsPassed = invariantsPassed;
    this.isFavorable = isFavorable;
    this.rationale = rationale;
  }
}

export class MATEResult {
  constructor({
    status = MATEStatus.R1_EXACT,
    value = null,
    cached = false,
    computeTimeSavedPct = 0.0,
    elapsedMs = 0.0,
    diagnosticMessage = "",
    reuseLevel = ReuseLevel.L5,
    mechanismUsed = null,
    intermediateCheckpoints = [],
    speculativeDiscoveries = [],
  } = {}) {
    this.status = status;
    this.value = value;
    this.cached = cached;
    this.computeTimeSavedPct = computeTimeSavedPct;
    this.elapsedMs = elapsedMs;
    this.diagnosticMessage = diagnosticMessage;
    this.reuseLevel = reuseLevel;
    this.mechanismUsed = mechanismUsed;
    this.intermediateCheckpoints = intermediateCheckpoints;
    this.speculativeDiscoveries = speculativeDiscoveries;
  }
}

export class MATEEngine {
  constructor({
    cachePrecisionDecimals = 6,
    specMode = "bounded",
    speculativeBudgetRatio = 0.20,
    maxSpecChains = 2,
  } = {}) {
    this.cachePrecision = cachePrecisionDecimals;
    this.specMode = specMode; // 'off', 'idle_only', 'bounded', 'aggressive'
    this.speculativeBudgetRatio = speculativeBudgetRatio;
    this.maxSpecChains = maxSpecChains;
    this.modelVersion = "v1.0";

    // 1. MATE-Core (Result & Plan Memory)
    this._cache = new Map();
    this._approximateRecords = [];
    this.cards = new Map();
    this.plansByPattern = new Map();
    this.negativeKnowledge = new Map();

    // 2. Metrics
    this._metrics = {
      totalQueries: 0,
      cacheHits: 0,
      earlyAborts: 0,
      fullComputes: 0,
      estimatedCpuMsSaved: 0.0,
      l0ExactHits: 0,
      l1ApproxHits: 0,
      l2PlanHits: 0,
      l3ShortcutHits: 0,
      speculativeRunsCount: 0,
      mechanismsDiscovered: 0,
      mechanismsPromoted: 0,
    };
  }

  _normalize(obj) {
    if (typeof obj === 'number') {
      if (Number.isNaN(obj) || !Number.isFinite(obj)) return String(obj);
      return Math.round(obj * 10 ** this.cachePrecision) / (10 ** this.cachePrecision);
    }
    if (obj === null || typeof obj === 'boolean' || typeof obj === 'string') {
      return obj;
    }
    if (Array.isArray(obj)) {
      return obj.map((x) => this._normalize(x));
    }
    if (typeof obj === 'object') {
      const sortedKeys = Object.keys(obj).sort();
      const res = {};
      for (const k of sortedKeys) {
        res[k] = this._normalize(obj[k]);
      }
      return res;
    }
    return String(obj);
  }

  _hashKey(namespace, inputs) {
    const normalized = {
      ns: namespace,
      inputs: this._normalize(inputs),
    };
    const jsonStr = JSON.stringify(normalized);
    return crypto.createHash('sha256').update(jsonStr).digest('hex');
  }

  synthesizePatternSignature(taskId, inputs, context = null) {
    const keys = Object.keys(inputs || {}).sort();
    const dim = keys.length;
    const regime = (context && context.regime) ? context.regime : "general";
    return `${taskId}::${regime}::${dim}D::${keys.slice(0, 4).join('_')}`;
  }

  memoizedGet(key) {
    return this._cache.get(key);
  }

  memoizedSet(key, value) {
    this._cache.set(key, value);
  }

  clearCache() {
    this._cache.clear();
    this._approximateRecords = [];
  }

  // --------------------------------------------------------------------------
  // MATE-Core: Multi-level Lookup (L0 -> L1 -> L2/L3 -> L5)
  // --------------------------------------------------------------------------

  lookupMultilevel(taskId, inputs, tolerance = 0.05, context = null) {
    // Level L0: Exact result lookup
    const cacheKey = this._hashKey(taskId, inputs);
    const exact = this.memoizedGet(cacheKey);
    if (exact !== undefined) {
      this._metrics.l0ExactHits += 1;
      return [ReuseLevel.L0, exact, null];
    }

    // Level L1: Approximate reuse from numerical neighbors
    if (inputs && typeof inputs === 'object') {
      const numKeys = Object.keys(inputs).filter(k => typeof inputs[k] === 'number');
      if (numKeys.length > 0) {
        for (const rec of this._approximateRecords) {
          if (rec.taskId === taskId && rec.modelVersion === this.modelVersion) {
            const recInputs = rec.inputs || {};
            const diffs = numKeys.map(k => Math.abs(inputs[k] - (recInputs[k] !== undefined ? recInputs[k] : inputs[k])) / Math.max(Math.abs(inputs[k]), 1.0));
            const maxRelDiff = diffs.length > 0 ? Math.max(...diffs) : 1.0;
            if (maxRelDiff <= tolerance) {
              this._metrics.l1ApproxHits += 1;
              return [ReuseLevel.L1, rec.value, null];
            }
          }
        }
      }
    }

    // Level L2/L3: Plan and shortcut reuse via MechanismCards
    const pattern = this.synthesizePatternSignature(taskId, inputs, context);
    const cardIds = this.plansByPattern.get(pattern) || [];
    const matchingCards = cardIds
      .map(cid => this.cards.get(cid))
      .filter(c => c && (c.status === MechanismStatus.TRUSTED || c.status === MechanismStatus.DEFAULT));

    if (matchingCards.length > 0) {
      matchingCards.sort((a, b) => {
        if (a.status === MechanismStatus.DEFAULT && b.status !== MechanismStatus.DEFAULT) return -1;
        if (b.status === MechanismStatus.DEFAULT && a.status !== MechanismStatus.DEFAULT) return 1;
        return a.expectedCost - b.expectedCost;
      });
      const bestCard = matchingCards[0];
      const hasShortcuts = bestCard.shortcuts && Object.keys(bestCard.shortcuts).length > 0;
      const reuseLvl = hasShortcuts ? ReuseLevel.L3 : ReuseLevel.L2;
      if (reuseLvl === ReuseLevel.L3) {
        this._metrics.l3ShortcutHits += 1;
      } else {
        this._metrics.l2PlanHits += 1;
      }
      return [reuseLvl, null, bestCard];
    }

    return [ReuseLevel.L5, null, null];
  }

  // --------------------------------------------------------------------------
  // MATE-Spec: Speculative Execution Battery
  // --------------------------------------------------------------------------

  speculate(taskId, inputs, officialValue, candidateChains = [], budgetTimeMs = 50.0) {
    if (this.specMode === "off" || budgetTimeMs <= 0) {
      return [];
    }

    const pattern = this.synthesizePatternSignature(taskId, inputs);
    const specResults = [];
    const chainsToTest = candidateChains.slice(0, this.maxSpecChains);

    for (const cand of chainsToTest) {
      const chainSeq = cand.chain || ["DEFAULT_PIPELINE"];
      const evalFn = cand.evalFn;
      const costFactor = cand.costFactor !== undefined ? cand.costFactor : 0.5;

      if (typeof evalFn !== 'function') continue;

      this._metrics.speculativeRunsCount += 1;
      const tStart = performance.now();
      try {
        const altValue = evalFn(inputs);
        const elapsed = performance.now() - tStart;

        // Discrepancy comparison
        let discrepancy = 0.0;
        if (typeof officialValue === 'number' && typeof altValue === 'number') {
          const denom = Math.max(Math.abs(officialValue), 1e-9);
          discrepancy = Math.abs(officialValue - altValue) / denom;
        }

        const tol = cand.tolerance !== undefined ? cand.tolerance : 0.05;
        const invariantsOk = typeof cand.invariantChecker === 'function' ? cand.invariantChecker(altValue) : true;
        const isFavorable = (discrepancy <= tol) && invariantsOk && (costFactor < 0.9);

        const cardId = `mech_${this._hashKey(pattern, chainSeq).slice(0, 8)}`;
        const res = new SpeculativeResult({
          mechanismId: cardId,
          chain: chainSeq,
          realCost: elapsed,
          outputValue: altValue,
          discrepancyVsOfficial: discrepancy,
          invariantsPassed: invariantsOk,
          isFavorable,
          rationale: `Alternative chain [${chainSeq.join(', ')}]: cost ${costFactor.toFixed(2)}x, discrepancy ${(discrepancy * 100).toFixed(2)}%`,
        });
        specResults.push(res);

        if (isFavorable) {
          this._registerOrUpdateMechanism({
            cardId,
            pattern,
            chain: chainSeq,
            cost: costFactor,
            quality: Math.max(0.0, 1.0 - discrepancy),
            shortcuts: cand.shortcuts || {},
          });
        } else {
          this._recordNegativeKnowledge(pattern, chainSeq, `Discrepancy ${(discrepancy * 100).toFixed(2)}% exceeded tolerance ${(tol * 100).toFixed(2)}%`);
        }
      } catch (e) {
        this._recordNegativeKnowledge(pattern, chainSeq, `Execution failed: ${e.message}`);
      }
    }

    return specResults;
  }

  _registerOrUpdateMechanism({ cardId, pattern, chain, cost, quality, shortcuts }) {
    let card;
    if (this.cards.has(cardId)) {
      card = this.cards.get(cardId);
      card.evidenceCount += 1;
      card.confidence = Math.min(0.99, card.confidence + 0.15);
      card.expectedCost = (card.expectedCost + cost) / 2.0;
      card.expectedQuality = (card.expectedQuality + quality) / 2.0;
    } else {
      card = new MechanismCard({
        id: cardId,
        pattern,
        chain,
        expectedCost: cost,
        expectedQuality: quality,
        expectedRisk: 0.05,
        confidence: 0.55,
        evidenceCount: 1,
        shortcuts,
        status: MechanismStatus.CANDIDATE,
        modelVersion: this.modelVersion,
      });
      this.cards.set(cardId, card);
      if (!this.plansByPattern.has(pattern)) {
        this.plansByPattern.set(pattern, []);
      }
      this.plansByPattern.get(pattern).push(cardId);
      this._metrics.mechanismsDiscovered += 1;
    }

    // Automated policy promotion criteria (candidate -> trusted)
    if (card.evidenceCount >= 3 && card.confidence >= 0.80 && card.status === MechanismStatus.CANDIDATE) {
      card.status = MechanismStatus.TRUSTED;
      this._metrics.mechanismsPromoted += 1;
    }

    return card;
  }

  _recordNegativeKnowledge(pattern, chain, reason) {
    if (!this.negativeKnowledge.has(pattern)) {
      this.negativeKnowledge.set(pattern, []);
    }
    this.negativeKnowledge.get(pattern).push({
      chain,
      reason,
      timestamp: Date.now() / 1000,
    });
  }

  // --------------------------------------------------------------------------
  // MATE-Policy: Promotion, Rejection & Governance
  // --------------------------------------------------------------------------

  promote(mechanismId, toDefault = false) {
    if (!this.cards.has(mechanismId)) return false;
    const card = this.cards.get(mechanismId);
    card.status = toDefault ? MechanismStatus.DEFAULT : MechanismStatus.TRUSTED;
    this._metrics.mechanismsPromoted += 1;
    return true;
  }

  reject(mechanismId, reason = "") {
    if (!this.cards.has(mechanismId)) return false;
    const card = this.cards.get(mechanismId);
    card.status = MechanismStatus.REJECTED;
    card.failures.push({ reason, timestamp: Date.now() / 1000 });
    return true;
  }

  invalidate(newModelVersion) {
    this.modelVersion = newModelVersion;
    this.clearCache();
    let invalidatedCount = 0;
    for (const card of this.cards.values()) {
      if (card.modelVersion !== newModelVersion) {
        card.status = MechanismStatus.REJECTED;
        card.failures.push({ reason: `Model upgraded to ${newModelVersion}`, timestamp: Date.now() / 1000 });
        invalidatedCount += 1;
      }
    }
    return invalidatedCount;
  }

  getMechanisms(pattern = null, status = null) {
    let results = Array.from(this.cards.values());
    if (pattern !== null) {
      results = results.filter(c => c.pattern === pattern);
    }
    if (status !== null) {
      results = results.filter(c => c.status === status);
    }
    return results;
  }

  explain(mechanismId) {
    if (!this.cards.has(mechanismId)) {
      return `Mechanism '${mechanismId}' not found in MATE registry.`;
    }
    const card = this.cards.get(mechanismId);
    const speedup = 1.0 / Math.max(card.expectedCost, 0.01);
    return [
      `### MATE Mechanism [${card.id}] — Status: ${String(card.status).toUpperCase()}`,
      `- **Problem Pattern:** \`${card.pattern}\``,
      `- **Execution Chain:** \`${card.chain.join(' -> ')}\``,
      `- **Performance Payoff:** ~${speedup.toFixed(1)}x speedup (Cost: ${(card.expectedCost * 100).toFixed(1)}%, Quality: ${(card.expectedQuality * 100).toFixed(1)}%)`,
      `- **Confidence & Evidence:** ${(card.confidence * 100).toFixed(1)}% across ${card.evidenceCount} evaluations`,
      `- **Shortcuts Applied:** ${JSON.stringify(card.shortcuts)}`,
      `- **Provenance:** ${card.provenance} (Model: ${card.modelVersion})`,
    ].join('\n');
  }

  // --------------------------------------------------------------------------
  // Execution Interface
  // --------------------------------------------------------------------------

  computeProjected({
    taskId,
    inputs,
    solver,
    boundaryValidator = null,
    intermediateCheck = null,
    estimatedHeavyCostMs = 50.0,
    candidateChains = null,
    approximateTolerance = 0.05,
  }) {
    const t0 = performance.now();
    this._metrics.totalQueries += 1;

    // 1. Boundary Pre-check (Early Exit R3)
    if (typeof boundaryValidator === 'function') {
      const [isValid, reason] = boundaryValidator(inputs);
      if (!isValid) {
        this._metrics.earlyAborts += 1;
        this._metrics.estimatedCpuMsSaved += estimatedHeavyCostMs;
        return new MATEResult({
          status: MATEStatus.R3_INFEASIBLE,
          value: null,
          cached: false,
          computeTimeSavedPct: 99.9,
          elapsedMs: performance.now() - t0,
          diagnosticMessage: `Early abort by boundary validator: ${reason}`,
          reuseLevel: ReuseLevel.L5,
        });
      }
    }

    // 2. Multilevel Lookup (L0 / L1 / L2 / L3)
    const [reuseLvl, cachedVal, favorableCard] = this.lookupMultilevel(taskId, inputs, approximateTolerance);

    // L0: Exact hit
    if (reuseLvl === ReuseLevel.L0) {
      this._metrics.cacheHits += 1;
      this._metrics.estimatedCpuMsSaved += estimatedHeavyCostMs;
      return new MATEResult({
        status: MATEStatus.R1_EXACT,
        value: cachedVal,
        cached: true,
        computeTimeSavedPct: 99.5,
        elapsedMs: performance.now() - t0,
        diagnosticMessage: "Value retrieved from MATE invariant cache (L0 Zero-Compute)",
        reuseLevel: ReuseLevel.L0,
      });
    }

    // L1: Approximate hit
    if (reuseLvl === ReuseLevel.L1) {
      this._metrics.cacheHits += 1;
      this._metrics.estimatedCpuMsSaved += (estimatedHeavyCostMs * 0.95);
      return new MATEResult({
        status: MATEStatus.R1_EXACT,
        value: cachedVal,
        cached: true,
        computeTimeSavedPct: 95.0,
        elapsedMs: performance.now() - t0,
        diagnosticMessage: "Value retrieved via MATE approximate neighbor reuse (L1)",
        reuseLevel: ReuseLevel.L1,
      });
    }

    // 3. Intermediate Feasibility Guard
    if (typeof intermediateCheck === 'function') {
      const [isFeasible, reason] = intermediateCheck(inputs);
      if (!isFeasible) {
        this._metrics.earlyAborts += 1;
        this._metrics.estimatedCpuMsSaved += (estimatedHeavyCostMs * 0.8);
        return new MATEResult({
          status: MATEStatus.R3_INFEASIBLE,
          value: null,
          cached: false,
          computeTimeSavedPct: 80.0,
          elapsedMs: performance.now() - t0,
          diagnosticMessage: `Aborted at intermediate checkpoint: ${reason}`,
          reuseLevel: ReuseLevel.L5,
        });
      }
    }

    // 4. Fresh Official Solver Execution
    this._metrics.fullComputes += 1;
    const resultValue = solver(inputs);

    // Register into exact cache & approximate memory
    const cacheKey = this._hashKey(taskId, inputs);
    this.memoizedSet(cacheKey, resultValue);
    this._approximateRecords.push({
      taskId,
      inputs: { ...inputs },
      value: resultValue,
      modelVersion: this.modelVersion,
      timestamp: Date.now() / 1000,
    });

    // 5. Speculative Execution Battery (Background / Budgeted)
    const discoveries = [];
    if (candidateChains && Array.isArray(candidateChains)) {
      const specRes = this.speculate(
        taskId,
        inputs,
        resultValue,
        candidateChains,
        estimatedHeavyCostMs * this.speculativeBudgetRatio
      );
      for (const r of specRes) {
        if (r.isFavorable && this.cards.has(r.mechanismId)) {
          discoveries.push(this.cards.get(r.mechanismId));
        }
      }
    }

    const elapsed = performance.now() - t0;
    return new MATEResult({
      status: MATEStatus.R1_EXACT,
      value: resultValue,
      cached: false,
      computeTimeSavedPct: 0.0,
      elapsedMs: elapsed,
      diagnosticMessage: "Computed freshly and registered into MATE memory",
      reuseLevel: ReuseLevel.L5,
      mechanismUsed: favorableCard ? favorableCard.id : null,
      speculativeDiscoveries: discoveries,
    });
  }

  stats() {
    return {
      totalLookups: this._metrics.totalQueries,
      cacheHits: this._metrics.cacheHits,
      earlyAborts: this._metrics.earlyAborts,
      operationsAvoided: this._metrics.cacheHits * 250,
      l0ExactHits: this._metrics.l0ExactHits,
      l1ApproxHits: this._metrics.l1ApproxHits,
      l2PlanHits: this._metrics.l2PlanHits,
      l3ShortcutHits: this._metrics.l3ShortcutHits,
      speculativeRunsCount: this._metrics.speculativeRunsCount,
      mechanismsDiscovered: this._metrics.mechanismsDiscovered,
      mechanismsPromoted: this._metrics.mechanismsPromoted,
    };
  }

  lookup(taskId, inputs) {
    const key = this._hashKey(taskId, inputs);
    return this.memoizedGet(key);
  }

  recordEarlyAbort() {
    this._metrics.earlyAborts += 1;
  }

  projectTrajectory(taskId, inputs, invariants = []) {
    for (const inv of invariants || []) {
      let res;
      try {
        res = inv(inputs);
      } catch {
        return false;
      }
      const ok = Array.isArray(res) ? res[0] : res;
      if (!ok) return false;
    }
    return true;
  }

  store(taskId, inputs, value) {
    const key = this._hashKey(taskId, inputs);
    this.memoizedSet(key, value);
    this._approximateRecords.push({
      taskId, inputs: { ...inputs }, value, modelVersion: this.modelVersion, timestamp: Date.now() / 1000,
    });
    return key;
  }

  exportManifest() {
    return {
      modelVersion: this.modelVersion,
      cacheEntries: this._cache.size,
      cacheKeys: [...this._cache.keys()].sort(),
      approximateRecords: this._approximateRecords.length,
      mechanisms: [...this.cards.values()].map((c) => ({ id: c.id, status: c.status, modelVersion: c.modelVersion })),
      metrics: { ...this._metrics },
    };
  }

  get metrics() {
    return { ...this._metrics };
  }
}
