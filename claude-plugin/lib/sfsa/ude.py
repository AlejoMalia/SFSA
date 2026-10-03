"""
sfsa.ude — Unit & Dimensional Analysis Engine (UDE)
==================================================
Guarantees formal dimensional homogeneity across all layer transfers and scientific computations.
Tracks SI base dimension exponents [M, L, T, Theta, N, I, J], verifying compatibility in O(1)
and preventing silent scale/unit conversion disasters (e.g., Pascal vs. Bar, Joule vs. eV).

Part of SFSA (Standard Framework for Scientific Advancement)
Author & Protocol Creator: Alejo Malia
License: CC BY 4.0
"""

from __future__ import annotations

import difflib
import math
import re
from dataclasses import dataclass, field
from fractions import Fraction
from typing import Any, Dict, List, Optional, Tuple, Union

Exponent = Union[int, Fraction]


@dataclass(frozen=True)
class DimensionVector:
    """SI fundamental physical dimension vector: [Mass, Length, Time, Temp, Amount, Current, Luminous]."""
    mass: Exponent = 0      # kg
    length: Exponent = 0    # m
    time: Exponent = 0      # s
    temp: Exponent = 0      # K
    amount: Exponent = 0    # mol
    current: Exponent = 0   # A
    luminous: Exponent = 0  # cd

    def __post_init__(self) -> None:
        # Exponents may be rational (sqrt(Hz) has time^-1/2); integral values are stored as int so that
        # DimensionVector(length=1) == DimensionVector(length=Fraction(2, 2)) and printing stays clean.
        for name in ("mass", "length", "time", "temp", "amount", "current", "luminous"):
            v = Fraction(getattr(self, name))
            object.__setattr__(self, name, int(v) if v.denominator == 1 else v)

    def _combine(self, other: DimensionVector, sign: int) -> DimensionVector:
        return DimensionVector(
            self.mass + sign * other.mass, self.length + sign * other.length, self.time + sign * other.time,
            self.temp + sign * other.temp, self.amount + sign * other.amount,
            self.current + sign * other.current, self.luminous + sign * other.luminous,
        )

    def __mul__(self, other: DimensionVector) -> DimensionVector:
        """Dimension of a product of quantities."""
        return self._combine(other, +1)

    def __truediv__(self, other: DimensionVector) -> DimensionVector:
        """Dimension of a quotient of quantities."""
        return self._combine(other, -1)

    def __pow__(self, p: Exponent) -> DimensionVector:
        f = Fraction(p)
        return DimensionVector(self.mass * f, self.length * f, self.time * f, self.temp * f,
                               self.amount * f, self.current * f, self.luminous * f)

    def label(self) -> str:
        """Human-readable form, e.g. ``kg^1 m^-1 s^-2`` (``1`` when dimensionless)."""
        names = (("kg", self.mass), ("m", self.length), ("s", self.time), ("K", self.temp),
                 ("mol", self.amount), ("A", self.current), ("cd", self.luminous))
        parts = [f"{n}^{e}" for n, e in names if e != 0]
        return " ".join(parts) if parts else "1"

    def __add__(self, other: DimensionVector) -> DimensionVector:
        return self._combine(other, +1)

    def __sub__(self, other: DimensionVector) -> DimensionVector:
        return self._combine(other, -1)

    def is_dimensionless(self) -> bool:
        return (
            self.mass == 0 and self.length == 0 and self.time == 0 and
            self.temp == 0 and self.amount == 0 and self.current == 0 and self.luminous == 0
        )


