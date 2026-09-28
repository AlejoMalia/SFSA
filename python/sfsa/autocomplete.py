"""
sfsa.autocomplete — Autocomplete & Model Gap-Filling Engine
===========================================================
Autonomous gap detector and conceptual connection synthesizer for scientific frameworks.
Monitors the framework state, detects epistemic or parameter voids,
and searches registered transformation rules to connect and complete the theoretical model.

Part of SFSA (Standard Framework for Scientific Advancement)
Author & Protocol Creator: Alejo Malia
License: CC BY 4.0
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Set, Tuple


class GapType(str, Enum):
    """Types of epistemic or operational gaps in a framework."""
    MISSING_PARAMETER = "MISSING_PARAMETER"
    UNCONNECTED_LAYER = "UNCONNECTED_LAYER"
    UNBOUND_EQUATION = "UNBOUND_EQUATION"
    INCOMPLETE_MATRIX = "INCOMPLETE_MATRIX"


@dataclass
class Gap:
    """A detected gap or missing variable in the scientific framework."""
    gap_id: str
    gap_type: GapType
    target_key: str
    required_by: str
    description: str
    context: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ConnectionCandidate:
    """A synthesized candidate connection that can resolve a detected gap."""
    rule_name: str
    target_key: str
    derived_value: Any
    confidence: float                  # 0.0 to 1.0
    source_dependencies: List[str]
    derivation_notes: str


class AutocompleteEngine:
    """
    Scientific Model Autocomplete & Self-Completion Engine.
    Scans the model layers, identifies missing links, and auto-synthesizes connections.
    """

    def __init__(self) -> None:
        self._rules: Dict[str, Callable[[Dict[str, Any]], Optional[ConnectionCandidate]]] = {}
        self._history: List[Dict[str, Any]] = []

    def register_rule(
        self,
        rule_name: str,
        resolver: Callable[[Dict[str, Any]], Optional[ConnectionCandidate]],
    ) -> None:
        """Registers a domain-neutral transformation rule for resolving gaps."""
        self._rules[rule_name] = resolver

    def detect_gaps(
        self,
        current_state: Dict[str, Any],
        required_schema: Dict[str, Any],
    ) -> List[Gap]:
        """
        Detects missing fields, null values, or unpopulated relations in the model state.
        """
        gaps: List[Gap] = []
        for key, requirement in required_schema.items():
            if key not in current_state or current_state[key] is None:
                gaps.append(
                    Gap(
                        gap_id=f"gap_{key}",
                        gap_type=GapType.MISSING_PARAMETER,
                        target_key=key,
                        required_by="schema_definition",
                        description=f"Missing required parameter '{key}' ({requirement})",
                        context={"requirement": requirement, "current_keys": list(current_state.keys())},
                    )
                )
        return gaps

    def suggest_connections(
        self,
        gaps: List[Gap],
        available_state: Dict[str, Any],
    ) -> List[ConnectionCandidate]:
        """
        Queries registered rules against detected gaps to discover valid connection paths.
        """
        candidates: List[ConnectionCandidate] = []
        for gap in gaps:
            for rule_name, rule_fn in self._rules.items():
                context = {**available_state, "_target_gap": gap}
                try:
                    candidate = rule_fn(context)
                    if candidate is not None and candidate.target_key == gap.target_key:
                        candidates.append(candidate)
                except Exception:
                    continue

        candidates.sort(key=lambda c: c.confidence, reverse=True)
        return candidates

    def auto_fill(
        self,
        current_state: Dict[str, Any],
        required_schema: Dict[str, Any],
        min_confidence: float = 0.70,
    ) -> Tuple[Dict[str, Any], List[ConnectionCandidate]]:
        """
        Detects gaps, finds the highest-confidence connections, and mutates/fills
        the framework state cleanly and automatically.
        """
        updated_state = dict(current_state)
        gaps = self.detect_gaps(updated_state, required_schema)
        applied_candidates: List[ConnectionCandidate] = []

        if not gaps:
            return updated_state, []

        candidates = self.suggest_connections(gaps, updated_state)
        filled_keys: Set[str] = set()

        for cand in candidates:
            if cand.target_key not in filled_keys and cand.confidence >= min_confidence:
                updated_state[cand.target_key] = cand.derived_value
                filled_keys.add(cand.target_key)
                applied_candidates.append(cand)
                self._history.append({
                    "target_key": cand.target_key,
                    "rule": cand.rule_name,
                    "confidence": cand.confidence,
                })

        return updated_state, applied_candidates

    @property
    def resolution_history(self) -> List[Dict[str, Any]]:
        return list(self._history)
