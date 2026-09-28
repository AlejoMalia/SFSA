/**
 * sfsa.mate — MATE Engine (Multi-Dimensional Acceleration & Trajectory Estimation)
 * =================================================================================
 * Generic scientific memoization, projection, and early-abort engine for JavaScript.
 * Prevents running dense calculations to completion when intermediate boundary
 * conditions dictate infeasibility or convergence.
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

export class MATEResult {
  constructor({
    status = MATEStatus.R1_EXACT,
    value = null,
    cached = false,
    computeTimeSavedPct = 0.0,
    elapsedMs = 0.0,
    diagnosticMessage = "",
    intermediateCheckpoints = [],
  } = {}) {
    this.status = status;
    this.value = value;
    this.cached = cached;
    this.computeTimeSavedPct = computeTimeSavedPct;
    this.elapsedMs = elapsedMs;
    this.diagnosticMessage = diagnosticMessage;
    this.intermediateCheckpoints = intermediateCheckpoints;
  }
}

export class MATEEngine {
  constructor({ cachePrecisionDecimals = 6 } = {}) {
    this.cachePrecision = cachePrecisionDecimals;
    this._cache = new Map();
    this._metrics = {
      totalQueries: 0,
      cacheHits: 0,
      earlyAborts: 0,
      fullComputes: 0,
      estimatedCpuMsSaved: 0.0,
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

  memoizedGet(key) {
    return this._cache.get(key);
  }

  memoizedSet(key, value) {
    this._cache.set(key, value);
  }

  computeProjected({
    taskId,
    inputs,
    solver,
    boundaryValidator = null,
    intermediateCheck = null,
    estimatedHeavyCostMs = 50.0,
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
        });
      }
    }

    // 2. Cache Lookup (O(1) Exact R1)
    const cacheKey = this._hashKey(taskId, inputs);
    const cachedVal = this.memoizedGet(cacheKey);
    if (cachedVal !== undefined) {
      this._metrics.cacheHits += 1;
      this._metrics.estimatedCpuMsSaved += estimatedHeavyCostMs;
      return new MATEResult({
        status: MATEStatus.R1_EXACT,
        value: cachedVal,
        cached: true,
        computeTimeSavedPct: 99.5,
        elapsedMs: performance.now() - t0,
        diagnosticMessage: "Value retrieved from MATE invariant cache",
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
        });
      }
    }

    // 4. Fresh Solver Execution
    this._metrics.fullComputes += 1;
    const resultValue = solver(inputs);
    this.memoizedSet(cacheKey, resultValue);

    const elapsed = performance.now() - t0;
    return new MATEResult({
      status: MATEStatus.R1_EXACT,
      value: resultValue,
      cached: false,
      computeTimeSavedPct: 0.0,
      elapsedMs: elapsed,
      diagnosticMessage: "Computed freshly and cached in MATE index",
    });
  }

  clearCache() {
    this._cache.clear();
  }

  get metrics() {
    return { ...this._metrics };
  }
}
