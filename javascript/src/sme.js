/**
 * sfsa.sme — Surrogate Modeling Engine (SME)
 * ==========================================
 * Synthesizes lightweight, compact response surface models (Radial Basis Functions / IDW)
 * in real-time from evaluated high-fidelity points. Provides the automatic "cheap model" required by AMF,
 * allowing non-ML researchers to benefit from multi-fidelity acceleration without writing surrogates manually.
 *
 * Part of SFSA (Standard Framework for Scientific Advancement)
 * Author & Protocol Creator: Alejo Malia
 * License: CC BY 4.0
 */

export class SurrogateModel {
  constructor({ featureNames, samplePoints, sampleValues, rbfEpsilon = 1.0 }) {
    this.featureNames = featureNames;
    this.samplePoints = samplePoints;
    this.sampleValues = sampleValues;
    this.rbfEpsilon = rbfEpsilon;
  }

  predict(point) {
    if (!this.samplePoints || this.samplePoints.length === 0) {
      return { value: 0.0, uncertainty: 1.0 };
    }

    const distances = [];
    for (const p of this.samplePoints) {
      let sq = 0;
      for (const k of this.featureNames) {
        if (point[k] !== undefined && p[k] !== undefined) {
          sq += (point[k] - p[k]) ** 2;
        }
      }
      distances.push(Math.sqrt(sq));
    }

    const minDist = Math.min(...distances);

    if (minDist < 1e-9) {
      const idx = distances.indexOf(minDist);
      return { value: this.sampleValues[idx], uncertainty: 0.0 };
    }

    // IDW
    const weights = distances.map(d => 1.0 / (d ** 2 + 1e-12));
    const totalW = weights.reduce((acc, w) => acc + w, 0);
    const interpolated = weights.reduce((acc, w, idx) => acc + w * this.sampleValues[idx], 0) / totalW;

    const uncertainty = Math.min(1.0, minDist * 0.5);

    return { value: interpolated, uncertainty };
  }
}

export class SurrogateModelingEngine {
  constructor() {
    this.surrogates = new Map();
  }

  fitFromHistory(modelId, points, values) {
    if (!points || !values || points.length === 0 || points.length !== values.length) {
      throw new Error('Points and values must be non-empty and of equal length.');
    }

    const featureNames = Object.keys(points[0]);
    const surrogate = new SurrogateModel({
      featureNames,
      samplePoints: points.map(p => ({ ...p })),
      sampleValues: [...values]
    });

    this.surrogates.set(modelId, surrogate);
    return surrogate;
  }

  createAmfSolver(modelId) {
    const surrogate = this.surrogates.get(modelId);
    if (!surrogate) {
      throw new Error(`Surrogate '${modelId}' not found.`);
    }

    return (inputs) => {
      const pred = surrogate.predict(inputs);
      return { value: pred.value, uncertainty: pred.uncertainty };
    };
  }
}
