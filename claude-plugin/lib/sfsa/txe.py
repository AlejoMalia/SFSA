"""
sfsa.txe — Transfer & Cross-Session Experience Engine (TXE)
==========================================================
Bridges computational memory across sessions, projects, and scientific campaigns.
Transfers inferred constraints (CAE), response surface surrogates (SME), active subspaces (SRA),
and domain tags (TIL) from completed sessions to warm-start new related frameworks,
preventing the waste of relearning the same scientific priors from scratch.

Part of SFSA (Standard Framework for Scientific Advancement)
Author & Protocol Creator: Alejo Malia
License: CC BY 4.0
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple
import json
import time


@dataclass
class TransferredPrior:
    """A scientific prior extracted from a previous session and ready for transfer."""
    source_session_name: str
    prior_type: str                   # 'SURROGATE', 'CONSTRAINT', 'ACTIVE_SUBSPACE', 'TAG_PROFILE'
    domain: str
    payload: Dict[str, Any]
    confidence: float
    timestamp: float = field(default_factory=time.time)


@dataclass
class ExperienceSnapshot:
    """Portable cross-session experience capsule."""
    framework_name: str
    domain_tags: List[str]
    priors: List[TransferredPrior]
    metadata: Dict[str, Any] = field(default_factory=dict)


class TransferExperienceEngine:
    """
    TXE manages medium-term scientific memory across sessions and projects.
    """

    def __init__(self) -> None:
        self.repository: List[ExperienceSnapshot] = []

    def capture_session_experience(self, session: Any) -> ExperienceSnapshot:
        """
        Extracts reusable priors (surrogates, constraints, active dimensions) from an active session.
        """
        priors: List[TransferredPrior] = []

        # 1. Capture Inferred Constraints from CAE
        if hasattr(session, "cae"):
            for c in getattr(session.cae, "inferred_constraints", []):
                priors.append(TransferredPrior(
                    source_session_name=session.name,
                    prior_type="CONSTRAINT",
                    domain="general",
                    payload={"param": c.parameter_name, "op": c.condition_op, "threshold": c.threshold_value},
                    confidence=c.confidence,
                ))

        # 2. Capture Surrogates from SME
        if hasattr(session, "sme"):
            for mid, surr in getattr(session.sme, "surrogates", {}).items():
                priors.append(TransferredPrior(
                    source_session_name=session.name,
                    prior_type="SURROGATE",
                    domain="response_surface",
                    payload={"model_id": mid, "features": surr.feature_names, "points_count": len(surr.sample_points)},
                    confidence=0.9,
                ))

        # 3. Capture Domain Tags from TIL
        tags: List[str] = []
        if hasattr(session, "til"):
            tags = [t.label for t in session.til.get_primary_tags()]

        snapshot = ExperienceSnapshot(
            framework_name=session.name,
            domain_tags=tags,
            priors=priors,
            metadata={"active_engines": getattr(session, "name", "sfsa_session")},
        )
        self.repository.append(snapshot)
        return snapshot

    @staticmethod
    def _transferred_rule(inp: Dict[str, Any], p: Dict[str, Any], src: str) -> Any:
        """Valid unless the parameter is present and inside the blocked region of the transferred cut."""
        val = inp.get(p["param"])
        if not isinstance(val, (int, float)) or isinstance(val, bool):
            return True, ""
        blocked = {
            ">=": val >= p["threshold"], "<=": val <= p["threshold"],
            "<": val >= p["threshold"], ">": val <= p["threshold"],  # legacy snapshots
        }.get(p["op"], False)
        return (not blocked), f"Transferred constraint from {src}: {p['param']} {p['op']} {p['threshold']}"

    def warm_start_session(
        self,
        target_session: Any,
        domain_keywords: List[str],
        min_confidence: float = 0.5,
    ) -> int:
        """
        Transfers compatible priors from the repository into target_session.
        Returns count of transferred priors.
        """
        applied_count = 0
        keywords_lower = [k.lower() for k in domain_keywords]

        for snapshot in self.repository:
            # Check domain similarity
            match = any(k in [t.lower() for t in snapshot.domain_tags] for k in keywords_lower) or not keywords_lower
            if not match:
                continue

            for prior in snapshot.priors:
                if prior.confidence < min_confidence:
                    continue

                if prior.prior_type == "CONSTRAINT" and hasattr(target_session, "cae"):
                    p = prior.payload
                    target_session.cae.add_explicit_constraint(
                        lambda inp, p=p, src=prior.source_session_name: self._transferred_rule(inp, p, src)
                    )
                    applied_count += 1

        return applied_count
