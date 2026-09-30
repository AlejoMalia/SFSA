/**
 * sfsa.die — Discrepancy Intelligence Engine (DIE)
 * ================================================
 * Diagnoses root causes of conflicting answers between solvers, surrogates, or fidelities.
 *
 * Part of SFSA (Standard Framework for Scientific Advancement)
 * Author & Protocol Creator: Alejo Malia
 * License: CC BY 4.0
 */

export const DiscrepancyCause = {
  NUMERICAL_TOLERANCE: 'NUMERICAL_TOLERANCE',
  MODELING_ASSUMPTION: 'MODELING_ASSUMPTION',
  REGIME_BREAKDOWN: 'REGIME_BREAKDOWN',
  ERRONEOUS_CONVERGENCE: 'ERRONEOUS_CONVERGENCE'
};

export class DiscrepancyIntelligenceEngine {
  constructor(numericalEpsilon = 0.01, severeDiscrepancyThreshold = 0.15) {
    this.numericalEpsilon = numericalEpsilon;
    this.severeThreshold = severeDiscrepancyThreshold;
  }

  analyze(sourceA, valueA, sourceB, valueB, referenceSolver = null) {
    const denom = Math.max(Math.abs(valueA), Math.abs(valueB), 1e-9);
    const relDiff = Math.abs(valueA - valueB) / denom;

    if (relDiff <= this.numericalEpsilon) {
      return {
        sourceA, sourceB, valueA, valueB,
        relativeDiscrepancy: relDiff,
        probableCause: DiscrepancyCause.NUMERICAL_TOLERANCE,
        recommendedAction: "Reconcile via arithmetic mean",
        reconciledValue: (valueA + valueB) / 2.0,
        confidence: 0.98
      };
    }

    if (relDiff <= this.severeThreshold) {
      return {
        sourceA, sourceB, valueA, valueB,
        relativeDiscrepancy: relDiff,
        probableCause: DiscrepancyCause.MODELING_ASSUMPTION,
        recommendedAction: "Apply constitutive correction factor",
        reconciledValue: (valueA + valueB) / 2.0,
        confidence: 0.75
      };
    }

    const refVal = referenceSolver ? referenceSolver() : null;
    return {
      sourceA, sourceB, valueA, valueB,
      relativeDiscrepancy: relDiff,
      probableCause: DiscrepancyCause.REGIME_BREAKDOWN,
      recommendedAction: refVal !== null ? `Escalated to reference solver: ${refVal}` : "Invalidation advised",
      reconciledValue: refVal !== null ? refVal : Math.max(valueA, valueB),
      confidence: refVal !== null ? 0.95 : 0.40
    };
  }
}
