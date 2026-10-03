"""
sfsa.sye — Symbolic Simplification & Equivalence Engine (SYE)
============================================================
Formal algebraic simplification and equivalence detection on scientific expressions.

Expressions are parsed into a restricted syntax tree (``+ - * / ** ^``, unary signs, numbers, names and a
whitelist of functions; nothing else is ever evaluated) and handled structurally, not with text
substitution. Identities that need real algebra (``log(v1/v0) + log(v2/v1) == log(v2/v0)``) are decided in
two layers:

1. an optional **symbolic proof** with ``sympy`` (used only if it is installed; SFSA has no hard dependency);
2. a seeded **numerical check** on many points of the declared domain (positive reals by default).

The result says which method decided it. A numerical agreement is strong evidence, not a proof; only the
``syntactic`` and ``symbolic`` methods are proofs.

Part of SFSA (Standard Framework for Scientific Advancement)
Author & Protocol Creator: Alejo Malia
License: CC BY 4.0
"""

from __future__ import annotations

import ast
import math
import random
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, Set, Tuple


@dataclass
class SimplifiedExpression:
    """Outcome of analyzing and symbolically simplifying an equation."""
    original_expression: str
    simplified_expression: str
    operations_eliminated_count: int
    detected_singularities: List[str]
    is_constant: bool
    constant_value: Optional[float] = None
    domain_restrictions: List[str] = field(default_factory=list)   # conditions under which the rewrite is valid


@dataclass
class EquivalenceResult:
    """Verdict on whether two expressions are equal, and how that was established."""
    equivalent: bool
    method: str                       # syntactic | symbolic | numeric | inconclusive
    proven: bool                      # True only for syntactic / symbolic
    domain: str                       # positive | real
    valid_points: int = 0
    max_error: float = 0.0
    counterexample: Optional[Dict[str, float]] = None
    note: str = ""


_FUNCS: Dict[str, Callable[..., float]] = {
    "log": math.log, "ln": math.log, "log10": math.log10, "log2": math.log2, "exp": math.exp, "sqrt": math.sqrt,
    "sin": math.sin, "cos": math.cos, "tan": math.tan, "asin": math.asin, "acos": math.acos, "atan": math.atan,
    "sinh": math.sinh, "cosh": math.cosh, "tanh": math.tanh, "abs": abs,
}
_CONSTS = {"pi": math.pi, "e": math.e}
_BINOPS = (ast.Add, ast.Sub, ast.Mult, ast.Div, ast.Pow)


def parse_expression(expr: str) -> ast.expr:
    """Parse ``expr`` into a validated tree; anything outside the whitelist raises ``ValueError``."""
    if not expr or not expr.strip():
        raise ValueError("Empty expression")
    try:
        tree = ast.parse(expr.strip().replace("^", "**"), mode="eval")
    except SyntaxError as exc:
        raise ValueError(f"Cannot parse expression {expr!r}: {exc.msg}") from exc
    for node in ast.walk(tree.body):
        if isinstance(node, (ast.BinOp,)):
            if not isinstance(node.op, _BINOPS):
                raise ValueError(f"Operator {type(node.op).__name__} is not allowed in {expr!r}")
        elif isinstance(node, ast.UnaryOp):
            if not isinstance(node.op, (ast.UAdd, ast.USub)):
                raise ValueError(f"Operator {type(node.op).__name__} is not allowed in {expr!r}")
        elif isinstance(node, ast.Constant):
            if isinstance(node.value, bool) or not isinstance(node.value, (int, float)):
                raise ValueError(f"Only numeric constants are allowed in {expr!r}")
        elif isinstance(node, ast.Name):
            pass
        elif isinstance(node, ast.Call):
            if not isinstance(node.func, ast.Name) or node.func.id not in _FUNCS or node.keywords or len(node.args) != 1:
                raise ValueError(f"Only one-argument calls to {sorted(_FUNCS)} are allowed in {expr!r}")
        elif isinstance(node, (ast.operator, ast.unaryop, ast.expr_context)):
            pass
        else:
            raise ValueError(f"Syntax element {type(node).__name__} is not allowed in {expr!r}")
    return tree.body


