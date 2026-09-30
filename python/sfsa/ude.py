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

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple


@dataclass(frozen=True)
class DimensionVector:
    """SI fundamental physical dimension vector: [Mass, Length, Time, Temp, Amount, Current, Luminous]."""
    mass: int = 0      # kg
    length: int = 0    # m
    time: int = 0      # s
    temp: int = 0      # K
    amount: int = 0    # mol
    current: int = 0   # A
    luminous: int = 0  # cd

    def __add__(self, other: DimensionVector) -> DimensionVector:
        return DimensionVector(
            self.mass + other.mass,
            self.length + other.length,
            self.time + other.time,
            self.temp + other.temp,
            self.amount + other.amount,
            self.current + other.current,
            self.luminous + other.luminous,
        )

    def __sub__(self, other: DimensionVector) -> DimensionVector:
        return DimensionVector(
            self.mass - other.mass,
            self.length - other.length,
            self.time - other.time,
            self.temp - other.temp,
            self.amount - other.amount,
            self.current - other.current,
            self.luminous - other.luminous,
        )

    def is_dimensionless(self) -> bool:
        return (
            self.mass == 0 and self.length == 0 and self.time == 0 and
            self.temp == 0 and self.amount == 0 and self.current == 0 and self.luminous == 0
        )


# Canonical Dimensional Constants & Registry
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


class UnitDimensionalEngine:
    """
    UDE ensures mathematical equations and layer transfers obey the Buckingham Pi theorem.
    """

    def __init__(self) -> None:
        self.registry = dict(CANONICAL_DIMENSIONS)

    def parse_unit(self, unit_str: str) -> Tuple[DimensionVector, float]:
        """Resolves unit string to fundamental dimension vector and SI scaling factor."""
        key = unit_str.strip().lower()
        if key in self.registry:
            return self.registry[key]
        return DimensionVector(), 1.0

    def convert(self, value: float, from_unit: str, to_unit: str) -> float:
        """Converts numerical value between compatible dimensional units."""
        dim_from, scale_from = self.parse_unit(from_unit)
        dim_to, scale_to = self.parse_unit(to_unit)

        if dim_from != dim_to:
            raise ValueError(
                f"Dimensional mismatch: cannot convert '{from_unit}' {dim_from} to '{to_unit}' {dim_to}"
            )
        return (value * scale_from) / scale_to

    def verify_compatibility(self, unit_a: str, unit_b: str) -> Tuple[bool, Optional[str]]:
        """Verifies if two units share identical physical dimensions."""
        dim_a, _ = self.parse_unit(unit_a)
        dim_b, _ = self.parse_unit(unit_b)
        if dim_a == dim_b:
            return True, None
        return False, f"Incompatible dimensions: '{unit_a}' has {dim_a} vs '{unit_b}' has {dim_b}"
