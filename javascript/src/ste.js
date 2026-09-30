/**
 * sfsa.ste — Scientific Thematic Engine (STE)
 * ==========================================
 * Analyzes semantic model makeup and generates domain coverage percentages without hallucinating physics.
 *
 * Part of SFSA (Standard Framework for Scientific Advancement)
 * Author & Protocol Creator: Alejo Malia
 * License: CC BY 4.0
 */

export const DOMAIN_TAXONOMY = {
  chemical_kinetics: ["kinetic", "rate", "arrhenius", "reaction", "activation_energy", "catalysis", "stoichiometry"],
  thermodynamics: ["temp", "pressure", "enthalpy", "entropy", "gibbs", "isobaric", "adiabatic", "heat", "thermal"],
  fluid_dynamics: ["reynolds", "viscosity", "navier", "mach", "flow", "density", "boundary_layer", "laminar"],
  materials_science: ["stress", "strain", "crystal", "lattice", "young_modulus", "brittle", "ductile", "aerogel"],
  electromagnetism: ["charge", "voltage", "current", "magnetic", "electric", "flux", "field"],
  astrophysics_space: ["orbit", "albedo", "insolation", "gravity", "escape_velocity", "planetary", "atmospheric"],
  numerical_optimization: ["gradient", "loss", "convergence", "pareto", "solver", "step_size", "hessian"],
  uncertainty_quantification: ["uncertainty", "confidence", "variance", "monte_carlo", "error_bound"],
  experimental_validation: ["experiment", "measured", "empirical", "lab_data", "sensor", "calibration"]
};

export class ScientificThematicEngine {
  constructor() {
    this.taxonomy = DOMAIN_TAXONOMY;
  }

  analyzeModel({ layerNames = [], variableNames = [], formulaTexts = [] }) {
    const tokens = [
      ...layerNames.map(s => s.toLowerCase()),
      ...variableNames.map(s => s.toLowerCase()),
      ...formulaTexts.flatMap(f => f.toLowerCase().split(/[\s()]+/))
    ];

    const scores = {};
    for (const dom of Object.keys(this.taxonomy)) scores[dom] = 0;

    for (const token of tokens) {
      for (const [dom, kws] of Object.entries(this.taxonomy)) {
        for (const kw of kws) {
          if (token.includes(kw)) {
            scores[dom] += 1;
            break;
          }
        }
      }
    }

    const total = Object.values(scores).reduce((a, b) => a + b, 0) || 1;
    const percentages = {};
    for (const [dom, score] of Object.entries(scores)) {
      percentages[dom] = Number(((score / total) * 100).toFixed(2));
    }

    const sortedThemes = Object.entries(percentages).sort((a, b) => b[1] - a[1]);
    const primary = sortedThemes.filter(t => t[1] >= 25.0);
    const secondary = sortedThemes.filter(t => t[1] >= 8.0 && t[1] < 25.0);

    const marginal = sortedThemes.filter(t => t[1] > 0.0 && t[1] < 8.0);
    const gaps = [];
    if ((percentages.uncertainty_quantification || 0) < 5.0) {
      gaps.push("Uncertainty Quantification (UQ): Model lacks explicit variance or error bounds.");
    }
    if ((percentages.experimental_validation || 0) < 5.0) {
      gaps.push("Experimental Validation: No empirical lab data or sensor calibration detected.");
    }

    const biasWarnings = [];
    if (primary.length > 0 && primary[0][1] > 65.0) {
      biasWarnings.push(
        `Severe thematic concentration: ${primary[0][0]} accounts for ${primary[0][1].toFixed(1)}% of detected framework concepts.`
      );
    }

    const suggestions = [];
    const has = (list, name) => list.some(t => t[0] === name);
    if (has(primary, 'chemical_kinetics') && !has([...primary, ...secondary], 'fluid_dynamics')) {
      suggestions.push("Consider coupling chemical kinetics with mass transport or fluid dynamics to capture diffusion limits.");
    }
    if (has(primary, 'thermodynamics') && !has([...primary, ...secondary], 'materials_science')) {
      suggestions.push("Consider verifying phase stability constraints against material degradation thresholds.");
    }

    return {
      primaryThemes: primary,
      secondaryThemes: secondary,
      marginalThemes: marginal,
      relatedSuggestions: suggestions,
      biasWarnings,
      coveragePct: percentages,
      thematicGaps: gaps,
      confidence: 0.88
    };
  }
}
