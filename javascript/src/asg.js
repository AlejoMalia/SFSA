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
  constructor(minEuclideanDistance = 0.05, uncertaintyWeight = 0.6) {
    this.minEuclideanDistance = minEuclideanDistance;
    this.uncertaintyWeight = uncertaintyWeight;
    this.evaluatedPoints = [];
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

  filterGrid(candidateGrid, maxBudget = null) {
    const selected = [];
    for (const cand of candidateGrid) {
      const a = this.evaluateCandidate(cand);
      if (!a.skipRecommended) {
        selected.push(cand);
        this.recordEvaluation(cand, 0.0); // mark as sampled in draft
      }
      if (maxBudget && selected.length >= maxBudget) break;
    }
    return selected;
  }
}
