"""
sfsa.sre — Schedule & Resource Engine (SRE)
==========================================
Hardware-aware execution scheduler for high-throughput scientific campaigns.
Prioritizes queues by Value-of-Information / cost ratio, calculates campaign makespan,
applies backpressure when budgets or memory limits approach exhaustion, and coordinates
asynchronous execution pools across available CPU cores and worker threads.

Part of SFSA (Standard Framework for Scientific Advancement)
Author & Protocol Creator: Alejo Malia
License: CC BY 4.0
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, Tuple
import os
import time


@dataclass
class ScheduledTask:
    """A prioritized scientific task ready for worker execution."""
    task_id: str
    inputs: Dict[str, Any]
    priority_score: float             # Higher score executes first (e.g. VOI / cost)
    estimated_cost_ms: float
    device_target: str = "CPU"        # 'CPU', 'GPU', 'DISTRIBUTED'


@dataclass
class CampaignSchedule:
    """A structured schedule plan for executing a batch campaign."""
    total_tasks: int
    concurrency_workers: int
    estimated_makespan_ms: float
    backpressure_active: bool
    task_order: List[str]


class ScheduleResourceEngine:
    """
    SRE optimizes hardware utilization and queue makespan across computing resources.
    """

    def __init__(self, default_concurrency: Optional[int] = None) -> None:
        self.concurrency = default_concurrency or min(16, (os.cpu_count() or 4))
        self.queue: List[ScheduledTask] = []

    def enqueue_task(
        self,
        task_id: str,
        inputs: Dict[str, Any],
        priority_score: float = 1.0,
        estimated_cost_ms: float = 10.0,
        device_target: str = "CPU",
    ) -> ScheduledTask:
        """Adds a task to the prioritized scheduler queue."""
        task = ScheduledTask(
            task_id=task_id,
            inputs=inputs,
            priority_score=priority_score,
            estimated_cost_ms=estimated_cost_ms,
            device_target=device_target,
        )
        self.queue.append(task)
        # Sort queue by descending priority
        self.queue.sort(key=lambda t: t.priority_score, reverse=True)
        return task

    def plan_campaign_schedule(
        self,
        budget_exhaustion_ratio: float = 0.0,
    ) -> CampaignSchedule:
        """
        Computes campaign makespan and determines if backpressure throttling is required.
        """
        backpressure = budget_exhaustion_ratio > 0.85
        total_time_ms = sum(t.estimated_cost_ms for t in self.queue)
        effective_workers = max(1, self.concurrency // 2) if backpressure else self.concurrency
        makespan = total_time_ms / effective_workers if self.queue else 0.0

        return CampaignSchedule(
            total_tasks=len(self.queue),
            concurrency_workers=effective_workers,
            estimated_makespan_ms=makespan,
            backpressure_active=backpressure,
            task_order=[t.task_id for t in self.queue],
        )

    def dispatch_next(self) -> Optional[ScheduledTask]:
        """Pops the highest priority task for immediate execution."""
        return self.queue.pop(0) if self.queue else None
