"""
sfsa.ste — Scientific Thematic Engine (STE)
==========================================
Analyzes the semantic and conceptual makeup of the user's scientific framework.
Inspects layers, variables, formulas, inventories, cache records, and documentation to build
a quantified thematic coverage map (%), identify methodological and disciplinary blind spots,
detect thematic bias, and project interdisciplinary connections without hallucinating physics.

Part of SFSA (Standard Framework for Scientific Advancement)
Author & Protocol Creator: Alejo Malia
License: CC BY 4.0
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Set, Tuple


# Standardized scientific domain keyword taxonomies
DOMAIN_TAXONOMY: Dict[str, List[str]] = {
    "chemical_kinetics": ["kinetic", "rate", "arrhenius", "reaction", "activation_energy", "catalysis", "stoichiometry", "half_life"],
    "thermodynamics": ["temp", "pressure", "enthalpy", "entropy", "gibbs", "isobaric", "adiabatic", "heat", "thermal", "joule"],
    "fluid_dynamics": ["reynolds", "viscosity", "navier", "mach", "flow", "density", "boundary_layer", "turbulent", "laminar"],
    "materials_science": ["stress", "strain", "crystal", "lattice", "young_modulus", "brittle", "ductile", "tensile", "aerogel"],
    "electromagnetism": ["charge", "voltage", "current", "magnetic", "electric", "dielectric", "flux", "field", "conductance"],
    "astrophysics_space": ["orbit", "albedo", "insolation", "gravity", "escape_velocity", "planetary", "atmospheric", "solar"],
    "numerical_optimization": ["gradient", "loss", "convergence", "pareto", "solver", "step_size", "hessian", "simplex", "tolerance"],
    "uncertainty_quantification": ["uncertainty", "confidence", "variance", "monte_carlo", "sobol", "std_dev", "error_bound"],
    "experimental_validation": ["experiment", "measured", "empirical", "lab_data", "sensor", "calibration", "benchmark"],
}


@dataclass
class ThematicReport:
    """Consolidated semantic and thematic diagnostic profile of the scientific model."""
    primary_themes: List[Tuple[str, float]]     # Themes >= 25%
    secondary_themes: List[Tuple[str, float]]   # Themes between 8% and 25%
    marginal_themes: List[Tuple[str, float]]    # Themes < 8%
    coverage_pct: Dict[str, float]              # Percentage allocation per theme
    thematic_gaps: List[str]                    # Flagged blind spots (e.g. missing UQ or validation)
    related_suggestions: List[str]              # Actionable interdisciplinary enhancements
    bias_warnings: List[str]                    # Potential over-specialization alerts
    confidence: float
    evidence: List[str]


class ScientificThematicEngine:
    """
    STE evaluates what a scientific framework is about and where its blind spots lie.
    Operates lazily and under demand without interfering with solver performance.
    """

    def __init__(self) -> None:
        self.taxonomy = dict(DOMAIN_TAXONOMY)

    def analyze_model(
        self,
        layer_names: List[str],
        variable_names: List[str],
        formula_texts: Optional[List[str]] = None,
        doc_texts: Optional[List[str]] = None,
    ) -> ThematicReport:
        """
        Extracts scientific concepts, matches against taxonomy, and computes weighted domain distribution.
        """
        all_tokens = [t.lower() for t in layer_names] + [t.lower() for t in variable_names]
        if formula_texts:
            for f in formula_texts:
                all_tokens.extend(f.lower().replace("(", " ").replace(")", " ").split())
        if doc_texts:
            for d in doc_texts:
                all_tokens.extend(d.lower().split())

        domain_scores: Dict[str, float] = {dom: 0.0 for dom in self.taxonomy}
        matched_evidence: List[str] = []

        for token in all_tokens:
            for dom, kws in self.taxonomy.items():
                for kw in kws:
                    if kw in token:
                        domain_scores[dom] += 1.0
                        if len(matched_evidence) < 15:
                            matched_evidence.append(f"Token '{token}' matched keyword '{kw}' -> {dom}")
                        break

        total_matches = sum(domain_scores.values())
        if total_matches == 0.0:
            total_matches = 1.0

        percentages = {dom: (score / total_matches) * 100.0 for dom, score in domain_scores.items()}
        sorted_themes = sorted(percentages.items(), key=lambda item: item[1], reverse=True)

        primary = [(k, v) for k, v in sorted_themes if v >= 25.0]
        secondary = [(k, v) for k, v in sorted_themes if 8.0 <= v < 25.0]
        marginal = [(k, v) for k, v in sorted_themes if 0.0 < v < 8.0]

        # Identify gaps and biases
        gaps: List[str] = []
        if percentages.get("uncertainty_quantification", 0.0) < 5.0:
            gaps.append("Uncertainty Quantification (UQ): Model lacks explicit variance or error bounds.")
        if percentages.get("experimental_validation", 0.0) < 5.0:
            gaps.append("Experimental Validation: No empirical lab data or sensor calibration detected.")

        bias_warnings: List[str] = []
        if primary and primary[0][1] > 65.0:
            bias_warnings.append(
                f"Severe thematic concentration: {primary[0][0]} accounts for {primary[0][1]:.1f}% of detected framework concepts."
            )

        suggestions: List[str] = []
        if any(t[0] == "chemical_kinetics" for t in primary) and not any(t[0] == "fluid_dynamics" for t in primary + secondary):
            suggestions.append("Consider coupling chemical kinetics with mass transport or fluid dynamics to capture diffusion limits.")
        if any(t[0] == "thermodynamics" for t in primary) and not any(t[0] == "materials_science" for t in primary + secondary):
            suggestions.append("Consider verifying phase stability constraints against material degradation thresholds.")

        return ThematicReport(
            primary_themes=primary,
            secondary_themes=secondary,
            marginal_themes=marginal,
            coverage_pct={k: round(v, 2) for k, v in percentages.items() if v > 0},
            thematic_gaps=gaps,
            related_suggestions=suggestions,
            bias_warnings=bias_warnings,
            confidence=0.88,
            evidence=matched_evidence[:10],
        )
