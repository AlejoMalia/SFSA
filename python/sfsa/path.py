"""
sfsa.path — ParetoPathEngine (Multi-Objective Transition & Pathway Optimizer)
=============================================================================
Computes optimal multi-stage transition pathways from an Initial State (A) to
a Desired Target State (B). Connects intermediate state transitions, generates
candidate graphs, and filters suboptimal pathways using Pareto dominance
(minimizing Cost and Time while maximizing Feasibility).

Part of SFSA (Standard Framework for Scientific Advancement)
Author & Protocol Creator: Alejo Malia
License: CC BY 4.0
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, Set, Tuple
import math


@dataclass
class TransitionStep:
    """An individual transition action connecting two intermediate states."""
    step_id: str
    name: str
    cost: float                     # e.g., energy, monetary cost, mass expended
    duration: float                 # e.g., elapsed time, cycle count
    feasibility: float              # 0.0 to 1.0 (probability of success / physical viability)
    delta_state: Dict[str, float]   # State modifications produced by this step
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Pathway:
    """An ordered sequence of transition steps leading toward the target state."""
    path_id: str
    steps: List[TransitionStep]
    accumulated_cost: float
    accumulated_duration: float
    joint_feasibility: float
    final_state: Dict[str, float]
    is_pareto_optimal: bool = True

    def dominates(self, other: Pathway) -> bool:
        """
        Returns True if self Pareto-dominates other:
        - Weakly better in all objectives: cost <= other.cost, duration <= other.duration, feasibility >= other.feasibility
        - Strictly better in at least one objective.
        """
        weakly_better = (
            self.accumulated_cost <= other.accumulated_cost and
            self.accumulated_duration <= other.accumulated_duration and
            self.joint_feasibility >= other.joint_feasibility
        )
        strictly_better = (
            self.accumulated_cost < other.accumulated_cost or
            self.accumulated_duration < other.accumulated_duration or
            self.joint_feasibility > other.joint_feasibility
        )
        return weakly_better and strictly_better


class ParetoPathEngine:
    """
    Multi-objective pathway optimizer for scientific state transitions.
    Explores candidate action cascades and extracts the Pareto-optimal frontier.
    """

    def __init__(self) -> None:
        self._actions: Dict[str, TransitionStep] = {}

    def register_step(self, step: TransitionStep) -> None:
        """Registers an available transformation step."""
        self._actions[step.step_id] = step

    def extract_pareto_frontier(self, pathways: List[Pathway]) -> List[Pathway]:
        """Filters a list of pathways down to only the non-dominated Pareto front."""
        frontier: List[Pathway] = []
        for cand in pathways:
            dominated = False
            for other in pathways:
                if other is not cand and other.dominates(cand):
                    dominated = True
                    cand.is_pareto_optimal = False
                    break
            if not dominated:
                cand.is_pareto_optimal = True
                frontier.append(cand)
        return frontier

    def find_pathways(
        self,
        initial_state: Dict[str, float],
        target_state: Dict[str, float],
        max_steps: int = 4,
        tolerance: float = 0.05,
    ) -> List[Pathway]:
        """
        Discovers transition pathways from initial_state to target_state using
        branch-and-bound exploration, returning the Pareto-optimal frontier.
        """
        completed_pathways: List[Pathway] = []

        def is_goal_satisfied(state: Dict[str, float]) -> bool:
            for k, target_val in target_state.items():
                curr = state.get(k, 0.0)
                if abs(curr - target_val) > abs(target_val * tolerance) + 1e-9:
                    return False
            return True

        # Breadth-first / branch-and-bound search
        queue: List[Tuple[Dict[str, float], List[TransitionStep]]] = [(dict(initial_state), [])]

        while queue:
            curr_state, path = queue.pop(0)

            if is_goal_satisfied(curr_state):
                total_cost = sum(s.cost for s in path)
                total_dur = sum(s.duration for s in path)
                # Joint feasibility: product of step feasibilities
                joint_feas = math.prod([s.feasibility for s in path]) if path else 1.0

                completed_pathways.append(
                    Pathway(
                        path_id=f"path_{len(completed_pathways) + 1}",
                        steps=list(path),
                        accumulated_cost=total_cost,
                        accumulated_duration=total_dur,
                        joint_feasibility=joint_feas,
                        final_state=dict(curr_state),
                    )
                )
                continue

            if len(path) >= max_steps:
                continue

            for act in self._actions.values():
                # Avoid trivial repeating identical action consecutively
                if path and path[-1].step_id == act.step_id:
                    continue

                new_state = dict(curr_state)
                for k, dv in act.delta_state.items():
                    new_state[k] = new_state.get(k, 0.0) + dv

                queue.append((new_state, path + [act]))

        # Filter down to the true Pareto frontier
        return self.extract_pareto_frontier(completed_pathways)
