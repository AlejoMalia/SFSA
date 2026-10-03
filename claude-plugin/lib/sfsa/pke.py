"""
sfsa.pke — Partial Knowledge Engine (PKE)
========================================
Extracts and caches valuable intermediate computation states (bounds, residuals, partial trajectories,
and approximate gradients) from interrupted, aborted, or ongoing solver runs. Prevents discarding
valuable exploratory work, providing bounded approximations and guidance for parallel branches.

Part of SFSA (Standard Framework for Scientific Advancement)
Author & Protocol Creator: Alejo Malia
License: CC BY 4.0
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
import time


@dataclass
class PartialKnowledge:
    """An intermediate observation captured from a solver before termination."""
    knowledge_id: str
    task_id: str
    iteration_reached: int
    latest_estimate: Any
    lower_bound: Optional[float]
    upper_bound: Optional[float]
    residual: Optional[float]
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: float = field(default_factory=time.time)


class PartialKnowledgeEngine:
    """
    PKE salvages compute investments from aborted or partial calculations.
    """

    def __init__(self) -> None:
        self.store: Dict[str, List[PartialKnowledge]] = {}

    def capture(
        self,
        task_id: str,
        iteration: int,
        estimate: Any,
        lower_bound: Optional[float] = None,
        upper_bound: Optional[float] = None,
        residual: Optional[float] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> PartialKnowledge:
        """Saves intermediate solver knowledge."""
        pk = PartialKnowledge(
            knowledge_id=f"pk_{task_id}_{iteration}_{int(time.time() * 1000)}",
            task_id=task_id,
            iteration_reached=iteration,
            latest_estimate=estimate,
            lower_bound=lower_bound,
            upper_bound=upper_bound,
            residual=residual,
            metadata=metadata or {},
        )
        self.store.setdefault(task_id, []).append(pk)
        return pk

    def get_latest(self, task_id: str) -> Optional[PartialKnowledge]:
        """Retrieves the most recent partial knowledge for a task."""
        records = self.store.get(task_id, [])
        return records[-1] if records else None

    def get_tightest_bounds(self, task_id: str) -> Tuple[Optional[float], Optional[float]]:
        """Returns the best (tightest) bounds extracted across all partial attempts."""
        records = self.store.get(task_id, [])
        if not records:
            return None, None
        lowers = [r.lower_bound for r in records if r.lower_bound is not None]
        uppers = [r.upper_bound for r in records if r.upper_bound is not None]
        best_lower = max(lowers) if lowers else None
        best_upper = min(uppers) if uppers else None
        return best_lower, best_upper
