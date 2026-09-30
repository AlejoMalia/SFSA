/**
 * sfsa.lse — Landscape Structure Engine (LSE)
 * ==========================================
 * Constructs coarse-grained topological contours of response surfaces.
 *
 * Part of SFSA (Standard Framework for Scientific Advancement)
 * Author & Protocol Creator: Alejo Malia
 * License: CC BY 4.0
 */

export const LandscapeTopology = {
  FLAT_PLATEAU: 'FLAT_PLATEAU',
  SMOOTH_GRADIENT: 'SMOOTH_GRADIENT',
  STEEP_VALLEY: 'STEEP_VALLEY',
  DISCONTINUITY: 'DISCONTINUITY'
};

export class LandscapeStructureEngine {
  constructor(probeCountPerDim = 3) {
    this.probeCount = probeCountPerDim;
    this.mappedFeatures = [];
  }

  probeRegion(bounds, fastSurrogateOrFn) {
    const centroid = {};
    for (const [k, [low, high]] of Object.entries(bounds)) {
      centroid[k] = (low + high) / 2.0;
    }
    const cVal = fastSurrogateOrFn(centroid);

    const deltas = [];
    for (const [k, [low, high]] of Object.entries(bounds)) {
      const span = Math.max(high - low, 1e-6);
      const pPlus = { ...centroid, [k]: centroid[k] + span * 0.25 };
      const pMinus = { ...centroid, [k]: centroid[k] - span * 0.25 };
      const diff = Math.abs(fastSurrogateOrFn(pPlus) - cVal) + Math.abs(fastSurrogateOrFn(pMinus) - cVal);
      deltas.push(diff / (Math.abs(cVal) + 1e-6));
    }

    const maxDelta = deltas.length > 0 ? Math.max(...deltas) : 0.0;
    let topo = LandscapeTopology.SMOOTH_GRADIENT;
    let density = 'STANDARD';

    if (maxDelta < 0.02) {
      topo = LandscapeTopology.FLAT_PLATEAU;
      density = 'MINIMAL';
    } else if (maxDelta > 0.8) {
      topo = LandscapeTopology.DISCONTINUITY;
      density = 'DENSE';
    }

    const feat = {
      regionId: `reg_${this.mappedFeatures.length + 1}`,
      centroid,
      topology: topo,
      recommendedSamplingDensity: density
    };
    this.mappedFeatures.push(feat);
    return feat;
  }
}
