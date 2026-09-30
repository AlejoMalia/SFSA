"""
sfsa.sye — Symbolic Simplification & Equivalence Engine (SYE)
============================================================
Performs formal algebraic simplification and equivalence detection on scientific expressions.
Eliminates redundant terms, folds identities (e.g. 0 * f(x) -> 0, 1 * f(x) -> f(x), log(exp(x)) -> x),
and detects mathematical singularities prior to compiling or numerically evaluating solvers.

Part of SFSA (Standard Framework for Scientific Advancement)
Author & Protocol Creator: Alejo Malia
License: CC BY 4.0
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Set, Tuple
import re


@dataclass
class SimplifiedExpression:
    """Outcome of analyzing and symbolically simplifying an equation."""
    original_expression: str
    simplified_expression: str
    operations_eliminated_count: int
    detected_singularities: List[str]
    is_constant: bool
    constant_value: Optional[float] = None


class SymbolicEquivalenceEngine:
    """
    SYE simplifies algebraic terms and detects closed-form identities.
    """

    def __init__(self) -> None:
        self.rules = [
            (r"\b0\s*\*\s*([a-zA-Z0-9_]+)", "0"),            # 0 * x -> 0
            (r"([a-zA-Z0-9_]+)\s*\*\s*0\b", "0"),            # x * 0 -> 0
            (r"\b1\s*\*\s*([a-zA-Z0-9_]+)", r"\1"),          # 1 * x -> x
            (r"([a-zA-Z0-9_]+)\s*\*\s*1\b", r"\1"),          # x * 1 -> x
            (r"\b0\s*\+\s*([a-zA-Z0-9_]+)", r"\1"),          # 0 + x -> x
            (r"([a-zA-Z0-9_]+)\s*\+\s*0\b", r"\1"),          # x + 0 -> x
            (r"([a-zA-Z0-9_]+)\s*-\s*\1\b", "0"),            # x - x -> 0
            (r"log\s*\(\s*exp\s*\(([^)]+)\)\s*\)", r"\1"),   # log(exp(x)) -> x
            (r"exp\s*\(\s*log\s*\(([^)]+)\)\s*\)", r"\1"),   # exp(log(x)) -> x
        ]

    def simplify(self, expr_str: str) -> SimplifiedExpression:
        """Applies canonical algebraic reduction rules to an expression string."""
        current = expr_str.strip()
        ops_eliminated = 0

        for pattern, replacement in self.rules:
            new_expr, count = re.subn(pattern, replacement, current)
            if count > 0:
                ops_eliminated += count
                current = new_expr

        # Clean multiple spaces
        current = re.sub(r"\s+", " ", current)

        # Detect potential divide-by-zero singularities
        singularities = []
        div_matches = re.findall(r"/\s*([a-zA-Z0-9_]+)", current)
        for var in div_matches:
            if var != "0":
                singularities.append(f"Pole at {var} == 0")

        # Check if collapsed to a numeric constant
        is_const = False
        const_val = None
        try:
            const_val = float(current)
            is_const = True
        except ValueError:
            pass

        return SimplifiedExpression(
            original_expression=expr_str,
            simplified_expression=current,
            operations_eliminated_count=ops_eliminated,
            detected_singularities=singularities,
            is_constant=is_const,
            constant_value=const_val,
        )

    def are_equivalent(self, expr_a: str, expr_b: str) -> bool:
        """Determines if two expressions simplify to the same canonical representation."""
        sim_a = self.simplify(expr_a).simplified_expression.replace(" ", "")
        sim_b = self.simplify(expr_b).simplified_expression.replace(" ", "")
        return sim_a == sim_b

