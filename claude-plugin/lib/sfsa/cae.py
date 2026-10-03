"""
sfsa.cae — Constraint Awareness Engine (CAE)
============================================
Propagates explicit and inferred constraints throughout framework layers before the solver runs.
Detects implicit infeasibility patterns across historical runs, generates tighter domain cuts,
and prunes parameter subspaces that are provably unviable, shrinking the search space.

Part of SFSA (Standard Framework for Scientific Advancement)
Author & Protocol Creator: Alejo Malia
License: CC BY 4.0
"""

from __future__ import annotations

from dataclasses import dataclass, field
import math
from typing import Any, Callable, Dict, List, Optional, Tuple


@dataclass
class InferredConstraint:
    """An implicit constraint synthesized from observed computational failures or boundaries."""
    constraint_id: str
    parameter_name: str
    condition_op: str                 # blocked region: '>=' (value >= t) or '<=' (value <= t)
    threshold_value: Any
    confidence: float
    support_count: int                # Number of historical observations supporting this cut
    rationale: str


@dataclass
class FeasibleDomainCut:
    """A bounded cut applied to shrink the initial search volume."""
    parameter: str
    original_bounds: Tuple[float, float]
    tightened_bounds: Tuple[float, float]
    volume_reduction_ratio: float


class ConstraintAwarenessEngine:
    """
    CAE synthesizes proactive mathematical cuts before solver dispatch.
    """

    def __init__(self, min_support_for_inference: int = 5) -> None:
        self.min_support = min_support_for_inference
        self.explicit_constraints: List[Callable[[Dict[str, Any]], Tuple[bool, str]]] = []
        self.inferred_constraints: List[InferredConstraint] = []
        self.infeasible_history: List[Dict[str, Any]] = []
        self.feasible_history: List[Dict[str, Any]] = []
        self.max_feasible_history = 5000

    def add_explicit_constraint(self, rule: Callable[[Dict[str, Any]], Tuple[bool, str]]) -> None:
        """Registers a user-declared hard scientific invariant rule."""
        self.explicit_constraints.append(rule)

    def record_infeasibility(self, parameters: Dict[str, Any], reason: str = "") -> None:
        """Records an infeasible evaluation and re-derives the implicit cuts."""
        self.infeasible_history.append(dict(parameters))
        self._infer_implicit_bounds()

    def record_feasibility(self, parameters: Dict[str, Any]) -> None:
        """
        Records a point where the computation succeeded. A feasible point inside a previously inferred
        cut revokes that cut: a cutting plane is only sound while no known-good point lies in the blocked region.
        """
        self.feasible_history.append(dict(parameters))
        if len(self.feasible_history) > self.max_feasible_history:
            del self.feasible_history[: len(self.feasible_history) - self.max_feasible_history]
        if self.inferred_constraints:
            self._infer_implicit_bounds()

    @staticmethod
    def _numeric(entries: List[Dict[str, Any]], param: str) -> List[float]:
        return [
            float(e[param]) for e in entries
            if isinstance(e.get(param), (int, float)) and not isinstance(e.get(param), bool) and math.isfinite(e[param])
        ]

    def _infer_implicit_bounds(self) -> None:
        """
        Rebuilds one-sided cutting planes from the failure history. For each numeric parameter with enough
        failures, a cut is emitted only if every known feasible value lies strictly on the safe side:
          - upper cut  (block value >= t) with t = min(failures), when all feasible values are < t
          - lower cut  (block value <= t) with t = max(failures), when all feasible values are > t
        """
        params = {k for e in self.infeasible_history for k in e}
        rebuilt: List[InferredConstraint] = []
        for param in sorted(params):
            fails = self._numeric(self.infeasible_history, param)
            if len(fails) < self.min_support:
                continue
            good = self._numeric(self.feasible_history, param)
            lo_fail, hi_fail = min(fails), max(fails)
            if all(g < lo_fail for g in good):
                op, thr = ">=", lo_fail
            elif all(g > hi_fail for g in good):
                op, thr = "<=", hi_fail
            else:
                continue  # failures are interleaved with successes: no sound one-sided cut exists
            rebuilt.append(
                InferredConstraint(
                    constraint_id=f"cut_{param}",
                    parameter_name=param,
                    condition_op=op,
                    threshold_value=thr,
                    confidence=min(1.0, len(fails) / max(self.min_support * 2, 1)),
                    support_count=len(fails),
                    rationale=f"{len(fails)} failures with {param} {op} {thr:.4g} and "
                              f"{len(good)} feasible points all on the safe side",
                )
            )
        self.inferred_constraints = rebuilt

    def validate_inputs(self, inputs: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
        """
        Fast-evaluates explicit and inferred cuts before launching computation.
        """
        # 1. Explicit constraints
        for rule in self.explicit_constraints:
            try:
                valid, reason = rule(inputs)
            except Exception as exc:  # fail closed: an unevaluable hard constraint blocks the solve
                valid, reason = False, f"rule raised {type(exc).__name__}: {exc}"
            if not valid:
                return False, f"Explicit constraint violated: {reason}"

        # 2. Inferred cuts
        for cut in self.inferred_constraints:
            if cut.parameter_name in inputs:
                val = inputs[cut.parameter_name]
                if isinstance(val, (int, float)) and not isinstance(val, bool) and cut.support_count >= self.min_support:
                    if cut.condition_op == ">=" and val >= cut.threshold_value:
                        return False, f"Inferred cut boundary violated: {cut.rationale}"
                    if cut.condition_op == "<=" and val <= cut.threshold_value:
                        return False, f"Inferred cut boundary violated: {cut.rationale}"

        return True, None