def _free_names(node: ast.expr) -> List[str]:
    names = {n.id for n in ast.walk(node) if isinstance(n, ast.Name) and n.id not in _CONSTS}
    funcs = {n.func.id for n in ast.walk(node) if isinstance(n, ast.Call) and isinstance(n.func, ast.Name)}
    return sorted(names - funcs)


def _count_ops(node: ast.expr) -> int:
    return sum(isinstance(n, (ast.BinOp, ast.UnaryOp, ast.Call)) for n in ast.walk(node))


def _const(v: float) -> ast.Constant:
    return ast.Constant(int(v) if float(v).is_integer() and abs(v) < 1e15 else v)


def _is_const(node: ast.expr, value: Optional[float] = None) -> bool:
    if isinstance(node, ast.Constant):
        return value is None or float(node.value) == value
    return False


def _same(a: ast.expr, b: ast.expr) -> bool:
    return ast.dump(a) == ast.dump(b)


def _eval(node: ast.expr, env: Dict[str, float]) -> float:
    """Evaluate a validated tree; raises ValueError/ZeroDivisionError/OverflowError where undefined."""
    if isinstance(node, ast.Constant):
        return float(node.value)
    if isinstance(node, ast.Name):
        if node.id in env:
            return env[node.id]
        if node.id in _CONSTS:
            return _CONSTS[node.id]
        raise ValueError(f"Unbound name {node.id}")
    if isinstance(node, ast.UnaryOp):
        v = _eval(node.operand, env)
        return -v if isinstance(node.op, ast.USub) else v
    if isinstance(node, ast.BinOp):
        a, b = _eval(node.left, env), _eval(node.right, env)
        if isinstance(node.op, ast.Add):
            return a + b
        if isinstance(node.op, ast.Sub):
            return a - b
        if isinstance(node.op, ast.Mult):
            return a * b
        if isinstance(node.op, ast.Div):
            return a / b
        r = a ** b
        if isinstance(r, complex):
            raise ValueError("complex result")
        return float(r)
    if isinstance(node, ast.Call):
        assert isinstance(node.func, ast.Name)
        return float(_FUNCS[node.func.id](_eval(node.args[0], env)))
    raise ValueError("unsupported node")


