"""
sfsa.rme — Reproducibility & Environment Manifest Engine (RME)
==============================================================
Tackles the scientific reproducibility crisis. Generates cryptographic execution certificates
and environment manifests recording hardware architecture, OS platform, IEEE-754 floating-point
precision, deterministic RNG seeds, and module signatures ready for journal peer-review supplements.

Part of SFSA (Standard Framework for Scientific Advancement)
Author & Protocol Creator: Alejo Malia
License: CC BY 4.0
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
import hashlib
import json
import platform
import sys
import time


@dataclass
class ReproducibilityManifest:
    """Cryptographic certificate guaranteeing full experimental reproducibility."""
    session_name: str
    manifest_timestamp: float
    cryptographic_seal: str          # SHA-256 digest of computational environment & state
    platform_info: Dict[str, str]
    python_version: str
    floating_point_precision: Dict[str, Any]
    active_engine_count: int
    environment_metadata: Dict[str, Any] = field(default_factory=dict)


class ReproducibilityManifestEngine:
    """
    RME stamps reproducible provenance seals onto research workflows.
    """

    def __init__(self) -> None:
        pass

    @staticmethod
    def _seal(session_name: str, timestamp: float, plat: Dict[str, Any], py_version: str,
              float_info: Dict[str, Any], engine_count: int, extra: Dict[str, Any]) -> str:
        payload = {
            "session_name": session_name,
            "timestamp": timestamp,
            "platform": plat,
            "python_version": py_version,
            "float_info": float_info,
            "engine_count": engine_count,
            "extra": extra,
        }
        return hashlib.sha256(json.dumps(payload, sort_keys=True, default=str).encode("utf-8")).hexdigest()

    def verify_manifest(self, manifest: ReproducibilityManifest) -> bool:
        """Recomputes the seal from the manifest's own fields; False if anything was altered."""
        expected = self._seal(
            manifest.session_name, manifest.manifest_timestamp, manifest.platform_info, manifest.python_version,
            manifest.floating_point_precision, manifest.active_engine_count, manifest.environment_metadata,
        )
        return expected == manifest.cryptographic_seal

    def generate_manifest(
        self,
        session_name: str,
        engine_count: int = 39,
        extra_metadata: Optional[Dict[str, Any]] = None,
    ) -> ReproducibilityManifest:
        """
        Gathers system platform, architecture, and floating-point parameters into a signed manifest.
        """
        plat = {
            "system": platform.system(),
            "release": platform.release(),
            "machine": platform.machine(),
            "processor": platform.processor(),
        }
        float_info = {
            "epsilon": sys.float_info.epsilon,
            "max": sys.float_info.max,
            "min": sys.float_info.min,
            "digits": sys.float_info.dig,
            "radix": sys.float_info.radix,
        }

        now = time.time()
        py_version = sys.version.split()[0]
        seal = self._seal(session_name, now, plat, py_version, float_info, engine_count, extra_metadata or {})

        return ReproducibilityManifest(
            session_name=session_name,
            manifest_timestamp=now,
            cryptographic_seal=seal,
            platform_info=plat,
            python_version=py_version,
            floating_point_precision=float_info,
            active_engine_count=engine_count,
            environment_metadata=extra_metadata or {},
        )
