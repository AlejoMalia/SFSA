"""
sfsa.aie — Assumption Integrity Engine (AIE)
============================================
Monitors model premises and operational assumptions as simulations and computations evolve.
Detects regime transitions where initial idealizations (e.g. laminar flow, dilute limit, ideal gas,
variable independence) become invalid, raising audit flags and triggering model adjustments.

Part of SFSA (Standard Framework for Scientific Advancement)
Author & Protocol Creator: Alejo Malia
License: CC BY 4.0
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, Tuple


@dataclass
class ModelAssumption:
    """A declared scientific hypothesis or physical regime assumption."""
    assumption_id: str
    name: str
    condition_fn: Callable[[Dict[str, Any]], Tuple[bool, str]]
    criticality: str                 # 'WARNING', 'FAIL_STOP', 'SWITCH_MODEL'
    description: str


@dataclass
class AssumptionViolation:
    """An alert raised when computational values breach a model assumption."""
    assumption_id: str
    name: str
    criticality: str
    diagnostic_message: str
    violating_state: Dict[str, Any]


class AssumptionIntegrityEngine:
    """
    AIE guards scientific validity by continuously auditing underlying assumptions.
    """

    def __init__(self) -> None:
        self.assumptions: Dict[str, ModelAssumption] = {}
        self.violation_history: List[AssumptionViolation] = []

    def register_assumption(
        self,
        assumption_id: str,
        name: str,
        condition_fn: Callable[[Dict[str, Any]], Tuple[bool, str]],
        criticality: str = "WARNING",
        description: str = "",
    ) -> None:
        """Registers a premise that must remain true during simulation."""
        self.assumptions[assumption_id] = ModelAssumption(
            assumption_id=assumption_id,
            name=name,
            condition_fn=condition_fn,
            criticality=criticality,
            description=description,
        )

    def audit_state(self, current_state: Dict[str, Any]) -> List[AssumptionViolation]:
        """
        Tests the current state against all registered model assumptions.
        """
        violations: List[AssumptionViolation] = []
        for a_id, asm in self.assumptions.items():
            try:
                valid, reason = asm.condition_fn(current_state)
            except Exception as exc:  # an assumption that cannot be evaluated cannot be assumed to hold
                valid, reason = False, f"assumption could not be evaluated ({type(exc).__name__}: {exc})"
            if not valid:
                violation = AssumptionViolation(
                    assumption_id=a_id,
                    name=asm.name,
                    criticality=asm.criticality,
                    diagnostic_message=reason,
                    violating_state=dict(current_state),
                )
                violations.append(violation)
                self.violation_history.append(violation)

        return violations