# Legacy lowercase aliases (v0.2.0 registry). Kept so that old call sites such as ``parse_unit('kpa')`` or
# ``'mpa'`` (= MPa) still resolve; they are consulted only after the case-sensitive SI lookup below.
CANONICAL_DIMENSIONS: Dict[str, Tuple[DimensionVector, float]] = {
    # Dimensionless
    "dimensionless": (DimensionVector(), 1.0),
    "fraction": (DimensionVector(), 1.0),
    "percent": (DimensionVector(), 0.01),
    # Length
    "m": (DimensionVector(length=1), 1.0),
    "meter": (DimensionVector(length=1), 1.0),
    "km": (DimensionVector(length=1), 1e3),
    "mm": (DimensionVector(length=1), 1e-3),
    "cm": (DimensionVector(length=1), 1e-2),
    # Mass
    "kg": (DimensionVector(mass=1), 1.0),
    "g": (DimensionVector(mass=1), 1e-3),
    "tonne": (DimensionVector(mass=1), 1e3),
    # Time
    "s": (DimensionVector(time=1), 1.0),
    "second": (DimensionVector(time=1), 1.0),
    "min": (DimensionVector(time=1), 60.0),
    "hour": (DimensionVector(time=1), 3600.0),
    "year": (DimensionVector(time=1), 31557600.0),
    # Temperature
    "k": (DimensionVector(temp=1), 1.0),
    "kelvin": (DimensionVector(temp=1), 1.0),
    # Pressure: [M=1, L=-1, T=-2]
    "pa": (DimensionVector(mass=1, length=-1, time=-2), 1.0),
    "pascal": (DimensionVector(mass=1, length=-1, time=-2), 1.0),
    "bar": (DimensionVector(mass=1, length=-1, time=-2), 1e5),
    "atm": (DimensionVector(mass=1, length=-1, time=-2), 101325.0),
    "kpa": (DimensionVector(mass=1, length=-1, time=-2), 1e3),
    "mpa": (DimensionVector(mass=1, length=-1, time=-2), 1e6),
    # Energy: [M=1, L=2, T=-2]
    "j": (DimensionVector(mass=1, length=2, time=-2), 1.0),
    "joule": (DimensionVector(mass=1, length=2, time=-2), 1.0),
    "kj": (DimensionVector(mass=1, length=2, time=-2), 1e3),
    "ev": (DimensionVector(mass=1, length=2, time=-2), 1.602176634e-19),
    # Force: [M=1, L=1, T=-2]
    "n": (DimensionVector(mass=1, length=1, time=-2), 1.0),
    "newton": (DimensionVector(mass=1, length=1, time=-2), 1.0),
    # Power: [M=1, L=2, T=-3]
    "w": (DimensionVector(mass=1, length=2, time=-3), 1.0),
    "watt": (DimensionVector(mass=1, length=2, time=-3), 1.0),
    "kw": (DimensionVector(mass=1, length=2, time=-3), 1e3),
    "mw": (DimensionVector(mass=1, length=2, time=-3), 1e6),
}


class UnknownUnitError(ValueError):
    """A unit name that is not in the registry. Never silently treated as dimensionless."""


class UnitSyntaxError(ValueError):
    """A malformed unit expression (e.g. ``m2`` without an operator, unbalanced parentheses)."""


# ---------------------------------------------------------------------------------------------------
# Case-sensitive SI registry: name -> (dimension, factor to SI base units)
# ---------------------------------------------------------------------------------------------------
_L = DimensionVector(length=1)
_M = DimensionVector(mass=1)
_T = DimensionVector(time=1)
_PRESSURE = DimensionVector(mass=1, length=-1, time=-2)
_ENERGY = DimensionVector(mass=1, length=2, time=-2)
_POWER = DimensionVector(mass=1, length=2, time=-3)
_FORCE = DimensionVector(mass=1, length=1, time=-2)
_CURRENT = DimensionVector(current=1)
_CHARGE = DimensionVector(time=1, current=1)
_VOLTAGE = DimensionVector(mass=1, length=2, time=-3, current=-1)
_ONE = DimensionVector()
_AU_M = 149_597_870_700.0                        # IAU 2012, exact
_YEAR_S = 31_557_600.0                           # Julian year, IAU

