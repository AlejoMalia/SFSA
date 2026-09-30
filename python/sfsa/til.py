"""
sfsa.til — Tag Index & Linking Engine (TIL)
==========================================
Constructs, maintains, and serves an operational living taxonomy of the scientific project or session.
Extracts concepts from code, layers, formulas, and results into typed, weighted, and aliased Tags
(domain, method, variable, regime, validation, data, software). Emits search profiles, tag diffs,
and maps for external engines (LKE, STE) and AI agents.

Part of SFSA (Standard Framework for Scientific Advancement)
Author & Protocol Creator: Alejo Malia
License: CC BY 4.0
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Tuple
import json
import time


class TagType(str, Enum):
    DOMAIN = "domain"           # Principal scientific discipline / scope (e.g., thermodynamics)
    METHOD = "method"           # Computational technique (e.g., adaptive-sampling, multi-fidelity)
    VARIABLE = "variable"       # Central state parameters (e.g., temperature, activation-energy)
    REGIME = "regime"           # Operating envelope / conditions (e.g., dilute-limit, laminar)
    VALIDATION = "validation"   # Verification / benchmark practice (e.g., uncertainty-quantification)
    DATA = "data"               # Data resource or format (e.g., nist-properties, time-series)
    SOFTWARE = "software"       # Computational libraries (e.g., numpy, scipy)


@dataclass
class Tag:
    """A weighted, typed semantic concept grounded in project evidence."""
    id: str
    label: str
    type: TagType
    weight: float
    confidence: float
    status: str = "active"                                  # 'active', 'pinned', 'deprecated', 'candidate'
    evidence: List[Dict[str, Any]] = field(default_factory=list)
    synonyms: List[str] = field(default_factory=list)
    related_tags: List[str] = field(default_factory=list)
    external_aliases: Dict[str, List[str]] = field(default_factory=dict)
    first_seen: float = field(default_factory=time.time)
    last_updated: float = field(default_factory=time.time)


@dataclass
class SearchProfile:
    """Search query profile synthesized from current tag distribution and detected gaps."""
    must_include: List[str]
    should_include: List[str]
    useful_for_gaps: List[str]
    primary_domain_aliases: Dict[str, List[str]]


class TagIndexLinkingEngine:
    """
    TIL Engine maintains the living operational taxonomy of the scientific workspace.
    """

    def __init__(self) -> None:
        self.tags: Dict[str, Tag] = {}

    def add_or_update_tag(
        self,
        tag_id: str,
        label: str,
        tag_type: TagType,
        weight_increment: float = 0.1,
        source: str = "internal",
        confidence: float = 0.8,
        aliases: Optional[Dict[str, List[str]]] = None,
    ) -> Tag:
        """Adds a concept tag or updates weight with new supporting evidence."""
        if tag_id in self.tags:
            tag = self.tags[tag_id]
            if tag.status != "pinned":
                tag.weight += weight_increment
            tag.last_updated = time.time()
            tag.evidence.append({"source": source, "timestamp": time.time(), "strength": confidence})
            if aliases:
                for k, v in aliases.items():
                    tag.external_aliases.setdefault(k, []).extend(v)
            return tag

        tag = Tag(
            id=tag_id,
            label=label,
            type=tag_type,
            weight=weight_increment,
            confidence=confidence,
            status="active",
            evidence=[{"source": source, "timestamp": time.time(), "strength": confidence}],
            external_aliases=aliases or {},
        )
        self.tags[tag_id] = tag
        return tag

    def pin_tag(self, tag_id: str) -> bool:
        """Pins a tag to ensure its significance is preserved."""
        if tag_id in self.tags:
            self.tags[tag_id].status = "pinned"
            return True
        return False

    def unpin_tag(self, tag_id: str) -> bool:
        """Removes the pinned status of a tag."""
        if tag_id in self.tags:
            self.tags[tag_id].status = "active"
            return True
        return False

    def reject_tag(self, tag_id: str) -> bool:
        """Deprecates/rejects an invalid tag."""
        if tag_id in self.tags:
            self.tags[tag_id].status = "deprecated"
            return True
        return False

    def merge_tags(self, target_tag_id: str, source_tag_id: str) -> Optional[Tag]:
        """Merges a duplicate/synonym tag into a canonical target tag."""
        if target_tag_id not in self.tags or source_tag_id not in self.tags:
            return None
        target = self.tags[target_tag_id]
        source = self.tags.pop(source_tag_id)
        target.weight += source.weight
        target.synonyms.append(source.label)
        target.evidence.extend(source.evidence)
        for k, v in source.external_aliases.items():
            target.external_aliases.setdefault(k, []).extend(v)
        return target

    def get_primary_tags(self, top_k: int = 5) -> List[Tag]:
        """Returns the highest-weighted active tags."""
        active = [t for t in self.tags.values() if t.status in ("active", "pinned")]
        active.sort(key=lambda t: t.weight, reverse=True)
        return active[:top_k]

    def make_search_profile(self, intent: str = "general") -> SearchProfile:
        """
        Synthesizes a structured search profile for external queries (e.g. LKE).
        """
        primary = self.get_primary_tags(top_k=4)
        must_inc = [t.label for t in primary if t.type == TagType.DOMAIN]
        should_inc = [t.label for t in primary if t.type != TagType.DOMAIN]
        gaps = [t.label for t in self.tags.values() if t.type == TagType.VALIDATION]

        aliases: Dict[str, List[str]] = {}
        for t in primary:
            for k, v in t.external_aliases.items():
                aliases.setdefault(k, []).extend(v)

        return SearchProfile(
            must_include=must_inc,
            should_include=should_inc,
            useful_for_gaps=gaps,
            primary_domain_aliases=aliases,
        )

    def export_tag_library(self) -> Dict[str, Any]:
        """Exports the living taxonomy as a dictionary (for tags.json persistence)."""
        return {
            "version": "0.2.0",
            "timestamp": time.time(),
            "total_tags": len(self.tags),
            "tags": {
                k: {
                    "id": t.id,
                    "label": t.label,
                    "type": t.type.value,
                    "weight": round(t.weight, 4),
                    "status": t.status,
                    "synonyms": t.synonyms,
                    "external_aliases": t.external_aliases,
                }
                for k, t in self.tags.items()
            },
        }
