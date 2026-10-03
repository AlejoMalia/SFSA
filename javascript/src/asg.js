/**
 * sfsa.asg — Adaptive Sampling & Experimentation Engine (ASG)
 * ==========================================================
 * Prioritizes unexplored parameter subspaces characterized by high gradient or uncertainty.
 *
 * Part of SFSA (Standard Framework for Scientific Advancement)
 * Author & Protocol Creator: Alejo Malia
 * License: CC BY 4.0
 */

export class AdaptiveSamplingEngine {
  constructor(minEuclideanDistance = 0.05, uncertaintyWeight = 0.6, { uncertaintyEstimator = null, gradientEstimator = null } = {}) {
    this.minEuclideanDistance = minEuclideanDistance;
    this.uncertaintyWeight = uncertaintyWeight;
    // Default estimators used by evaluateCandidate / filterGrid when none is passed per call.
    this.uncertaintyEstimator = uncertaintyEstimator;
    this.gradientEstimator = gradientEstimator;
    this.evaluatedPoints = [];
    // NaN marks a point that was selected but whose response has not been recorded yet.
    this.pointValues = [];
  }

  recordEvaluation(point, value) {
    this.evaluatedPoints.push({ ...point });
    this.pointValues.push(value);
  }

  _normalizeDist(p1, p2) {
    const keys1 = Object.keys(p1);
    const shared = keys1.filter(k => k in p2);
    if (shared.length === 0) return 1.0;
    const sqSum = shared.reduce((acc, k) => acc + (p1[k] - p2[k]) ** 2, 0);
    return Math.sqrt(sqSum) / Math.sqrt(shared.length);
  }

  evaluateCandidate(candidatePoint, uncertaintyEstimator = null, gradientEstimator = null) {
    uncertaintyEstimator = uncertaintyEstimator || this.uncertaintyEstimator;
    gradientEstimator = gradientEstimator || this.gradientEstimator;
    if (this.evaluatedPoints.length === 0) {
      return {
        point: candidatePoint,
        informationGain: 1.0,
        distanceToNearest: 1.0,
        estimatedUncertainty: 1.0,
        skipRecommended: false,
        rationale: "Initial baseline sample in unexplored space"
      };
    }

    const minDistance = Math.min(...this.evaluatedPoints.map(p => this._normalizeDist(candidatePoint, p)));
    const unc = uncertaintyEstimator ? uncertaintyEstimator(candidatePoint) : Math.min(1.0, minDistance * 2.0);
    const grad = gradientEstimator ? gradientEstimator(candidatePoint) : 0.5;

    const utility = (1.0 - this.uncertaintyWeight) * (minDistance * grad) + this.uncertaintyWeight * unc;
    const skip = minDistance < this.minEuclideanDistance && unc < 0.1;

    return {
      point: candidatePoint,
      informationGain: utility,
      distanceToNearest: minDistance,
      estimatedUncertainty: unc,
      skipRecommended: skip,
      rationale: skip
        ? `Skip: point is within ${minDistance.toFixed(4)} of evaluated point`
        : `Sample: information gain ${utility.toFixed(4)}`
    };
  }

  /**
   * Filters a dense candidate grid down to the most informative points. The uncertainty/gradient estimators
   * (per call, or those given at construction) drive both the skip decision and, under a budget, the ranking:
   * without a budget the grid is scanned in order and every non-redundant point is kept; with maxBudget the points
   * are chosen greedily by acquisition utility, re-evaluated after every pick. Budget 0 selects nothing; a
   * negative budget throws. Selected points are registered with a NaN response until the real value is recorded.
   */
  filterGrid(candidateGrid, maxBudget = null, uncertaintyEstimator = null, gradientEstimator = null) {
    if (maxBudget !== null && maxBudget < 0) throw new Error('maxBudget must be >= 0');
    const selected = [];
    if (maxBudget === 0) return selected;
    if (maxBudget === null) {
      for (const cand of candidateGrid) {
        const a = this.evaluateCandidate(cand, uncertaintyEstimator, gradientEstimator);
        if (!a.skipRecommended) {
          selected.push(cand);
          this.recordEvaluation(cand, NaN);
        }
      }
      return selected;
    }
    const remaining = [...candidateGrid];
    while (remaining.length && selected.length < maxBudget) {
      let best = null;
      let bestIdx = -1;
      remaining.forEach((c, i) => {
        const a = this.evaluateCandidate(c, uncertaintyEstimator, gradientEstimator);
        if (!a.skipRecommended && (best === null || a.informationGain > best.informationGain)) { best = a; bestIdx = i; }
      });
      if (best === null) break;
      selected.push(remaining.splice(bestIdx, 1)[0]);
      this.recordEvaluation(best.point, NaN);
    }
    return selected;
  }
}