SI_UNITS: Dict[str, Tuple[DimensionVector, float]] = {
    # dimensionless
    "dimensionless": (_ONE, 1.0), "fraction": (_ONE, 1.0), "percent": (_ONE, 0.01), "%": (_ONE, 0.01),
    "ppm": (_ONE, 1e-6), "ppb": (_ONE, 1e-9), "rad": (_ONE, 1.0), "sr": (_ONE, 1.0),
    "deg": (_ONE, math.pi / 180.0), "arcsec": (_ONE, math.pi / 648000.0),
    # length
    "m": (_L, 1.0), "meter": (_L, 1.0), "metre": (_L, 1.0), "AU": (_L, _AU_M),
    "ly": (_L, 299_792_458.0 * _YEAR_S), "pc": (_L, _AU_M * 648000.0 / math.pi),
    "in": (_L, 0.0254), "ft": (_L, 0.3048), "mile": (_L, 1609.344), "nmi": (_L, 1852.0), "angstrom": (_L, 1e-10),
    # mass
    "kg": (_M, 1.0), "g": (_M, 1e-3), "tonne": (_M, 1e3), "lb": (_M, 0.45359237),
    "u": (_M, 1.66053906660e-27), "Da": (_M, 1.66053906660e-27),
    # time
    "s": (_T, 1.0), "second": (_T, 1.0), "min": (_T, 60.0), "minute": (_T, 60.0), "h": (_T, 3600.0), "hour": (_T, 3600.0),
    "day": (_T, 86400.0), "d": (_T, 86400.0), "week": (_T, 604800.0), "month": (_T, _YEAR_S / 12.0),
    "year": (_T, _YEAR_S), "yr": (_T, _YEAR_S),
    "Hz": (DimensionVector(time=-1), 1.0), "hertz": (DimensionVector(time=-1), 1.0),
    # temperature (intervals; absolute offsets are handled in ``convert``)
    "K": (DimensionVector(temp=1), 1.0), "kelvin": (DimensionVector(temp=1), 1.0),
    "degC": (DimensionVector(temp=1), 1.0), "°C": (DimensionVector(temp=1), 1.0), "celsius": (DimensionVector(temp=1), 1.0),
    "degF": (DimensionVector(temp=1), 5.0 / 9.0), "°F": (DimensionVector(temp=1), 5.0 / 9.0),
    # amount, current, luminous
    "mol": (DimensionVector(amount=1), 1.0), "mole": (DimensionVector(amount=1), 1.0),
    "A": (_CURRENT, 1.0), "ampere": (_CURRENT, 1.0), "cd": (DimensionVector(luminous=1), 1.0),
    # derived mechanical
    "N": (_FORCE, 1.0), "newton": (_FORCE, 1.0),
    "Pa": (_PRESSURE, 1.0), "pascal": (_PRESSURE, 1.0), "bar": (_PRESSURE, 1e5), "atm": (_PRESSURE, 101325.0),
    "torr": (_PRESSURE, 101325.0 / 760.0), "mmHg": (_PRESSURE, 133.322387415), "psi": (_PRESSURE, 6894.757293168),
    "J": (_ENERGY, 1.0), "joule": (_ENERGY, 1.0), "eV": (_ENERGY, 1.602176634e-19), "cal": (_ENERGY, 4.184),
    "Wh": (_ENERGY, 3600.0),
    "W": (_POWER, 1.0), "watt": (_POWER, 1.0),
    "L": (DimensionVector(length=3), 1e-3), "liter": (DimensionVector(length=3), 1e-3), "litre": (DimensionVector(length=3), 1e-3),
    # electrical / magnetic
    "C": (_CHARGE, 1.0), "V": (_VOLTAGE, 1.0), "volt": (_VOLTAGE, 1.0),
    "ohm": (_VOLTAGE / _CURRENT, 1.0), "Ω": (_VOLTAGE / _CURRENT, 1.0), "S": (_CURRENT / _VOLTAGE, 1.0),
    "F": (_CHARGE / _VOLTAGE, 1.0), "H": (_VOLTAGE * _T / _CURRENT, 1.0),
    "Wb": (_VOLTAGE * _T, 1.0), "T": (_VOLTAGE * _T / DimensionVector(length=2), 1.0),
}

# Units that accept an SI prefix. Prefixing a unit that is not here (e.g. "mmin", "kyear") is an error, not a guess.
_PREFIXABLE = {"m", "g", "s", "Hz", "K", "mol", "A", "cd", "N", "Pa", "bar", "J", "eV", "cal", "Wh", "W", "L", "C", "V",
               "ohm", "Ω", "S", "F", "H", "Wb", "T", "pc", "u", "Da", "rad"}
_PREFIXES: Dict[str, float] = {
    "Y": 1e24, "Z": 1e21, "E": 1e18, "P": 1e15, "T": 1e12, "G": 1e9, "M": 1e6, "k": 1e3, "h": 1e2, "da": 1e1,
    "d": 1e-1, "c": 1e-2, "m": 1e-3, "µ": 1e-6, "μ": 1e-6, "u": 1e-6, "n": 1e-9, "p": 1e-12, "f": 1e-15,
    "a": 1e-18, "z": 1e-21, "y": 1e-24,
}
# Absolute-temperature conversions (offset units cannot appear inside a compound expression).
_OFFSET_TO_KELVIN = {
    "K": lambda v: v, "kelvin": lambda v: v,
    "degC": lambda v: v + 273.15, "°C": lambda v: v + 273.15, "celsius": lambda v: v + 273.15,
    "degF": lambda v: (v - 32.0) * 5.0 / 9.0 + 273.15, "°F": lambda v: (v - 32.0) * 5.0 / 9.0 + 273.15,
}
_OFFSET_FROM_KELVIN = {
    "K": lambda k: k, "kelvin": lambda k: k,
    "degC": lambda k: k - 273.15, "°C": lambda k: k - 273.15, "celsius": lambda k: k - 273.15,
    "degF": lambda k: (k - 273.15) * 9.0 / 5.0 + 32.0, "°F": lambda k: (k - 273.15) * 9.0 / 5.0 + 32.0,
}

