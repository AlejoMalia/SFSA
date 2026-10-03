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
  NUMERICAL_DISCRETIZATION: 'NUMERICAL_DISCRETIZATION',
  MODELING_ASSUMPTION: 'MODELING_ASSUMPTION',
  REGIME_BREAKDOWN: 'REGIME_BREAKDOWN',
  ERRONEOUS_CONVERGENCE: 'ERRONEOUS_CONVERGENCE'
};

export class DiscrepancyIntelligenceEngine {
  constructor(numericalEpsilon = 0.01, severeDiscrepancyThreshold = 0.15) {
    this.numericalEpsilon = numericalEpsilon;
    this.severeThreshold = severeDiscrepancyThreshold;
  }

  /**
   * A difference between two solutions of the same equations (sameModel: different step, mesh, integrator such as
   * Euler vs RK4) is discretization error, not a modeling assumption. It is also classified as discretization when
   * the gap is within discretizationError (an absolute error estimate, e.g. from richardson()).
   */
  analyze(sourceA, valueA, sourceB, valueB, referenceSolver = null, { sameModel = false, discretizationError = null } = {}) {
    if (discretizationError !== null && !(discretizationError >= 0)) throw new Error('discretizationError must be >= 0');
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

    const withinEstimate = discretizationError !== null && Math.abs(valueA - valueB) <= discretizationError;
    if ((sameModel && relDiff <= this.severeThreshold) || withinEstimate) {
      return {
        sourceA, sourceB, valueA, valueB,
        relativeDiscrepancy: relDiff,
        probableCause: DiscrepancyCause.NUMERICAL_DISCRETIZATION,
        recommendedAction: 'Same model, different discretization: refine the step/mesh or extrapolate (Richardson); prefer the finer solution',
        reconciledValue: null,
        confidence: withinEstimate ? 0.85 : 0.70
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

  /** Richardson extrapolation: returns [extrapolatedValue, estimatedErrorOfFineValue]. Euler order 1, RK4 order 4. */
  static richardson(valueCoarse, valueFine, order, stepRatio = 2.0) {
    if (!(order > 0) || !(stepRatio > 1)) throw new Error('order must be > 0 and stepRatio > 1');
    const extrapolated = valueFine + (valueFine - valueCoarse) / (stepRatio ** order - 1.0);
    return [extrapolated, Math.abs(extrapolated - valueFine)];
  }

  analyzeRefinement(sourceCoarse, valueCoarse, sourceFine, valueFine, order, stepRatio = 2.0) {
    const [extrapolated, err] = DiscrepancyIntelligenceEngine.richardson(valueCoarse, valueFine, order, stepRatio);
    const denom = Math.max(Math.abs(valueCoarse), Math.abs(valueFine), 1e-9);
    const small = err / Math.max(Math.abs(extrapolated), 1e-9) <= this.numericalEpsilon;
    return {
      sourceA: sourceCoarse, sourceB: sourceFine, valueA: valueCoarse, valueB: valueFine,
      relativeDiscrepancy: Math.abs(valueCoarse - valueFine) / denom,
      probableCause: DiscrepancyCause.NUMERICAL_DISCRETIZATION,
      recommendedAction: `Richardson extrapolation (order ${order}, ratio ${stepRatio}): estimated error of '${sourceFine}' is ${err.toPrecision(3)}${small ? '; resolved to the numerical tolerance.' : '; refine further.'}`,
      reconciledValue: extrapolated,
      confidence: small ? 0.9 : 0.65
    };
  }
}
