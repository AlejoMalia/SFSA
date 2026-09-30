"""
sfsa.pbe — Parallel Batch & Dispatch Engine (PBE)
================================================
Concurrent scientific workload dispatcher. Distributes heavy query batches, centroid evaluations (CQE),
and adaptive sampling candidates (ASG) across parallel worker threads/processes, unlocking native
multi-core CPU parallelism while keeping the SFSA API synchronous and clean.

Part of SFSA (Standard Framework for Scientific Advancement)
Author & Protocol Creator: Alejo Malia
License: CC BY 4.0
"""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional
import os
import time


@dataclass
class BatchExecutionSummary:
    """Outcome of executing a scientific batch across parallel workers."""
    total_items: int
    successful_items: int
    failed_items: int
    concurrency_level: int
    wall_clock_ms: float
    results: List[Any]


class ParallelBatchEngine:
    """
    PBE scales batch evaluations across multi-core architectures.
    """

    def __init__(self, max_workers: Optional[int] = None) -> None:
        self.max_workers = max_workers or min(32, (os.cpu_count() or 4))

    def map_concurrent(
        self,
        items: List[Any],
        worker_fn: Callable[[Any], Any],
        max_workers: Optional[int] = None,
    ) -> BatchExecutionSummary:
        """
        Executes worker_fn concurrently over items with bounded thread pool.
        """
        workers = max_workers or self.max_workers
        workers = min(workers, max(1, len(items)))

        t0 = time.perf_counter()
        results: List[Any] = [None] * len(items)
        successes = 0
        failures = 0

        with ThreadPoolExecutor(max_workers=workers) as executor:
            future_to_idx = {executor.submit(worker_fn, item): idx for idx, item in enumerate(items)}
            for future in as_completed(future_to_idx):
                idx = future_to_idx[future]
                try:
                    res = future.result()
                    results[idx] = res
                    successes += 1
                except Exception as e:
                    results[idx] = {"error": str(e)}
                    failures += 1

        elapsed = (time.perf_counter() - t0) * 1000.0

        return BatchExecutionSummary(
            total_items=len(items),
            successful_items=successes,
            failed_items=failures,
            concurrency_level=workers,
            wall_clock_ms=elapsed,
            results=results,
        )