_TOKEN = re.compile(
    r"\s*(?:(?P<num>\d+\.?\d*(?:[eE][+-]?\d+)?|\.\d+(?:[eE][+-]?\d+)?)"
    r"|(?P<name>[A-Za-zµμ°%Ω_][A-Za-zµμ°%Ω_]*)"
    r"|(?P<pow>\*\*|\^)|(?P<op>[*/·])|(?P<lp>\()|(?P<rp>\))|(?P<sign>[+-]))")


class UnitDimensionalEngine:
    """
    UDE ensures mathematical equations and layer transfers obey the Buckingham Pi theorem.

    It parses real unit expressions: ``m/s``, ``1/year``, ``kg*m/s^2``, ``J/(kg*K)``, ``mW``, ``km/h``,
    ``Pa^(1/2)``. A name that is not in the registry raises :class:`UnknownUnitError`; it is never
    silently treated as dimensionless (which would let any mismatch pass the audit).
    """

    def __init__(self) -> None:
        self.registry = dict(CANONICAL_DIMENSIONS)           # legacy lowercase aliases
        self._cache: Dict[str, Tuple[DimensionVector, float]] = {}

    # ------------------------------------------------------------------ name resolution
    def _resolve_name(self, name: str, expr: str) -> Tuple[DimensionVector, float]:
        if name in SI_UNITS:
            return SI_UNITS[name]
        parses = set()
        for pre, factor in _PREFIXES.items():
            if name.startswith(pre) and len(name) > len(pre) and name[len(pre):] in _PREFIXABLE:
                dim, scale = SI_UNITS[name[len(pre):]]
                parses.add((dim, scale * factor, f"{pre}+{name[len(pre):]}"))
        if len({(d, round(s, 15)) for d, s, _ in parses}) > 1:
            raise UnknownUnitError(f"Ambiguous unit '{name}' in '{expr}': " + ", ".join(sorted(p[2] for p in parses)))
        if parses:
            dim, scale, _ = next(iter(parses))
            return dim, scale
        legacy = self.registry.get(name.lower())
        if legacy is not None:
            return legacy
        close = difflib.get_close_matches(name, list(SI_UNITS), n=3, cutoff=0.6)
        hint = f" Did you mean: {', '.join(close)}?" if close else ""
        raise UnknownUnitError(f"Unknown unit '{name}' in '{expr}'.{hint}")

    # ------------------------------------------------------------------ expression parser
    def _tokens(self, expr: str) -> List[Tuple[str, str]]:
        out: List[Tuple[str, str]] = []
        pos = 0
        s = expr.strip()
        while pos < len(s):
            m = _TOKEN.match(s, pos)
            if not m or m.end() == pos:
                raise UnitSyntaxError(f"Unexpected character {s[pos:pos + 1]!r} in unit '{expr}'")
            kind = m.lastgroup or ""
            out.append((kind, m.group(kind)))
            pos = m.end()
        return out

    def parse_unit(self, unit_str: str) -> Tuple[DimensionVector, float]:
        """Resolves a unit expression to its dimension vector and SI scale factor.

        Raises :class:`UnknownUnitError` for an unknown name and :class:`UnitSyntaxError` for a malformed
        expression. Temperature offsets (degC, degF) resolve as *intervals*; absolute values go through
        :meth:`convert`.
        """
        key = unit_str.strip()
        if key == "":
            raise UnitSyntaxError("Empty unit string")
        if key in self._cache:
            return self._cache[key]
        toks = self._tokens(key)
        pos = 0

        def peek() -> Tuple[str, str]:
            return toks[pos] if pos < len(toks) else ("end", "")

        def take() -> Tuple[str, str]:
            nonlocal pos
            t = peek()
            pos += 1
            return t

        def exponent() -> Fraction:
            kind, val = take()
            sign = 1
            if kind == "sign":
                sign = -1 if val == "-" else 1
                kind, val = take()
            if kind == "lp":                                    # (a/b)
                num = exponent_literal()
                if peek()[0] == "op" and peek()[1] == "/":
                    take()
                    den = exponent_literal()
                    num = num / den
                if take()[0] != "rp":
                    raise UnitSyntaxError(f"Unbalanced parentheses in exponent of '{key}'")
                return sign * num
            if kind != "num":
                raise UnitSyntaxError(f"Exponent must be a number in '{key}'")
            return sign * Fraction(val).limit_denominator(1000)

        def exponent_literal() -> Fraction:
            kind, val = take()
            sign = 1
            if kind == "sign":
                sign = -1 if val == "-" else 1
                kind, val = take()
            if kind != "num":
                raise UnitSyntaxError(f"Exponent must be a number in '{key}'")
            return sign * Fraction(val).limit_denominator(1000)

        def factor() -> Tuple[DimensionVector, float, str]:
            kind, val = take()
            if kind == "lp":
                d, s, _ = expr_()
                if take()[0] != "rp":
                    raise UnitSyntaxError(f"Unbalanced parentheses in unit '{key}'")
                res = (d, s, "group")
            elif kind == "num":
                res = (_ONE, float(val), "num")
            elif kind == "name":
                d, s = self._resolve_name(val, key)
                res = (d, s, "name")
            else:
                raise UnitSyntaxError(f"Unexpected '{val or kind}' in unit '{key}'")
            if peek()[0] == "pow":
                take()
                e = exponent()
                return res[0] ** e, res[1] ** float(e), res[2]
            return res

        def expr_() -> Tuple[DimensionVector, float, str]:
            d, s, last = factor()
            while True:
                kind, val = peek()
                if kind == "op":
                    take()
                    d2, s2, last = factor()
                    if val == "/":
                        d, s = d / d2, s / s2
                    else:
                        d, s = d * d2, s * s2
                elif kind in ("name", "lp"):                    # implicit product: "kg m s^-2"
                    d2, s2, last = factor()
                    d, s = d * d2, s * s2
                elif kind == "num":
                    raise UnitSyntaxError(
                        f"Missing operator before number {val!r} in unit '{key}' (write m^2, not m2; s^-1, not s-1)")
                else:
                    return d, s, last

        dim, scale, _ = expr_()
        if pos != len(toks):
            raise UnitSyntaxError(f"Unexpected trailing '{toks[pos][1]}' in unit '{key}'")
        self._cache[key] = (dim, scale)
        return dim, scale

    # ------------------------------------------------------------------ public API
    def dimension_of(self, unit_str: str) -> DimensionVector:
        """Dimension vector of a unit expression (raises on unknown units)."""
        return self.parse_unit(unit_str)[0]

    def is_known(self, unit_str: str) -> bool:
        """True if the unit expression parses and every name in it is registered."""
        try:
            self.parse_unit(unit_str)
            return True
        except ValueError:
            return False

    def describe(self, unit_str: str) -> str:
        """``'N' -> 'kg^1 m^1 s^-2 (x1)'``: dimension and SI scale in one line."""
        d, s = self.parse_unit(unit_str)
        return f"{d.label()} (x{s:g})"

    def convert(self, value: float, from_unit: str, to_unit: str) -> float:
        """Converts a value between dimensionally compatible units (absolute temperatures included)."""
        f, t = from_unit.strip(), to_unit.strip()
        if f in _OFFSET_TO_KELVIN and t in _OFFSET_FROM_KELVIN and (f != t):
            return float(_OFFSET_FROM_KELVIN[t](_OFFSET_TO_KELVIN[f](value)))
        dim_from, scale_from = self.parse_unit(from_unit)
        dim_to, scale_to = self.parse_unit(to_unit)

        if dim_from != dim_to:
            raise ValueError(
                f"Dimensional mismatch: cannot convert '{from_unit}' [{dim_from.label()}] to '{to_unit}' [{dim_to.label()}]"
            )
        return (value * scale_from) / scale_to

    def verify_compatibility(self, unit_a: str, unit_b: str) -> Tuple[bool, Optional[str]]:
        """Verifies that two units share identical physical dimensions.

        An unknown or malformed unit is reported as incompatible with the reason, never as dimensionless.
        """
        try:
            dim_a, _ = self.parse_unit(unit_a)
            dim_b, _ = self.parse_unit(unit_b)
        except ValueError as exc:
            return False, str(exc)
        if dim_a == dim_b:
            return True, None
        return False, f"Incompatible dimensions: '{unit_a}' has [{dim_a.label()}] vs '{unit_b}' has [{dim_b.label()}]"

    def check_sum(self, units: List[str]) -> Tuple[bool, Optional[str]]:
        """Dimensional homogeneity of an additive expression: every term must share one dimension."""
        if not units:
            return True, None
        ref = units[0]
        for u in units[1:]:
            ok, why = self.verify_compatibility(ref, u)
            if not ok:
                return False, why
        return True, None
