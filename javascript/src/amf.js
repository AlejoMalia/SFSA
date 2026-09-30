/**
 * sfsa.amf — Adaptive Multi-Fidelity Engine (AMF)
 * ==============================================
 * Decides and routes computations across varying model fidelity levels (CHEAP vs. INTERMEDIATE vs. HIGH).
 * Accepts lower-fidelity approximations when estimated uncertainty is within calibrated scientific tolerances.
 *
 * Part of SFSA (Standard Framework for Scientific Advancement)
 * Author & Protocol Creator: Alejo Malia
 * License: CC BY 4.0
 */

export const FidelityLevel = {
  CHEAP: 'CHEAP',
  INTERMEDIATE: 'INTERMEDIATE',
  HIGH: 'HIGH'
};

export class AdaptiveMultiFidelityEngine {
  constructor(defaultTolerance = 0.05) {
    this.defaultTolerance = defaultTolerance;
    this.history = [];
    this.totalEvaluations = 0;
    this.cheapAcceptedCount = 0;
    this.escalationsCount = 0;
  }

  evaluate({
    taskId,
    inputs,
    cheapSolver,
    expensiveSolver,
    intermediateSolver = null,
    tolerance = null,
    benchmarkCostFactor = 100
  }) {
    const tol = tolerance !== null ? tolerance : this.defaultTolerance;
    this.totalEvaluations += 1;

    const t0 = Date.now();
    const { value: cheapVal, uncertainty: cheapUnc } = cheapSolver(inputs);
    const tCheap = Date.now() - t0;

    if (cheapUnc <= tol) {
      this.cheapAcceptedCount += 1;
      const decision = {
        taskId,
        selectedLevel: FidelityLevel.CHEAP,
        escalated: false,
        estimatedUncertainty: cheapUnc,
        uncertaintyTolerance: tol,
        executionTimeMs: tCheap,
        value: cheapVal,
        computeSavedRatio: 1.0 - (1.0 / Math.max(benchmarkCostFactor, 1)),
        rationale: `Cheap approximation uncertainty (${cheapUnc}) <= tolerance (${tol})`
      };
      this.history.push(decision);
      return decision;
    }

    if (intermediateSolver) {
      const tInt0 = Date.now();
      const { value: intVal, uncertainty: intUnc } = intermediateSolver(inputs);
      const tInt = (Date.now() - tInt0) + tCheap;
      if (intUnc <= tol) {
        this.cheapAcceptedCount += 1;
        const decision = {
          taskId,
          selectedLevel: FidelityLevel.INTERMEDIATE,
          escalated: true,
          estimatedUncertainty: intUnc,
          uncertaintyTolerance: tol,
          executionTimeMs: tInt,
          value: intVal,
          computeSavedRatio: 0.8,
          rationale: `Escalated to intermediate level. Uncertainty (${intUnc}) accepted`
        };
        this.history.push(decision);
        return decision;
      }
    }

    this.escalationsCount += 1;
    const tExp0 = Date.now();
    const expVal = expensiveSolver(inputs);
    const tTotal = (Date.now() - tExp0) + tCheap;

    const decision = {
      taskId,
      selectedLevel: FidelityLevel.HIGH,
      escalated: true,
      estimatedUncertainty: 0.0,
      uncertaintyTolerance: tol,
      executionTimeMs: tTotal,
      value: expVal,
      computeSavedRatio: 0.0,
      rationale: `Escalated to high fidelity. Cheap model uncertainty (${cheapUnc}) > tolerance (${tol})`
    };
    this.history.push(decision);
    return decision;
  }
}
