/**
 * sfsa.uas — Uncertainty-Aware Stopping Engine (UAS)
 * =================================================
 * Evaluates whether residual numerical error can alter qualitative scientific conclusions.
 *
 * Part of SFSA (Standard Framework for Scientific Advancement)
 * Author & Protocol Creator: Alejo Malia
 * License: CC BY 4.0
 */

export class UncertaintyAwareStoppingEngine {
  constructor(targetTolerance = 1e-4, minIterationsBeforeStop = 3) {
    this.targetTolerance = targetTolerance;
    this.minIterationsBeforeStop = minIterationsBeforeStop;
  }

  evaluateStep({
    iteration,
    currentValue,
    previousValue = null,
    maxPlannedIterations = 100,
    scientificThreshold = null,
    estimatedUncertainty = null,
    customTolerance = null
  }) {
    const tol = customTolerance !== null ? customTolerance : this.targetTolerance;
    const residual = previousValue !== null ? Math.abs(currentValue - previousValue) : 1.0;
    const unc = estimatedUncertainty !== null ? estimatedUncertainty : residual;

    if (iteration < this.minIterationsBeforeStop) {
      return {
        iteration,
        currentValue,
        currentResidual: residual,
        currentUncertainty: unc,
        targetTolerance: tol,
        shouldStop: false,
        iterationsSaved: 0,
        rationale: "Under minimum initial iterations"
      };
    }

    if (residual <= tol && unc <= tol) {
      return {
        iteration,
        currentValue,
        currentResidual: residual,
        currentUncertainty: unc,
        targetTolerance: tol,
        shouldStop: true,
        iterationsSaved: Math.max(0, maxPlannedIterations - iteration),
        rationale: `Tolerance satisfied: residual ${residual.toExponential(2)} <= ${tol.toExponential(2)}`
      };
    }

    if (scientificThreshold !== null) {
      const dist = Math.abs(currentValue - scientificThreshold);
      if (dist > 5.0 * unc && residual < 10.0 * tol) {
        return {
          iteration,
          currentValue,
          currentResidual: residual,
          currentUncertainty: unc,
          targetTolerance: tol,
          shouldStop: true,
          iterationsSaved: Math.max(0, maxPlannedIterations - iteration),
          rationale: `Scientific conclusion invariant: distance to boundary (${dist.toFixed(3)}) > 5x unc`
        };
      }
    }

    return {
      iteration,
      currentValue,
      currentResidual: residual,
      currentUncertainty: unc,
      targetTolerance: tol,
      shouldStop: false,
      iterationsSaved: 0,
      rationale: `Continuing: residual (${residual.toExponential(2)}) > tol`
    };
  }
}
