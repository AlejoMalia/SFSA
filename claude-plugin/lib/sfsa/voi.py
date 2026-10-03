"""
sfsa.voi — Value-of-Information Decision Engine (VOI)
====================================================
Transforms SFSA from an execution optimizer into a scientific progress optimizer.
Evaluates expected epistemic gain before spending computation: asks "Will this additional
calculation alter the scientific conclusion, decision threshold, or Pareto ranking?"
Cuts calculations whose marginal information gain is lower than computational cost.

Part of SFSA (Standard Framework for Scientific Advancement)
Author & Protocol Creator: Alejo Malia
License: CC BY 4.0
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, Tuple
import math


@dataclass
class VOIAssessment:
    """Quantitative value-of-information assessment for an evaluation candidate."""
    candidate_id: str
    expected_value_of_information: float  # EVOI [0.0 to 1.0]
    estimated_cost: float
    voi_cost_ratio: float
    recommendation: str                   # 'COMPUTE', 'SKIP_LOW_VALUE', 'USE_CHEAP_SURROGATE'
    rationale: str


class ValueInformationEngine:
    """
    VOI quantifies the marginal utility of performing additional computations or experiments.
    """

    def __init__(self, cost_weight: float = 0.5, min_evoi_threshold: float = 0.15) -> None:
        self.cost_weight = cost_weight
        self.min_evoi_threshold = min_evoi_threshold
        self.history: List[VOIAssessment] = []

    def evaluate_candidate(
        self,
        candidate_id: str,
        predicted_value: float,
        epistemic_uncertainty: float,
        decision_threshold: float,
        estimated_cost: float = 1.0,
    ) -> VOIAssessment:
        """
        Calculates Expected Value of Information (EVOI) around a scientific decision boundary.
        High uncertainty close to the decision boundary yields maximal VOI;
        far from boundary or low uncertainty yields near-zero VOI.
        """
        distance_to_boundary = abs(predicted_value - decision_threshold)
        denom = max(epistemic_uncertainty, 1e-6)

        # Probability of state crossing boundary under Gaussian assumption
        z = distance_to_boundary / denom
        prob_flip = 0.5 * math.erfc(z / math.sqrt(2.0))

        # Expected value of information scales with probability of changing decision
        evoi = min(1.0, 2.0 * prob_flip * (1.0 + epistemic_uncertainty))
        norm_cost = max(estimated_cost, 0.01)
        ratio = evoi / norm_cost

        if evoi < self.min_evoi_threshold:
            rec = "SKIP_LOW_VALUE"
            rationale = f"Marginal information gain ({evoi:.3f}) below threshold ({self.min_evoi_threshold})"
        elif ratio < 0.2:
            rec = "USE_CHEAP_SURROGATE"
            rationale = f"Cost ({estimated_cost:.1f}) exceeds epistemic payoff ({evoi:.3f})"
        else:
            rec = "COMPUTE"
            rationale = f"High information value ({evoi:.3f}) near decision boundary"

        assessment = VOIAssessment(
            candidate_id=candidate_id,
            expected_value_of_information=evoi,
            estimated_cost=estimated_cost,
            voi_cost_ratio=ratio,
            recommendation=rec,
            rationale=rationale,
        )
        self.history.append(assessment)
        return assessment

    def filter_candidates(
        self,
        candidates: List[Dict[str, Any]],
        predict_fn: Callable[[Dict[str, Any]], Tuple[float, float]], # returns (pred_val, uncertainty)
        decision_threshold: float,
        cost_fn: Optional[Callable[[Dict[str, Any]], float]] = None,
    ) -> List[Dict[str, Any]]:
        """
        Filters out candidate evaluations with low epistemic return.
        """
        approved: List[Dict[str, Any]] = []
        for idx, cand in enumerate(candidates):
            cid = cand.get("id", f"cand_{idx}")
            val, unc = predict_fn(cand)
            cost = cost_fn(cand) if cost_fn else 1.0
            assessment = self.evaluate_candidate(cid, val, unc, decision_threshold, cost)
            if assessment.recommendation == "COMPUTE":
                approved.append(cand)
        return approved
