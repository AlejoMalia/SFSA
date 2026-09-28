/**
 * sfsa.projection — LayerConsistencyProjector (Layer Coupling & Consistency Projector)
 * =====================================================================================
 * Evaluates coupling, vector distance, and parameter consistency between framework layers.
 * Detects parameter conflicts, bound violations, and high-affinity scaling relationships
 * without ungrounded metaphysical claims.
 *
 * Part of SFSA (Standard Framework for Scientific Advancement)
 * Author & Protocol Creator: Alejo Malia
 * License: CC BY 4.0
 */

export class ParameterCoupling {
  constructor({
    sourceLayer,
    targetLayer,
    sourceParam,
    targetParam,
    correlationRatio,
    normalizedAffinity,
    description = "",
  }) {
    this.sourceLayer = sourceLayer;
    this.targetLayer = targetLayer;
    this.sourceParam = sourceParam;
    this.targetParam = targetParam;
    this.correlationRatio = correlationRatio;
    this.normalizedAffinity = normalizedAffinity;
    this.description = description;
  }
}

export class InconsistencyConflict {
  constructor({
    layerA,
    layerB,
    parameterName,
    valueInA,
    valueInB,
    conflictType,
    description = "",
  }) {
    this.layerA = layerA;
    this.layerB = layerB;
    this.parameterName = parameterName;
    this.valueInA = valueInA;
    this.valueInB = valueInB;
    this.conflictType = conflictType; // 'VALUE_MISMATCH' | 'BOUND_VIOLATION'
    this.description = description;
  }
}

export class LayerConsistencyReport {
  constructor({
    layersEvaluated = [],
    totalParametersCompared = 0,
    normalizedVectorDistance = 0.0,
    stronglyCoupledPairs = [],
    inconsistencies = [],
    diagnosticSummary = [],
  }) {
    this.layersEvaluated = layersEvaluated;
    this.totalParametersCompared = totalParametersCompared;
    this.normalizedVectorDistance = normalizedVectorDistance;
    this.stronglyCoupledPairs = stronglyCoupledPairs;
    this.inconsistencies = inconsistencies;
    this.diagnosticSummary = diagnosticSummary;
  }
}

export class LayerConsistencyProjector {
  constructor({ affinityThreshold = 0.25 } = {}) {
    this.affinityThreshold = affinityThreshold;
    this._history = [];
  }

  _extractNumericVector(state) {
    const res = {};
    for (const [k, v] of Object.entries(state)) {
      if (typeof v === 'boolean') {
        res[k] = v ? 1.0 : 0.0;
      } else if (typeof v === 'number' && !Number.isNaN(v)) {
        res[k] = v;
      }
    }
    return res;
  }

  projectAndIntersect({
    layerAId,
    layerAState,
    layerBId,
    layerBState,
    knownBounds = {},
    parameterAliases = {},
  }) {
    const vecA = this._extractNumericVector(layerAState);
    const vecB = this._extractNumericVector(layerBState);

    const inconsistencies = [];
    const stronglyCoupled = [];
    const diagnostics = [];

    // 1. Shared Parameter Conflict Check
    const canonicalA = {};
    for (const [k, v] of Object.entries(vecA)) {
      canonicalA[parameterAliases[k] || k] = { orig: k, val: v };
    }
    const canonicalB = {};
    for (const [k, v] of Object.entries(vecB)) {
      canonicalB[parameterAliases[k] || k] = { orig: k, val: v };
    }

    const sharedParams = Object.keys(canonicalA).filter((p) => p in canonicalB);

    for (const p of sharedParams) {
      const valA = canonicalA[p].val;
      const valB = canonicalB[p].val;

      // A. Value mismatch check
      const denom = Math.max(Math.abs(valA), Math.abs(valB), 1e-9);
      const relDiff = Math.abs(valA - valB) / denom;
      if (relDiff > 0.01) {
        inconsistencies.push(
          new InconsistencyConflict({
            layerA: layerAId,
            layerB: layerBId,
            parameterName: p,
            valueInA: valA,
            valueInB: valB,
            conflictType: "VALUE_MISMATCH",
            description: `Parameter '${p}' has conflicting values: ${valA} in '${layerAId}' vs ${valB} in '${layerBId}' (diff: ${(relDiff * 100).toFixed(1)}%).`,
          })
        );
      }

      // B. Bound violation check
      if (knownBounds[p]) {
        const [pMin, pMax] = knownBounds[p];
        for (const [lid, val] of [[layerAId, valA], [layerBId, valB]]) {
          if (val < pMin || val > pMax) {
            inconsistencies.push(
              new InconsistencyConflict({
                layerA: layerAId,
                layerB: layerBId,
                parameterName: p,
                valueInA: valA,
                valueInB: valB,
                conflictType: "BOUND_VIOLATION",
                description: `Value ${val} in layer '${lid}' violates allowable bound [${pMin}, ${pMax}].`,
              })
            );
          }
        }
      }
    }

    // 2. Vector distance (normalized cosine distance)
    const normA = Math.sqrt(Object.values(vecA).reduce((acc, v) => acc + v ** 2, 0)) || 1.0;
    const normB = Math.sqrt(Object.values(vecB).reduce((acc, v) => acc + v ** 2, 0)) || 1.0;
    const sharedKeys = Object.keys(vecA).filter((k) => k in vecB);
    const overlap = sharedKeys.reduce((acc, k) => acc + vecA[k] * vecB[k], 0);
    const cosTheta = Math.min(1.0, Math.max(0.0, Math.abs(overlap) / (normA * normB)));
    const normalizedDistance = 1.0 - cosTheta;

    // 3. Cross-layer Parameter Affinity
    for (const [kA, valA] of Object.entries(vecA)) {
      for (const [kB, valB] of Object.entries(vecB)) {
        if (Math.abs(valA) > 1e-12 && Math.abs(valB) > 1e-12) {
          const ratio = valA / valB;
          const logRatio = Math.abs(Math.log10(Math.abs(ratio) + 1e-15));
          const affinity = Math.max(0.0, Math.min(1.0, 1.0 - logRatio / 6.0));

          if (affinity >= this.affinityThreshold) {
            stronglyCoupled.push(
              new ParameterCoupling({
                sourceLayer: layerAId,
                targetLayer: layerBId,
                sourceParam: kA,
                targetParam: kB,
                correlationRatio: ratio,
                normalizedAffinity: affinity,
                description: `Scaling relation between ${layerAId}.${kA} and ${layerBId}.${kB} (ratio: ${ratio.toExponential(3)}).`,
              })
            );
          }
        }
      }
    }

    if (inconsistencies.length > 0) {
      diagnostics.push(`Detected ${inconsistencies.length} parameter inconsistencies between '${layerAId}' and '${layerBId}'.`);
    } else {
      diagnostics.push(`Layers '${layerAId}' and '${layerBId}' are mutually consistent within tolerance.`);
    }

    const report = new LayerConsistencyReport({
      layersEvaluated: [layerAId, layerBId],
      totalParametersCompared: Object.keys(vecA).length + Object.keys(vecB).length,
      normalizedVectorDistance: normalizedDistance,
      stronglyCoupledPairs: stronglyCoupled,
      inconsistencies,
      diagnosticSummary: diagnostics,
    });

    this._history.push(report);
    return report;
  }

  get projectionHistory() {
    return [...this._history];
  }
}

// Aliases for compatibility
export const DimensionalProjectionEngine = LayerConsistencyProjector;
export const ManifoldIntersectionReport = LayerConsistencyReport;
export const LatentCoupling = ParameterCoupling;
