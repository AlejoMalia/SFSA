"""
sfsa.lke — Literature & Knowledge Engine (LKE)
=============================================
Manages a curated, typed registry of external scientific repositories, literature APIs, databases,
and reproducible code archives. Selects sources based on the active model's thematic profile (STE),
emitting actionable proposals (preprints, benchmark datasets, reference implementations, physical properties)
with evidence citations, without hallucinating mechanisms.

Part of SFSA (Standard Framework for Scientific Advancement)
Author & Protocol Creator: Alejo Malia
License: CC BY 4.0
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional


class SourceType(str, Enum):
    PREPRINT = "PREPRINT"                 # arXiv, bioRxiv, ChemRxiv
    INDEXED_LITERATURE = "INDEXED_LIT"   # OpenAlex, Semantic Scholar, PubMed, NASA ADS
    DATASET_PROPERTIES = "DATASET"       # NIST, PubChem, Materials Project, Zenodo
    CODE_METHODS = "CODE_METHODS"        # GitHub, Papers with Code, Software Heritage
    STANDARDS = "STANDARDS"              # IUPAC, CODATA, FAIR protocols


@dataclass
class ScientificSource:
    """Registered external repository or data source."""
    source_id: str
    name: str
    source_type: SourceType
    domain_tags: List[str]
    base_url: str
    has_api: bool
    is_open_access: bool
    signal_quality: str                  # 'PEER_REVIEW', 'CURATED_DATABASE', 'PREPRINT', 'COMMUNITY'


@dataclass
class EvidenceProposal:
    """An actionable external candidate recommended for model enrichment or validation."""
    title: str
    source_name: str
    source_type: SourceType
    url: str
    rationale: str
    confidence: float
    is_open_access: bool


# Curated catalog of primary scientific sources
DEFAULT_SOURCES: List[ScientificSource] = [
    # Preprints
    ScientificSource("arxiv", "arXiv", SourceType.PREPRINT, ["physics", "math", "astrophysics", "computer_science"], "https://arxiv.org", True, True, "PREPRINT"),
    ScientificSource("chemrxiv", "ChemRxiv", SourceType.PREPRINT, ["chemical_kinetics", "chemistry", "materials_science"], "https://chemrxiv.org", True, True, "PREPRINT"),
    ScientificSource("biorxiv", "bioRxiv", SourceType.PREPRINT, ["biology", "biophysics", "biochemistry"], "https://biorxiv.org", True, True, "PREPRINT"),
    # Literature
    ScientificSource("openalex", "OpenAlex", SourceType.INDEXED_LITERATURE, ["multidisciplinary"], "https://openalex.org", True, True, "CURATED_DATABASE"),
    ScientificSource("semantic_scholar", "Semantic Scholar", SourceType.INDEXED_LITERATURE, ["multidisciplinary", "computer_science"], "https://www.semanticscholar.org", True, True, "CURATED_DATABASE"),
    ScientificSource("nasa_ads", "NASA ADS", SourceType.INDEXED_LITERATURE, ["astrophysics_space", "planetary"], "https://ui.adsabs.harvard.edu", True, True, "CURATED_DATABASE"),
    ScientificSource("pubmed", "PubMed / Europe PMC", SourceType.INDEXED_LITERATURE, ["biology", "biochemistry", "medical"], "https://europepmc.org", True, True, "PEER_REVIEW"),
    # Data & Properties
    ScientificSource("nist", "NIST Chemistry WebBook", SourceType.DATASET_PROPERTIES, ["thermodynamics", "chemical_kinetics"], "https://webbook.nist.gov", True, True, "CURATED_DATABASE"),
    ScientificSource("materials_project", "Materials Project", SourceType.DATASET_PROPERTIES, ["materials_science", "crystallography"], "https://materialsproject.org", True, True, "CURATED_DATABASE"),
    ScientificSource("pubchem", "PubChem", SourceType.DATASET_PROPERTIES, ["chemistry", "chemical_kinetics"], "https://pubchem.ncbi.nlm.nih.gov", True, True, "CURATED_DATABASE"),
    ScientificSource("zenodo", "Zenodo", SourceType.DATASET_PROPERTIES, ["multidisciplinary", "experimental_validation"], "https://zenodo.org", True, True, "COMMUNITY"),
    # Code & Methods
    ScientificSource("papers_with_code", "Papers with Code", SourceType.CODE_METHODS, ["numerical_optimization", "machine_learning"], "https://paperswithcode.com", True, True, "COMMUNITY"),
]


class LiteratureKnowledgeEngine:
    """
    LKE connects internal model concepts with external scientific repositories.
    """

    def __init__(self, custom_sources: Optional[List[ScientificSource]] = None) -> None:
        self.sources: Dict[str, ScientificSource] = {s.source_id: s for s in (custom_sources or DEFAULT_SOURCES)}

    def propose_resources(
        self,
        primary_domains: List[str],
        limit: int = 5,
        prefer_open_access: bool = True,
        source_types: Optional[List[SourceType]] = None,
    ) -> List[EvidenceProposal]:
        """
        Proposes targeted external resources based on active domain tags.
        If source_types is given, only those source types are returned; when none of them match the
        domains, they are still returned with a low baseline score rather than an empty list.
        """
        matched: List[Tuple[ScientificSource, float]] = []

        for s in self.sources.values():
            if prefer_open_access and not s.is_open_access:
                continue
            if source_types and s.source_type not in source_types:
                continue

            score = 0.0
            if "multidisciplinary" in s.domain_tags:
                score += 0.5

            for d in primary_domains:
                if d in s.domain_tags:
                    score += 1.0

            if source_types and score == 0.0:
                score = 0.25
            if score > 0.0:
                matched.append((s, score))

        matched.sort(key=lambda item: item[1], reverse=True)

        proposals: List[EvidenceProposal] = []
        for s, score in matched[:limit]:
            rationale = f"Aligned with active domain focus ({', '.join(primary_domains)}). High quality signal: {s.signal_quality}"
            proposals.append(
                EvidenceProposal(
                    title=f"External {s.source_type.value}: {s.name}",
                    source_name=s.name,
                    source_type=s.source_type,
                    url=s.base_url,
                    rationale=rationale,
                    confidence=min(1.0, score / 2.0),
                    is_open_access=s.is_open_access,
                )
            )

        return proposals
