"""
sfsa.projection — LayerConsistencyProjector (Layer Coupling & Consistency Projector)
=====================================================================================
Analyzes coupling and consistency between framework layers.
Evaluates numerical parameter vectors and binary claim flags, calculating normalized
vector distance, cross-layer correlations, and detecting concrete parameter inconsistencies
(e.g., conflicting variable bounds or incompatible state values across layers).

Part of SFSA (Standard Framework for Scientific Advancement)
Author & Protocol Creator: Alejo Malia
License: CC BY 4.0
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Set, Tuple
import math


@dataclass
class ParameterCoupling:
    """Coupling relationship between two parameters across distinct layers."""
    source_layer: str
    target_layer: str
    source_param: str
    target_param: str
    correlation_ratio: float           # Scaling ratio between the two numeric values
    normalized_affinity: float         # 0.0 to 1.0 (closeness of normalized magnitude)
    description: str


@dataclass
class InconsistencyConflict:
    """A detected inconsistency or boundary violation between two layers."""
    layer_a: str
    layer_b: str
    parameter_name: str
    value_in_a: Any
    value_in_b: Any
    conflict_type: str                 # 'VALUE_MISMATCH', 'BOUND_VIOLATION', 'MUTUAL_EXCLUSION'
    description: str


@dataclass
class LayerConsistencyReport:
    """Outcome of evaluating consistency and mutual coupling between framework layers."""
    layers_evaluated: List[str]
    total_parameters_compared: int
    normalized_vector_distance: float  # 0.0 (identical normalized state) to 1.0 (orthogonal)
    strongly_coupled_pairs: List[ParameterCoupling] = field(default_factory=list)
    inconsistencies: List[InconsistencyConflict] = field(default_factory=list)
    diagnostic_summary: List[str] = field(default_factory=list)


class LayerConsistencyProjector:
    """
    Evaluator of cross-layer coupling, parameter consistency, and boundary alignment.
    Executes entirely computationally without graphics or ungrounded metaphysical claims.
    """

    def __init__(self, affinity_threshold: float = 0.25) -> None:
        self.affinity_threshold = affinity_threshold
        self._history: List[LayerConsistencyReport] = []

    def _extract_numeric_vector(self, state: Dict[str, Any]) -> Dict[str, float]:
        """Extracts numeric values and boolean flags (0.0 / 1.0) from a layer state."""
        res: Dict[str, float] = {}
        for k, v in state.items():
            if isinstance(v, bool):
                res[k] = 1.0 if v else 0.0
            elif isinstance(v, (int, float)) and not math.isnan(v):
                res[k] = float(v)
        return res

    def project_and_intersect(
        self,
        layer_a_id: str,
        layer_a_state: Dict[str, Any],
        layer_b_id: str,
        layer_b_state: Dict[str, Any],
        known_bounds: Optional[Dict[str, Tuple[float, float]]] = None,
        parameter_aliases: Optional[Dict[str, str]] = None,
    ) -> LayerConsistencyReport:
        """
        Projects two layer states and compares parameter alignment:
        1. Checks shared parameters for value mismatches or bound violations.
        2. Computes normalized vector cosine distance between states.
        3. Identifies cross-layer parameter pairs with high scaling affinity.
        """
        vec_a = self._extract_numeric_vector(layer_a_state)
        vec_b = self._extract_numeric_vector(layer_b_state)
        known_bounds = known_bounds or {}
        aliases = parameter_aliases or {}

        inconsistencies: List[InconsistencyConflict] = []
        strongly_coupled: List[ParameterCoupling] = []
        diagnostics: List[str] = []

        # 1. Direct shared-parameter consistency check
        # Map aliases to find parameters that represent the same physical quantity
        canonical_a = {aliases.get(k, k): (k, v) for k, v in vec_a.items()}
        canonical_b = {aliases.get(k, k): (k, v) for k, v in vec_b.items()}
        shared_canonical = set(canonical_a.keys()) & set(canonical_b.keys())

        for param in shared_canonical:
            orig_k_a, val_a = canonical_a[param]
            orig_k_b, val_b = canonical_b[param]

            # A. Value Mismatch Check: Same variable asserted with incompatible values (> 1% delta)
            denom = max(abs(val_a), abs(val_b), 1e-9)
            relative_diff = abs(val_a - val_b) / denom
            if relative_diff > 0.01:
                inconsistencies.append(
                    InconsistencyConflict(
                        layer_a=layer_a_id,
                        layer_b=layer_b_id,
                        parameter_name=param,
                        value_in_a=val_a,
                        value_in_b=val_b,
                        conflict_type="VALUE_MISMATCH",
                        description=f"Parameter '{param}' has conflicting values: {val_a} in '{layer_a_id}' vs {val_b} in '{layer_b_id}' (diff: {relative_diff*100:.1f}%).",
                    )
                )

            # B. Known Bound Violations
            if param in known_bounds:
                p_min, p_max = known_bounds[param]
                for lid, val in [(layer_a_id, val_a), (layer_b_id, val_b)]:
                    if val < p_min or val > p_max:
                        inconsistencies.append(
                            InconsistencyConflict(
                                layer_a=layer_a_id,
                                layer_b=layer_b_id,
                                parameter_name=param,
                                value_in_a=val_a,
                                value_in_b=val_b,
                                conflict_type="BOUND_VIOLATION",
                                description=f"Value {val} in layer '{lid}' violates configured allowable bound [{p_min}, {p_max}].",
                            )
                        )

        # 2. Vector distance (normalized cosine distance)
        norm_a = math.sqrt(sum(v**2 for v in vec_a.values())) or 1.0
        norm_b = math.sqrt(sum(v**2 for v in vec_b.values())) or 1.0
        shared_direct = set(vec_a.keys()) & set(vec_b.keys())
        overlap = sum(vec_a[k] * vec_b[k] for k in shared_direct) if shared_direct else 0.0
        cos_similarity = min(1.0, max(0.0, abs(overlap) / (norm_a * norm_b)))
        normalized_distance = 1.0 - cos_similarity

        # 3. Cross-layer Parameter Coupling & Affinity
        for k_a, v_a in vec_a.items():
            for k_b, v_b in vec_b.items():
                if abs(v_a) > 1e-12 and abs(v_b) > 1e-12:
                    ratio = v_a / v_b
                    log_order = abs(math.log10(abs(ratio) + 1e-15))
                    affinity = max(0.0, min(1.0, 1.0 - (log_order / 6.0)))

                    if affinity >= self.affinity_threshold:
                        strongly_coupled.append(
                            ParameterCoupling(
                                source_layer=layer_a_id,
                                target_layer=layer_b_id,
                                source_param=k_a,
                                target_param=k_b,
                                correlation_ratio=ratio,
                                normalized_affinity=affinity,
                                description=f"Scaling relation between {layer_a_id}.{k_a} and {layer_b_id}.{k_b} (ratio: {ratio:.3e}).",
                            )
                        )

        if inconsistencies:
            diagnostics.append(f"Detected {len(inconsistencies)} parameter inconsistencies between layers '{layer_a_id}' and '{layer_b_id}'.")
        else:
            diagnostics.append(f"Layers '{layer_a_id}' and '{layer_b_id}' are mutually consistent within tolerance.")

        report = LayerConsistencyReport(
            layers_evaluated=[layer_a_id, layer_b_id],
            total_parameters_compared=len(vec_a) + len(vec_b),
            normalized_vector_distance=normalized_distance,
            strongly_coupled_pairs=strongly_coupled,
            inconsistencies=inconsistencies,
            diagnostic_summary=diagnostics,
        )
        self._history.append(report)
        return report

    @property
    def projection_history(self) -> List[LayerConsistencyReport]:
        return list(self._history)


# Compatibility aliases
DimensionalProjectionEngine = LayerConsistencyProjector
ManifoldIntersectionReport = LayerConsistencyReport
LatentCoupling = ParameterCoupling
