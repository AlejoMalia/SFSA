"""
sfsa.rfe — Result Forgetting Engine (RFE)
========================================
Manages scientific cache lifecycle and evicts obsolete, low-utility, or context-invalidated entries.
Weighs the cost of recomputation against memory footprint, historical reuse frequency, and parameter
drift, ensuring the MATE memoization engine stays fast, lightweight, and relevant in massive sessions.

Part of SFSA (Standard Framework for Scientific Advancement)
Author & Protocol Creator: Alejo Malia
License: CC BY 4.0
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Set
import math
import time


@dataclass
class RetentionScore:
    """Utility score indicating retention value for a cached result."""
    key: str
    reuse_count: int
    age_seconds: float
    recompute_cost_estimate: float
    retention_score: float
    evict_recommended: bool


class ResultForgettingEngine:
    """
    RFE maintains cache hygiene by purging stale or trivial computation entries.
    """

    def __init__(self, max_cache_entries: int = 10000, max_age_seconds: float = 86400.0) -> None:
        self.max_entries = max_cache_entries
        self.max_age = max_age_seconds
        self.entry_metadata: Dict[str, Dict[str, Any]] = {}

    def track_entry(self, key: str, recompute_cost_ms: float = 1.0) -> None:
        """Registers a newly cached entry."""
        self.entry_metadata[key] = {
            "created_at": time.time(),
            "last_accessed": time.time(),
            "access_count": 1,
            "cost_ms": recompute_cost_ms,
        }

    def record_access(self, key: str) -> None:
        """Updates hit count and recency."""
        if key in self.entry_metadata:
            self.entry_metadata[key]["last_accessed"] = time.time()
            self.entry_metadata[key]["access_count"] += 1

    def assess_retention(self, key: str) -> Optional[RetentionScore]:
        """Calculates retention score."""
        meta = self.entry_metadata.get(key)
        if not meta:
            return None

        now = time.time()
        age = now - meta["created_at"]
        idle = now - meta["last_accessed"]
        count = meta["access_count"]
        cost = meta["cost_ms"]

        # High score = retain (frequently used or expensive to recalculate)
        score = (count * 2.0 + math.log1p(cost)) / (1.0 + idle / 3600.0)
        evict = idle > self.max_age or (count <= 1 and idle > 300.0 and cost < 5.0)

        return RetentionScore(
            key=key,
            reuse_count=count,
            age_seconds=age,
            recompute_cost_estimate=cost,
            retention_score=score,
            evict_recommended=evict,
        )

    def identify_eviction_candidates(self, count_to_prune: int) -> List[str]:
        """Returns the keys with lowest retention utility for eviction."""
        scored = []
        for k in self.entry_metadata:
            sc = self.assess_retention(k)
            if sc:
                scored.append(sc)

        scored.sort(key=lambda s: s.retention_score)
        return [s.key for s in scored[:count_to_prune]]
