/**
 * sfsa.icr — In-Frame Computer Reduction (ICR) Engine
 * ===================================================
 * Computational optimizer for JavaScript scientific frameworks.
 * Inspects calculation calls, performs dead-branch elimination,
 * folds zero/trivial inputs, and substitutes expensive iterative solvers with closed forms.
 *
 * Part of SFSA (Standard Framework for Scientific Advancement)
 * Author & Protocol Creator: Alejo Malia
 * License: CC BY 4.0
 */

export const OptimizationLevel = Object.freeze({
  O0_NONE: "O0_NONE",
  O1_BASIC: "O1_BASIC",
  O2_ANALYTICAL: "O2_ANALYTICAL",
  O3_AGGRESSIVE: "O3_AGGRESSIVE",
});

export class ReductionProfile {
  constructor({
    initialOperationsEstimated,
    executedOperations,
    operationsEliminated,
    reductionPercentage,
    timeSavedEstimatedMs,
    optimizationsApplied = [],
  }) {
    this.initialOperationsEstimated = initialOperationsEstimated;
    this.executedOperations = executedOperations;
    this.operationsEliminated = operationsEliminated;
    this.reductionPercentage = reductionPercentage;
    this.timeSavedEstimatedMs = timeSavedEstimatedMs;
    this.optimizationsApplied = optimizationsApplied;
  }
}

export class ICREngine {
  constructor({ level = OptimizationLevel.O2_ANALYTICAL } = {}) {
    this.level = level;
    this._totalOperationsAvoided = 0;
    this._history = [];
  }

  optimizeAndExecute({
    taskId,
    inputParams,
    exactSolver,
    analyticalShortcut = null,
    shortcutValidityCondition = null,
    estimatedDenseOps = 1000,
  }) {
    const applied = [];
    const t0 = performance.now();

    // PASS 1: Trivial / Near-Zero Pruning
    const values = Object.values(inputParams);
    const allNearZero = values.length > 0 && values.every((v) => typeof v === 'number' && Math.abs(v) < 1e-15);
    if (allNearZero) {
      applied.push("TrivialZeroPruning: All parameters near zero");
      const profile = new ReductionProfile({
        initialOperationsEstimated: estimatedDenseOps,
        executedOperations: 1,
        operationsEliminated: estimatedDenseOps - 1,
        reductionPercentage: ((estimatedDenseOps - 1) / estimatedDenseOps) * 100.0,
        timeSavedEstimatedMs: performance.now() - t0,
        optimizationsApplied: applied,
      });
      this._totalOperationsAvoided += profile.operationsEliminated;
      this._history.push(profile);
      return { result: 0.0, profile };
    }

    // PASS 2: Analytical Closed-Form Substitution
    if (this.level === OptimizationLevel.O2_ANALYTICAL || this.level === OptimizationLevel.O3_AGGRESSIVE) {
      if (typeof analyticalShortcut === 'function') {
        const canUse = typeof shortcutValidityCondition === 'function'
          ? shortcutValidityCondition(inputParams)
          : true;

        if (canUse) {
          applied.push("ClosedFormSubstitution: Executed O(1) analytical shortcut");
          const result = analyticalShortcut(inputParams);
          const executedOps = 5;
          const profile = new ReductionProfile({
            initialOperationsEstimated: estimatedDenseOps,
            executedOperations: executedOps,
            operationsEliminated: Math.max(0, estimatedDenseOps - executedOps),
            reductionPercentage: ((estimatedDenseOps - executedOps) / estimatedDenseOps) * 100.0,
            timeSavedEstimatedMs: performance.now() - t0,
            optimizationsApplied: applied,
          });
          this._totalOperationsAvoided += profile.operationsEliminated;
          this._history.push(profile);
          return { result, profile };
        }
      }
    }

    // PASS 3: Fallback Exact Execution
    applied.push("DenseFallback: Executed exact solver");
    const result = exactSolver(inputParams);
    const profile = new ReductionProfile({
      initialOperationsEstimated: estimatedDenseOps,
      executedOperations: estimatedDenseOps,
      operationsEliminated: 0,
      reductionPercentage: 0.0,
      timeSavedEstimatedMs: 0.0,
      optimizationsApplied: applied,
    });
    this._history.push(profile);
    return { result, profile };
  }

  get totalOperationsAvoided() {
    return this._totalOperationsAvoided;
  }

  get reductionHistory() {
    return [...this._history];
  }
}
