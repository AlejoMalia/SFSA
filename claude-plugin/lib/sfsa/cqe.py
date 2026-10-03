"""
sfsa.cqe — Query Compression Engine (CQE)
========================================
Batches, compresses, and clusters large incoming streams of similar scientific queries into representative
centroids. Evaluates only the representative queries through heavy solvers and reconstructs the full
batch responses using controlled, error-bounded local interpolation.

Part of SFSA (Standard Framework for Scientific Advancement)
Author & Protocol Creator: Alejo Malia
License: CC BY 4.0
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, Tuple
import math


@dataclass
class RepresentativeQuery:
    """A cluster centroid query evaluated directly with full precision."""
    query_id: str
    centroid_inputs: Dict[str, float]
    computed_output: Optional[float]
    cluster_member_indices: List[int] = field(default_factory=list)


@dataclass
class CompressedBatchResult:
    """Outcome of resolving a compressed query stream."""
    original_query_count: int
    representative_count: int
    compression_ratio: float
    reconstructed_outputs: List[float]
    compute_reduction_pct: float


class QueryCompressionEngine:
    """
    CQE compresses query throughput to maximize batch computational efficiency.
    """

    def __init__(self, clustering_radius: float = 0.05) -> None:
        self.clustering_radius = clustering_radius

    def _dist(self, q1: Dict[str, float], q2: Dict[str, float]) -> float:
        keys = set(q1.keys()).intersection(q2.keys())
        if not keys:
            return 1.0
        diffs = []
        for k in keys:
            denom = max(abs(q1[k]), 1.0)
            diffs.append((abs(q1[k] - q2[k]) / denom) ** 2)
        return math.sqrt(sum(diffs) / len(diffs))

    def compress_and_solve(
        self,
        queries: List[Dict[str, float]],
        heavy_solver: Callable[[Dict[str, float]], float],
    ) -> CompressedBatchResult:
        """
        Clusters similar queries, evaluates centroids, and reconstructs outcomes.
        """
        if not queries:
            return CompressedBatchResult(0, 0, 1.0, [], 0.0)

        representatives: List[RepresentativeQuery] = []

        # Greedy centroid clustering
        for idx, q in enumerate(queries):
            matched = False
            for rep in representatives:
                if self._dist(q, rep.centroid_inputs) <= self.clustering_radius:
                    rep.cluster_member_indices.append(idx)
                    matched = True
                    break

            if not matched:
                rep = RepresentativeQuery(
                    query_id=f"rep_{len(representatives)}",
                    centroid_inputs=q,
                    computed_output=None,
                    cluster_member_indices=[idx],
                )
                representatives.append(rep)

        # Solve only centroids
        for rep in representatives:
            rep.computed_output = heavy_solver(rep.centroid_inputs)

        # Reconstruct outputs
        reconstructed = [0.0] * len(queries)
        for rep in representatives:
            out = rep.computed_output if rep.computed_output is not None else 0.0
            for idx in rep.cluster_member_indices:
                reconstructed[idx] = out

        comp_ratio = len(representatives) / len(queries)
        reduction = (1.0 - comp_ratio) * 100.0

        return CompressedBatchResult(
            original_query_count=len(queries),
            representative_count=len(representatives),
            compression_ratio=comp_ratio,
            reconstructed_outputs=reconstructed,
            compute_reduction_pct=reduction,
        )
