/**
 * sfsa.aie — Assumption Integrity Engine (AIE)
 * ============================================
 * Audits model assumptions and flags regime breakdowns during simulation.
 *
 * Part of SFSA (Standard Framework for Scientific Advancement)
 * Author & Protocol Creator: Alejo Malia
 * License: CC BY 4.0
 */

export class AssumptionIntegrityEngine {
  constructor() {
    this.assumptions = new Map();
    this.violationHistory = [];
  }

  registerAssumption(assumptionId, name, conditionFn, criticality = "WARNING", description = "") {
    this.assumptions.set(assumptionId, { assumptionId, name, conditionFn, criticality, description });
  }

  auditState(currentState) {
    const violations = [];
    for (const [id, asm] of this.assumptions.entries()) {
      let valid, reason;
      try {
        [valid, reason] = asm.conditionFn(currentState);
      } catch (err) {
        valid = false;
        reason = `assumption could not be evaluated (${err && err.name}: ${err && err.message})`;
      }
      if (!valid) {
        const v = {
          assumptionId: id,
          name: asm.name,
          criticality: asm.criticality,
          diagnosticMessage: reason,
          violatingState: { ...currentState }
        };
        violations.push(v);
        this.violationHistory.push(v);
      }
    }
    return violations;
  }
}
