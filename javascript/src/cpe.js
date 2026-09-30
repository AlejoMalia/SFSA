/**
 * sfsa.cpe — Computational Provenance & Reuse Engine (CPE)
 * =======================================================
 * Manages scientific provenance metadata and allows approximate reuse within tolerances.
 *
 * Part of SFSA (Standard Framework for Scientific Advancement)
 * Author & Protocol Creator: Alejo Malia
 * License: CC BY 4.0
 */

export const ReuseType = {
  EXACT_CACHE: 'EXACT_CACHE',
  APPROXIMATE_REUSE: 'APPROXIMATE_REUSE',
  WARM_START: 'WARM_START',
  FULL_COMPUTATION: 'FULL_COMPUTATION'
};

export class ComputationalProvenanceEngine {
  constructor(approximateTolerance = 0.02) {
    this.approximateTolerance = approximateTolerance;
    this.records = new Map();
  }

  registerResult({
    taskId,
    inputs,
    output,
    modelVersion = "1.0.0",
    numericalMethod = "analytical_or_numerical",
    tolerances = {},
    dependencies = [],
    context = {}
  }) {
    const recId = `cpe_${taskId}_${this.records.size + 1}_${Date.now()}`;
    const record = {
      recordId: recId,
      taskId,
      modelVersion,
      inputs: { ...inputs },
      output,
      numericalMethod,
      tolerances,
      dependencies,
      context,
      timestamp: Date.now(),
      reuseCount: 0
    };
    this.records.set(recId, record);
    return record;
  }

  assessReuse(taskId, targetInputs, customTolerance = null, requiredModelVersion = null) {
    const tol = customTolerance !== null ? customTolerance : this.approximateTolerance;
    const candidates = Array.from(this.records.values()).filter(
      r => r.taskId === taskId && (requiredModelVersion === null || r.modelVersion === requiredModelVersion)
    );

    if (candidates.length === 0) {
      return {
        reuseType: ReuseType.FULL_COMPUTATION,
        matchedRecordId: null,
        deltaNorm: 1.0,
        confidence: 0.0,
        value: null,
        rationale: "No prior calculation exists for this task"
      };
    }

    let bestRecord = null;
    let minDelta = Infinity;

    for (const r of candidates) {
      const keys = Object.keys(targetInputs).filter(k => k in r.inputs);
      if (keys.length === 0) continue;

      let sumDiff = 0.0;
      for (const k of keys) {
        const vT = targetInputs[k];
        const vC = r.inputs[k];
        if (typeof vT === 'number' && typeof vC === 'number') {
          const denom = Math.max(Math.abs(vC), 1.0);
          sumDiff += Math.abs(vT - vC) / denom;
        } else if (vT === vC) {
          sumDiff += 0.0;
        } else {
          sumDiff += 1.0;
        }
      }
      const delta = sumDiff / keys.length;
      if (delta < minDelta) {
        minDelta = delta;
        bestRecord = r;
      }
    }

    if (!bestRecord) {
      return {
        reuseType: ReuseType.FULL_COMPUTATION,
        matchedRecordId: null,
        deltaNorm: 1.0,
        confidence: 0.0,
        value: null,
        rationale: "Incompatible signatures"
      };
    }

    if (minDelta < 1e-12) {
      bestRecord.reuseCount += 1;
      return {
        reuseType: ReuseType.EXACT_CACHE,
        matchedRecordId: bestRecord.recordId,
        deltaNorm: 0.0,
        confidence: 1.0,
        value: bestRecord.output,
        rationale: "Exact provenance match"
      };
    }

    if (minDelta <= tol) {
      bestRecord.reuseCount += 1;
      return {
        reuseType: ReuseType.APPROXIMATE_REUSE,
        matchedRecordId: bestRecord.recordId,
        deltaNorm: minDelta,
        confidence: 1.0 - (minDelta / tol) * 0.2,
        value: bestRecord.output,
        rationale: `Approximate reuse valid: delta (${minDelta.toFixed(4)}) <= tol (${tol})`
      };
    }

    if (minDelta <= tol * 5.0) {
      return {
        reuseType: ReuseType.WARM_START,
        matchedRecordId: bestRecord.recordId,
        deltaNorm: minDelta,
        confidence: 0.5,
        value: bestRecord.output,
        rationale: `Candidate suitable for warm-starting (delta=${minDelta.toFixed(4)})`
      };
    }

    return {
      reuseType: ReuseType.FULL_COMPUTATION,
      matchedRecordId: bestRecord.recordId,
      deltaNorm: minDelta,
      confidence: 0.0,
      value: null,
      rationale: `Delta exceeds tolerance`
    };
  }
}