class SymbolicEquivalenceEngine:
    """
    SYE simplifies algebraic terms and decides equivalence of scientific expressions.
    """

    def __init__(self, n_points: int = 64, rel_tol: float = 1e-9, seed: int = 20260101) -> None:
        self.n_points = n_points
        self.rel_tol = rel_tol
        self.seed = seed

    # ------------------------------------------------------------------ simplification
    def _simp(self, node: ast.expr, restr: Set[str]) -> ast.expr:
        if isinstance(node, ast.UnaryOp):
            inner = self._simp(node.operand, restr)
            if isinstance(node.op, ast.UAdd):
                return inner
            if isinstance(inner, ast.Constant):
                return _const(-float(inner.value))
            if isinstance(inner, ast.UnaryOp) and isinstance(inner.op, ast.USub):
                return inner.operand
            return ast.UnaryOp(ast.USub(), inner)
        if isinstance(node, ast.Call):
            fn = node.func.id if isinstance(node.func, ast.Name) else ""
            arg = self._simp(node.args[0], restr)
            if isinstance(arg, ast.Constant):
                try:
                    return _const(_FUNCS[fn](float(arg.value)))
                except (ValueError, OverflowError):
                    pass
            if fn in ("log", "ln") and isinstance(arg, ast.Call) and isinstance(arg.func, ast.Name) and arg.func.id == "exp":
                return arg.args[0]                                   # log(exp(x)) = x  (x real)
            if fn == "exp" and isinstance(arg, ast.Call) and isinstance(arg.func, ast.Name) and arg.func.id in ("log", "ln"):
                restr.add(f"{ast.unparse(arg.args[0])} > 0")           # exp(log(x)) = x  only for x > 0
                return arg.args[0]
            return ast.Call(ast.Name(fn, ast.Load()), [arg], [])
        if not isinstance(node, ast.BinOp):
            return node
        left, right, op = self._simp(node.left, restr), self._simp(node.right, restr), node.op
        if isinstance(left, ast.Constant) and isinstance(right, ast.Constant):
            try:
                return _const(_eval(ast.BinOp(left, op, right), {}))
            except (ValueError, ZeroDivisionError, OverflowError):
                return ast.BinOp(left, op, right)
        if isinstance(op, ast.Add):
            if _is_const(left, 0):
                return right
            if _is_const(right, 0):
                return left
        elif isinstance(op, ast.Sub):
            if _is_const(right, 0):
                return left
            if _is_const(left, 0):
                return ast.UnaryOp(ast.USub(), right)
            if _same(left, right):
                return _const(0)
        elif isinstance(op, ast.Mult):
            if _is_const(left, 0) or _is_const(right, 0):
                return _const(0)
            if _is_const(left, 1):
                return right
            if _is_const(right, 1):
                return left
        elif isinstance(op, ast.Div):
            if _is_const(right, 1):
                return left
            if _same(left, right):
                restr.add(f"{ast.unparse(left)} != 0")
                return _const(1)
            if _is_const(left, 0):
                restr.add(f"{ast.unparse(right)} != 0")
                return _const(0)
        elif isinstance(op, ast.Pow):
            if _is_const(right, 1):
                return left
            if _is_const(right, 0):
                return _const(1)
            if _is_const(left, 1):
                return _const(1)
        return ast.BinOp(left, op, right)

    def _poles(self, node: ast.expr) -> List[str]:
        out: List[str] = []
        for n in ast.walk(node):
            den: Optional[ast.expr] = None
            if isinstance(n, ast.BinOp) and isinstance(n.op, ast.Div):
                den = n.right
            elif (isinstance(n, ast.BinOp) and isinstance(n.op, ast.Pow) and isinstance(n.right, ast.Constant)
                  and float(n.right.value) < 0):
                den = n.left
            if den is None:
                continue
            if isinstance(den, ast.Constant):
                if float(den.value) == 0:
                    out.append("Division by the constant 0")
                continue
            msg = f"Pole at {ast.unparse(den)} == 0"
            if msg not in out:
                out.append(msg)
        return out

    def _domain(self, node: ast.expr) -> List[str]:
        out: List[str] = []
        for n in ast.walk(node):
            if isinstance(n, ast.Call) and isinstance(n.func, ast.Name):
                a = ast.unparse(n.args[0])
                if n.func.id in ("log", "ln", "log10", "log2"):
                    out.append(f"{a} > 0")
                elif n.func.id == "sqrt":
                    out.append(f"{a} >= 0")
                elif n.func.id in ("asin", "acos"):
                    out.append(f"-1 <= {a} <= 1")
        return out

    def simplify(self, expr_str: str) -> SimplifiedExpression:
        """Applies identity-folding rules on the expression tree and reports poles and domain conditions."""
        original = parse_expression(expr_str)
        restr: Set[str] = set()
        simplified = self._simp(original, restr)
        # a second pass lets rewrites enabled by the first one fire (e.g. (x - x) * y + z)
        for _ in range(4):
            again = self._simp(simplified, restr)
            if _same(again, simplified):
                break
            simplified = again
        const_val = float(simplified.value) if isinstance(simplified, ast.Constant) else None
        restrictions = sorted(restr | set(self._domain(simplified)))
        return SimplifiedExpression(
            original_expression=expr_str,
            simplified_expression=ast.unparse(simplified),
            operations_eliminated_count=max(_count_ops(original) - _count_ops(simplified), 0),
            detected_singularities=self._poles(simplified),
            is_constant=const_val is not None,
            constant_value=const_val,
            domain_restrictions=restrictions,
        )

    # ------------------------------------------------------------------ equivalence
    def _to_sympy(self, node: ast.expr, sp: Any, symbols: Dict[str, Any]) -> Any:
        if isinstance(node, ast.Constant):
            return sp.Integer(node.value) if isinstance(node.value, int) else sp.Float(node.value)
        if isinstance(node, ast.Name):
            if node.id == "pi":
                return sp.pi
            if node.id == "e":
                return sp.E
            return symbols.setdefault(node.id, sp.Symbol(node.id, positive=True))
        if isinstance(node, ast.UnaryOp):
            v = self._to_sympy(node.operand, sp, symbols)
            return -v if isinstance(node.op, ast.USub) else v
        if isinstance(node, ast.BinOp):
            a, b = self._to_sympy(node.left, sp, symbols), self._to_sympy(node.right, sp, symbols)
            return {ast.Add: lambda: a + b, ast.Sub: lambda: a - b, ast.Mult: lambda: a * b,
                    ast.Div: lambda: a / b, ast.Pow: lambda: a ** b}[type(node.op)]()
        assert isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
        f, x = node.func.id, self._to_sympy(node.args[0], sp, symbols)
        table = {"log": sp.log, "ln": sp.log, "exp": sp.exp, "sqrt": sp.sqrt, "sin": sp.sin, "cos": sp.cos, "tan": sp.tan,
                 "asin": sp.asin, "acos": sp.acos, "atan": sp.atan, "sinh": sp.sinh, "cosh": sp.cosh, "tanh": sp.tanh,
                 "abs": sp.Abs}
        if f == "log10":
            return sp.log(x, 10)
        if f == "log2":
            return sp.log(x, 2)
        return table[f](x)

    def _sympy_proof(self, a: ast.expr, b: ast.expr) -> bool:
        try:
            import sympy as sp
        except ImportError:
            return False
        try:
            symbols: Dict[str, Any] = {}
            diff = self._to_sympy(a, sp, symbols) - self._to_sympy(b, sp, symbols)
            for step in (sp.simplify, lambda d: sp.simplify(sp.expand_log(d, force=True)), sp.logcombine):
                if step(diff) == 0:
                    return True
        except Exception:                                       # a failed proof attempt is not an error
            return False
        return False

    def _sample(self, rng: random.Random, names: List[str], domain: str, i: int) -> Dict[str, float]:
        if i == 0:
            return {n: 1.0 for n in names}
        if i == 1:
            return {n: 2.0 for n in names}
        out = {}
        for n in names:
            mag = 10 ** rng.uniform(-1.3, 1.3)
            out[n] = mag if domain == "positive" or rng.random() < 0.5 else -mag
        return out

    def check_equivalence(self, expr_a: str, expr_b: str, domain: str = "positive") -> EquivalenceResult:
        """Decide whether two expressions are equal and report how.

        ``domain='positive'`` (default) tests positive real variables, the usual case for physical
        quantities; ``domain='real'`` also samples negative values and requires both sides to be defined on
        exactly the same points.
        """
        if domain not in ("positive", "real"):
            raise ValueError("domain must be 'positive' or 'real'")
        a, b = parse_expression(expr_a), parse_expression(expr_b)
        sa, sb = self.simplify(expr_a), self.simplify(expr_b)
        if sa.simplified_expression == sb.simplified_expression:
            return EquivalenceResult(True, "syntactic", True, domain, note="identical after simplification")
        names = sorted(set(_free_names(a)) | set(_free_names(b)))
        if domain == "positive" and self._sympy_proof(a, b):
            return EquivalenceResult(True, "symbolic", True, "positive", note="proved with sympy for positive real variables")

        rng = random.Random(self.seed)
        valid, worst, mismatch = 0, 0.0, 0
        for i in range(self.n_points):
            env = self._sample(rng, names, domain, i)
            va = vb = None
            try:
                va = _eval(a, env)
            except (ValueError, ZeroDivisionError, OverflowError):
                pass
            try:
                vb = _eval(b, env)
            except (ValueError, ZeroDivisionError, OverflowError):
                pass
            if va is None and vb is None:
                continue
            if va is None or vb is None:
                mismatch += 1
                if domain == "real":
                    return EquivalenceResult(False, "numeric", False, domain, valid, worst, env,
                                             "defined on different domains at this point")
                continue
            if not (math.isfinite(va) and math.isfinite(vb)):
                continue
            err = abs(va - vb) / max(1.0, abs(va), abs(vb))
            valid += 1
            worst = max(worst, err)
            if err > self.rel_tol:
                return EquivalenceResult(False, "numeric", False, domain, valid, worst, env,
                                         f"values differ: {va!r} vs {vb!r}")
        if valid < max(8, self.n_points // 4):
            return EquivalenceResult(False, "inconclusive", False, domain, valid, worst,
                                     note="too few points where both expressions are defined")
        return EquivalenceResult(True, "numeric", False, domain, valid, worst,
                                 note=f"agree on {valid} points (max rel. error {worst:.2e}); strong evidence, not a proof")

    def are_equivalent(self, expr_a: str, expr_b: str, domain: str = "positive") -> bool:
        """True if :meth:`check_equivalence` finds the two expressions equal (see its ``method``/``proven``)."""
        return self.check_equivalence(expr_a, expr_b, domain).equivalent
