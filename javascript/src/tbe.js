/**
 * sfsa.tbe — Temporal Budget Engine (TBE)
 * ======================================
 * Manages compute time dynamically across sessions.
 *
 * Part of SFSA (Standard Framework for Scientific Advancement)
 * Author & Protocol Creator: Alejo Malia
 * License: CC BY 4.0
 */

export class TemporalBudgetEngine {
  constructor(totalBudgetSeconds = 60.0) {
    this.totalBudget = totalBudgetSeconds;
    this.spentSeconds = 0.0;
    this.startTimestamp = Date.now();
  }

  getRemainingSeconds() {
    const elapsed = (Date.now() - this.startTimestamp) / 1000.0;
    return Math.max(0.0, this.totalBudget - Math.max(elapsed, this.spentSeconds));
  }

  requestAllocation(taskId, expectedCostSeconds, priority = 1.0) {
    if (!(expectedCostSeconds >= 0) || !(priority > 0)) {
      throw new Error("expectedCostSeconds must be >= 0 and priority must be > 0");
    }
    const rem = this.getRemainingSeconds();
    if (rem <= 0.0) {
      return {
        taskId,
        allocatedSeconds: 0.0,
        remainingTotalSeconds: 0.0,
        canProceed: false,
        rationale: "Budget exhausted"
      };
    }

    const quota = Math.min(rem * 0.4 * priority, expectedCostSeconds * 1.2);
    return {
      taskId,
      allocatedSeconds: quota,
      remainingTotalSeconds: rem,
      canProceed: quota >= expectedCostSeconds * 0.5,
      rationale: `Allocated ${quota.toFixed(2)}s (reserve=${rem.toFixed(2)}s)`
    };
  }

  recordUsage(taskId, secondsUsed) {
    this.spentSeconds += secondsUsed;
  }
}
