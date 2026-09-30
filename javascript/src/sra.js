/**
 * sfsa.sra — Sensitivity & Reduction Analyzer (SRA)
 * ================================================
 * Quantifies local and global parameter sensitivities; projects into active lower-dimensional subspaces.
 *
 * Part of SFSA (Standard Framework for Scientific Advancement)
 * Author & Protocol Creator: Alejo Malia
 * License: CC BY 4.0
 */

export class SensitivityReductionAnalyzer {
  constructor(sensitivityThreshold = 0.05) {
    this.sensitivityThreshold = sensitivityThreshold;
    this.profiles = {};
  }

  analyzeOneAtATime(baseInputs, objectiveFn, perturbationDelta = 0.01) {
    const baseVal = objectiveFn(baseInputs);
    const gradients = {};
    let totalMag = 0.0;

    for (const [k, v] of Object.entries(baseInputs)) {
      const perturbed = { ...baseInputs };
      const delta = Math.abs(v) > 1e-9 ? Math.abs(v) * perturbationDelta : perturbationDelta;
      perturbed[k] = v + delta;
      const perturbedVal = objectiveFn(perturbed);
      const grad = Math.abs((perturbedVal - baseVal) / delta);
      gradients[k] = grad;
      totalMag += grad;
    }

    const results = [];
    for (const [k, grad] of Object.entries(gradients)) {
      const index = totalMag > 1e-12 ? grad / totalMag : 0.0;
      const impactful = index >= this.sensitivityThreshold;
      const prof = {
        parameterName: k,
        firstOrderIndex: index,
        isImpactful: impactful,
        effectiveGradient: grad,
        description: impactful ? `Impactful (${(index * 100).toFixed(1)}%)` : `Insensitive (${(index * 100).toFixed(1)}%)`
      };
      this.profiles[k] = prof;
      results.push(prof);
    }

    return results.sort((a, b) => b.firstOrderIndex - a.firstOrderIndex);
  }

  reduceParameterSpace(baseInputs, objectiveFn, targetVarianceExplained = 0.95) {
    const profiles = this.analyzeOneAtATime(baseInputs, objectiveFn);
    const retained = [];
    const pruned = [];
    let accumulated = 0.0;

    for (const p of profiles) {
      if (accumulated < targetVarianceExplained || p.isImpactful) {
        retained.push(p.parameterName);
        accumulated += p.firstOrderIndex;
      } else {
        pruned.push(p.parameterName);
      }
    }

    return {
      originalDimension: Object.keys(baseInputs).length,
      reducedDimension: retained.length,
      retainedParameters: retained,
      prunedParameters: pruned,
      varianceRetainedRatio: Math.min(1.0, accumulated)
    };
  }
}
