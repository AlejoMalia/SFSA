/**
 * sfsa.cae — Constraint Awareness Engine (CAE)
 * ============================================
 * Propagates explicit constraints and infers implicit bounds cuts from history.
 *
 * Part of SFSA (Standard Framework for Scientific Advancement)
 * Author & Protocol Creator: Alejo Malia
 * License: CC BY 4.0
 */

export class ConstraintAwarenessEngine {
  constructor(minSupportForInference = 5) {
    this.minSupport = minSupportForInference;
    this.explicitConstraints = [];
    this.inferredConstraints = [];
    this.infeasibleHistory = [];
    this.feasibleHistory = [];
    this.maxFeasibleHistory = 5000;
  }

  addExplicitConstraint(rule) {
    this.explicitConstraints.push(rule);
  }

  recordInfeasibility(parameters) {
    this.infeasibleHistory.push({ ...parameters });
    this._inferImplicitBounds();
  }

  // A feasible point inside a previously inferred cut revokes it: a cutting plane is only sound
  // while no known-good point lies in the blocked region.
  recordFeasibility(parameters) {
    this.feasibleHistory.push({ ...parameters });
    if (this.feasibleHistory.length > this.maxFeasibleHistory) {
      this.feasibleHistory.splice(0, this.feasibleHistory.length - this.maxFeasibleHistory);
    }
    if (this.inferredConstraints.length > 0) this._inferImplicitBounds();
  }

  static _numeric(entries, param) {
    return entries.map(e => e[param]).filter(v => typeof v === 'number' && Number.isFinite(v));
  }

  // Rebuilds one-sided cuts: upper (block value >= t, t = min failure) when all feasible values are < t;
  // lower (block value <= t, t = max failure) when all feasible values are > t.
  _inferImplicitBounds() {
    const params = new Set(this.infeasibleHistory.flatMap(e => Object.keys(e)));
    const rebuilt = [];
    for (const param of [...params].sort()) {
      const fails = ConstraintAwarenessEngine._numeric(this.infeasibleHistory, param);
      if (fails.length < this.minSupport) continue;
      const good = ConstraintAwarenessEngine._numeric(this.feasibleHistory, param);
      const loFail = Math.min(...fails), hiFail = Math.max(...fails);
      let op, thr;
      if (good.every(g => g < loFail)) { op = '>='; thr = loFail; }
      else if (good.every(g => g > hiFail)) { op = '<='; thr = hiFail; }
      else continue;
      rebuilt.push({
        constraintId: `cut_${param}`,
        parameterName: param,
        conditionOp: op,
        thresholdValue: thr,
        confidence: Math.min(1.0, fails.length / Math.max(this.minSupport * 2, 1)),
        supportCount: fails.length,
        rationale: `${fails.length} failures with ${param} ${op} ${Number(thr.toPrecision(4))} and ${good.length} feasible points all on the safe side`
      });
    }
    this.inferredConstraints = rebuilt;
  }

  validateInputs(inputs) {
    for (const rule of this.explicitConstraints) {
      let valid, reason;
      try {
        [valid, reason] = rule(inputs);
      } catch (err) {
        valid = false;
        reason = `rule raised ${err && err.name}: ${err && err.message}`;
      }
      if (!valid) return [false, `Explicit constraint violated: ${reason}`];
    }

    for (const cut of this.inferredConstraints) {
      if (cut.parameterName in inputs) {
        const val = inputs[cut.parameterName];
        if (typeof val === 'number' && cut.supportCount >= this.minSupport &&
            ((cut.conditionOp === '>=' && val >= cut.thresholdValue) || (cut.conditionOp === '<=' && val <= cut.thresholdValue))) {
          return [false, `Inferred cut boundary violated: ${cut.rationale}`];
        }
      }
    }

    return [true, null];
  }
}
