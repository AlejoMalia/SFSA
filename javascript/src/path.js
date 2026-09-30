/**
 * sfsa.path — ParetoPathEngine (Multi-Objective Transition & Pathway Optimizer)
 * =============================================================================
 * JavaScript implementation of the Pareto Pathway Optimizer.
 * Explores multi-stage transition actions connecting an Initial State (A) to
 * a Target State (B), filtering out suboptimal paths via strict Pareto dominance.
 *
 * Part of SFSA (Standard Framework for Scientific Advancement)
 * Author & Protocol Creator: Alejo Malia
 * License: CC BY 4.0
 */

export class TransitionStep {
  constructor({
    stepId,
    name,
    cost,
    duration,
    feasibility = 1.0,
    deltaState = {},
    metadata = {},
  }) {
    this.stepId = stepId;
    this.name = name;
    this.cost = cost;
    this.duration = duration;
    this.feasibility = feasibility;
    this.deltaState = deltaState;
    this.metadata = metadata;
  }
}

export class Pathway {
  constructor({
    pathId,
    steps = [],
    accumulatedCost = 0.0,
    accumulatedDuration = 0.0,
    jointFeasibility = 1.0,
    finalState = {},
    isParetoOptimal = true,
  }) {
    this.pathId = pathId;
    this.steps = steps;
    this.accumulatedCost = accumulatedCost;
    this.accumulatedDuration = accumulatedDuration;
    this.jointFeasibility = jointFeasibility;
    this.finalState = finalState;
    this.isParetoOptimal = isParetoOptimal;
  }

  dominates(other) {
    const weaklyBetter =
      this.accumulatedCost <= other.accumulatedCost &&
      this.accumulatedDuration <= other.accumulatedDuration &&
      this.jointFeasibility >= other.jointFeasibility;

    const strictlyBetter =
      this.accumulatedCost < other.accumulatedCost ||
      this.accumulatedDuration < other.accumulatedDuration ||
      this.jointFeasibility > other.jointFeasibility;

    return weaklyBetter && strictlyBetter;
  }
}

export class ParetoPathEngine {
  constructor() {
    this._actions = new Map();
    this.maxExpansions = 200000;
  }

  registerStep(step) {
    this._actions.set(step.stepId, step);
  }

  extractParetoFrontier(pathways) {
    const frontier = [];
    for (const cand of pathways) {
      let dominated = false;
      for (const other of pathways) {
        if (other !== cand && other.dominates(cand)) {
          dominated = true;
          cand.isParetoOptimal = false;
          break;
        }
      }
      if (!dominated) {
        cand.isParetoOptimal = true;
        frontier.push(cand);
      }
    }
    return frontier;
  }

  findPathways({
    initialState,
    targetState,
    maxSteps = 4,
    tolerance = 0.05,
  }) {
    const completedPathways = [];

    const isGoalSatisfied = (state) => {
      for (const [k, targetVal] of Object.entries(targetState)) {
        const curr = state[k] || 0.0;
        if (Math.abs(curr - targetVal) > Math.abs(targetVal * tolerance) + 1e-9) {
          return false;
        }
      }
      return true;
    };

    // Steps may repeat (heat, heat, heat); bounded by dominance pruning per state and a cap on expansions.
    const queue = [[{ ...initialState }, []]];
    const bestSeen = new Map();
    let expansions = 0;
    let head = 0;

    while (head < queue.length) {
      const [currState, path] = queue[head++];

      const obj = [
        path.reduce((a, s) => a + s.cost, 0),
        path.reduce((a, s) => a + s.duration, 0),
        path.reduce((a, s) => a * s.feasibility, 1.0),
      ];
      const stateKey = JSON.stringify(Object.keys(currState).sort().map((k) => [k, Math.round(currState[k] * 1e9) / 1e9]));
      if (!bestSeen.has(stateKey)) bestSeen.set(stateKey, []);
      const seen = bestSeen.get(stateKey);
      if (seen.some(([c, d, f]) => c <= obj[0] && d <= obj[1] && f >= obj[2])) continue;
      seen.push(obj);

      if (isGoalSatisfied(currState)) {
        const totalCost = path.reduce((acc, s) => acc + s.cost, 0);
        const totalDur = path.reduce((acc, s) => acc + s.duration, 0);
        const jointFeas = path.reduce((acc, s) => acc * s.feasibility, 1.0);

        completedPathways.push(
          new Pathway({
            pathId: `path_${completedPathways.length + 1}`,
            steps: [...path],
            accumulatedCost: totalCost,
            accumulatedDuration: totalDur,
            jointFeasibility: jointFeas,
            finalState: { ...currState },
          })
        );
        continue;
      }

      if (path.length >= maxSteps) {
        continue;
      }

      for (const act of this._actions.values()) {
        expansions += 1;
        if (expansions > this.maxExpansions) {
          return this.extractParetoFrontier(completedPathways);
        }

        const newState = { ...currState };
        for (const [k, dv] of Object.entries(act.deltaState)) {
          newState[k] = (newState[k] || 0.0) + dv;
        }

        queue.push([newState, [...path, act]]);
      }
    }

    return this.extractParetoFrontier(completedPathways);
  }
}
