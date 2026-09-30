/**
 * sfsa.voi — Value-of-Information Decision Engine (VOI)
 * ====================================================
 * Transforms SFSA from an execution optimizer into a scientific progress optimizer.
 * Evaluates expected epistemic gain before spending computation: asks "Will this additional
 * calculation alter the scientific conclusion, decision threshold, or Pareto ranking?"
 * Cuts calculations whose marginal information gain is lower than computational cost.
 *
 * Part of SFSA (Standard Framework for Scientific Advancement)
 * Author & Protocol Creator: Alejo Malia
 * License: CC BY 4.0
 */

function erfc(x) {
  if (x < 0) return 2 - erfc(-x);
  const p = 0.3275911;
  const a1 = 0.254829592;
  const a2 = -0.284496736;
  const a3 = 1.421413741;
  const a4 = -1.453152027;
  const a5 = 1.061405429;

  const t = 1.0 / (1.0 + p * x);
  const poly = ((((a5 * t + a4) * t + a3) * t + a2) * t + a1) * t;
  return poly * Math.exp(-x * x);
}

export class VOIAssessment {
  constructor({
    candidateId,
    expectedValueOfInformation,
    estimatedCost,
    voiCostRatio,
    recommendation,
    rationale
  }) {
    this.candidateId = candidateId;
    this.expectedValueOfInformation = expectedValueOfInformation;
    this.estimatedCost = estimatedCost;
    this.voiCostRatio = voiCostRatio;
    this.recommendation = recommendation;
    this.rationale = rationale;
  }
}

export class ValueInformationEngine {
  constructor({ costWeight = 0.5, minEvoiThreshold = 0.15 } = {}) {
    this.costWeight = costWeight;
    this.minEvoiThreshold = minEvoiThreshold;
    this.history = [];
  }

  evaluateCandidate(candidateId, predictedValue, epistemicUncertainty, decisionThreshold, estimatedCost = 1.0) {
    const distanceToBoundary = Math.abs(predictedValue - decisionThreshold);
    const denom = Math.max(epistemicUncertainty, 1e-6);

    // Probability of state crossing boundary under Gaussian assumption
    const z = distanceToBoundary / denom;
    const probFlip = 0.5 * erfc(z / Math.SQRT2);

    // Expected value of information scales with probability of changing decision
    const evoi = Math.min(1.0, 2.0 * probFlip * (1.0 + epistemicUncertainty));
    const normCost = Math.max(estimatedCost, 0.01);
    const ratio = evoi / normCost;

    let rec = 'COMPUTE';
    let rationale = `High information value (${evoi.toFixed(3)}) near decision boundary`;

    if (evoi < this.minEvoiThreshold) {
      rec = 'SKIP_LOW_VALUE';
      rationale = `Marginal information gain (${evoi.toFixed(3)}) below threshold (${this.minEvoiThreshold})`;
    } else if (ratio < 0.2) {
      rec = 'USE_CHEAP_SURROGATE';
      rationale = `Cost (${estimatedCost.toFixed(1)}) exceeds epistemic payoff (${evoi.toFixed(3)})`;
    }

    const assessment = new VOIAssessment({
      candidateId,
      expectedValueOfInformation: evoi,
      estimatedCost,
      voiCostRatio: ratio,
      recommendation: rec,
      rationale
    });

    this.history.push(assessment);
    return assessment;
  }

  filterCandidates(candidates, predictFn, decisionThreshold, costFn = null) {
    const approved = [];
    for (let idx = 0; idx < candidates.length; idx++) {
      const cand = candidates[idx];
      const cid = cand.id || `cand_${idx}`;
      const [val, unc] = predictFn(cand);
      const cost = costFn ? costFn(cand) : 1.0;
      const assessment = this.evaluateCandidate(cid, val, unc, decisionThreshold, cost);
      if (assessment.recommendation === 'COMPUTE') {
        approved.push(cand);
      }
    }
    return approved;
  }
}
