/**
 * sfsa.uqe — Uncertainty Propagation Engine (UQE)
 * ==============================================
 * Propagates parametric uncertainties, confidence intervals, and error variances through framework
 * layers and reactive DAGs without demanding brute-force Monte Carlo sampling (10,000 runs).
 * Applies analytical first-order error propagation (covariance Taylor expansion) and interval arithmetic.
 *
 * Part of SFSA (Standard Framework for Scientific Advancement)
 * Author & Protocol Creator: Alejo Malia
 * License: CC BY 4.0
 */

export class UncertaintyInterval {
  constructor({ nominal, uncertainty, confidenceLevel = 0.95 }) {
    this.nominal = nominal;
    this.uncertainty = uncertainty;
    this.confidenceLevel = confidenceLevel;
  }

  get lower() {
    const z = this.confidenceLevel === 0.95 ? 1.96 : 1.0;
    return this.nominal - z * this.uncertainty;
  }

  get upper() {
    const z = this.confidenceLevel === 0.95 ? 1.96 : 1.0;
    return this.nominal + z * this.uncertainty;
  }

  get relativeUncertainty() {
    return Math.abs(this.uncertainty / Math.max(Math.abs(this.nominal), 1e-12));
  }
}

export class UncertaintyPropagationEngine {
  constructor(defaultConfidence = 0.95) {
    this.defaultConfidence = defaultConfidence;
  }

  combineBinary(a, b, operation) {
    let nom = 0;
    let unc = 0;

    if (operation === '+') {
      nom = a.nominal + b.nominal;
      unc = Math.sqrt(a.uncertainty ** 2 + b.uncertainty ** 2);
    } else if (operation === '-') {
      nom = a.nominal - b.nominal;
      unc = Math.sqrt(a.uncertainty ** 2 + b.uncertainty ** 2);
    } else if (operation === '*') {
      nom = a.nominal * b.nominal;
      const relSq = (a.uncertainty / Math.max(Math.abs(a.nominal), 1e-12)) ** 2 +
                    (b.uncertainty / Math.max(Math.abs(b.nominal), 1e-12)) ** 2;
      unc = Math.abs(nom) * Math.sqrt(relSq);
    } else if (operation === '/') {
      const denom = Math.abs(b.nominal) > 1e-12 ? b.nominal : 1e-12;
      nom = a.nominal / denom;
      const relSq = (a.uncertainty / Math.max(Math.abs(a.nominal), 1e-12)) ** 2 +
                    (b.uncertainty / Math.max(Math.abs(b.nominal), 1e-12)) ** 2;
      unc = Math.abs(nom) * Math.sqrt(relSq);
    } else {
      throw new Error(`Unsupported operation: ${operation}`);
    }

    return new UncertaintyInterval({
      nominal: nom,
      uncertainty: unc,
      confidenceLevel: this.defaultConfidence
    });
  }

  propagateGeneral(fn, inputs, finiteDifferenceStep = 1e-4) {
    const nominalDict = {};
    for (const [k, v] of Object.entries(inputs)) {
      nominalDict[k] = v.nominal;
    }

    const baseOutput = fn(nominalDict);
    let varianceSum = 0;
    const contributions = {};

    for (const [k, interval] of Object.entries(inputs)) {
      const h = Math.max(Math.abs(interval.nominal) * finiteDifferenceStep, finiteDifferenceStep);
      const perturbedPlus = { ...nominalDict, [k]: nominalDict[k] + h };
      const perturbedMinus = { ...nominalDict, [k]: nominalDict[k] - h };

      const dfDx = (fn(perturbedPlus) - fn(perturbedMinus)) / (2.0 * h);
      const paramVariance = (dfDx * interval.uncertainty) ** 2;
      varianceSum += paramVariance;
      contributions[k] = paramVariance;
    }

    const totalSigma = Math.sqrt(varianceSum);
    const outputInterval = new UncertaintyInterval({
      nominal: baseOutput,
      uncertainty: totalSigma,
      confidenceLevel: this.defaultConfidence
    });

    const dominantContributors = Object.entries(contributions)
      .map(([k, varVal]) => [k, varianceSum > 0 ? varVal / varianceSum : 0])
      .sort((a, b) => b[1] - a[1]);

    return {
      outputInterval,
      dominantContributors,
      formulaDerivation: `First-order Taylor expansion over ${Object.keys(inputs).length} dimensions`
    };
  }
}
