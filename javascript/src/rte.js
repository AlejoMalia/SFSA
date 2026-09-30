/**
 * sfsa.rte — Robustness & Stress-Testing Engine (RTE)
 * ==================================================
 * Audits model stability and hypothesis fragility under worst-case adversarial perturbations.
 * Identifies whether a theoretical conclusion is robust or dangerously fragile to small parameter
 * fluctuations, computing condition numbers and detecting bifurcation risks before publication.
 *
 * Part of SFSA (Standard Framework for Scientific Advancement)
 * Author & Protocol Creator: Alejo Malia
 * License: CC BY 4.0
 */

export class RobustnessTestingEngine {
  constructor(toleranceOutputDelta = 0.10) {
    this.toleranceOutputDelta = toleranceOutputDelta;
  }

  // A throw or non-finite output under perturbation is maximal fragility, not a reason to crash.
  _relDelta(modelFn, inputs, baseVal, denomBase, pName, pct, diagnostics) {
    let val;
    try {
      val = modelFn(inputs);
    } catch (err) {
      diagnostics.push(`Singularity on '${pName}' at ${(pct * 100).toFixed(1)}% shift: ${err && err.name}`);
      return Infinity;
    }
    if (!Number.isFinite(val)) {
      diagnostics.push(`Non-finite output on '${pName}' at ${(pct * 100).toFixed(1)}% shift`);
      return Infinity;
    }
    return Math.abs(val - baseVal) / denomBase;
  }

  stressTest(baseInputs, modelFn, perturbationPercentages = [0.01, 0.05, 0.10]) {
    const baseVal = modelFn(baseInputs);
    const denomBase = Math.max(Math.abs(baseVal), 1e-12);

    let worstRelDelta = 0.0;
    let mostSensitive = 'none';
    let maxConditionNum = 0.0;
    const diagnostics = [];

    for (const [pName, val] of Object.entries(baseInputs)) {
      for (const pct of perturbationPercentages) {
        const delta = Math.max(Math.abs(val) * pct, 1e-6);

        // Positive
        const inpPos = { ...baseInputs, [pName]: val + delta };
        const relDeltaPos = this._relDelta(modelFn, inpPos, baseVal, denomBase, pName, pct, diagnostics);

        // Negative
        const inpNeg = { ...baseInputs, [pName]: val - delta };
        const relDeltaNeg = this._relDelta(modelFn, inpNeg, baseVal, denomBase, pName, pct, diagnostics);

        const localWorst = Math.max(relDeltaPos, relDeltaNeg);
        const condNum = localWorst / Math.max(pct, 1e-6);

        if (condNum > maxConditionNum) {
          maxConditionNum = condNum;
          mostSensitive = pName;
        }

        if (localWorst > worstRelDelta) {
          worstRelDelta = localWorst;
        }

        if (localWorst > this.toleranceOutputDelta) {
          diagnostics.push(`Parameter '${pName}' perturbed by ${pct * 100}% caused ${localWorst * 100}% delta`);
        }
      }
    }

    const fragility = Math.min(1.0, maxConditionNum / 10.0);
    const isRobust = fragility < 0.35;
    const safeRadius = maxConditionNum > 0 ? (this.toleranceOutputDelta / maxConditionNum) : 1.0;

    return {
      isRobust,
      fragilityScore: fragility,
      conditionNumber: maxConditionNum,
      mostSensitiveParameter: mostSensitive,
      safePerturbationRadius: safeRadius,
      diagnosticDetails: diagnostics
    };
  }
}
