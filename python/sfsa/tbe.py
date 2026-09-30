"""
sfsa.tbe — Temporal Budget Engine (TBE)
======================================
Manages computational execution time adaptively across extended scientific sessions or agent workflows.
Allocates time quotas dynamically between exploratory low-fidelity sweeps and late-stage precision
refinement, ensuring deadlines are honored without exhausting compute prematurely.

Part of SFSA (Standard Framework for Scientific Advancement)
Author & Protocol Creator: Alejo Malia
License: CC BY 4.0
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional
import time


class BudgetStrategy(str, Enum):
    EXPEDIENT_EXPLORATION = "EXPEDIENT_EXPLORATION" # Front-load rapid cheap checks, reserve for broad search
    BALANCED_PIPELINE = "BALANCED_PIPELINE"         # Uniform allocation across discovery and solver stages
    DEEP_REFINEMENT = "DEEP_REFINEMENT"             # Heavy budget reserved for high-fidelity convergence


@dataclass
class BudgetAllocation:
    """Dynamic computation quota for an imminent task."""
    task_id: str
    allocated_seconds: float
    remaining_total_seconds: float
    recommended_strategy: BudgetStrategy
    can_proceed: bool
    rationale: str


class TemporalBudgetEngine:
    """
    TBE governs wall-clock consumption to keep exploratory campaigns within bounds.
    """

    def __init__(self, total_budget_seconds: float = 60.0) -> None:
        self.total_budget = total_budget_seconds
        self.spent_seconds: float = 0.0
        self.start_timestamp: float = time.time()
        self.task_history: List[Dict[str, Any]] = []

    def get_remaining_seconds(self) -> float:
        """Returns remaining available budget."""
        elapsed = time.time() - self.start_timestamp
        return max(0.0, self.total_budget - max(elapsed, self.spent_seconds))

    def request_allocation(
        self,
        task_id: str,
        expected_cost_seconds: float,
        priority: float = 1.0, # 1.0 = standard, > 1.0 = high priority
    ) -> BudgetAllocation:
        """
        Dynamically allocates computational time slice based on remaining reserves and priority.
        """
        if not (expected_cost_seconds >= 0.0) or not (priority > 0.0):
            raise ValueError("expected_cost_seconds must be >= 0 and priority must be > 0")
        rem = self.get_remaining_seconds()

        if rem <= 0.0:
            return BudgetAllocation(
                task_id=task_id,
                allocated_seconds=0.0,
                remaining_total_seconds=0.0,
                recommended_strategy=BudgetStrategy.EXPEDIENT_EXPLORATION,
                can_proceed=False,
                rationale="Computational budget exhausted for current session",
            )

        # Determine strategy based on proportion of remaining budget
        ratio_left = rem / max(self.total_budget, 1e-6)
        if ratio_left > 0.6:
            strat = BudgetStrategy.EXPEDIENT_EXPLORATION
            quota = min(rem * 0.25 * priority, expected_cost_seconds * 1.5)
        elif ratio_left > 0.25:
            strat = BudgetStrategy.BALANCED_PIPELINE
            quota = min(rem * 0.40 * priority, expected_cost_seconds * 1.2)
        else:
            strat = BudgetStrategy.DEEP_REFINEMENT
            quota = min(rem * 0.70, expected_cost_seconds)

        can_proceed = quota >= expected_cost_seconds * 0.5

        return BudgetAllocation(
            task_id=task_id,
            allocated_seconds=quota,
            remaining_total_seconds=rem,
            recommended_strategy=strat,
            can_proceed=can_proceed,
            rationale=f"Allocated {quota:.2f}s under strategy {strat.value} (reserve={rem:.2f}s)",
        )

    def record_usage(self, task_id: str, seconds_used: float) -> None:
        """Logs actual execution time spent."""
        self.spent_seconds += seconds_used
        self.task_history.append({"task_id": task_id, "used": seconds_used, "timestamp": time.time()})
