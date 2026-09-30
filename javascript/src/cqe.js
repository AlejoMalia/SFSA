/**
 * sfsa.cqe — Query Compression Engine (CQE)
 * ========================================
 * Batches, clusters, and compresses large streams of similar queries into representative centroids.
 *
 * Part of SFSA (Standard Framework for Scientific Advancement)
 * Author & Protocol Creator: Alejo Malia
 * License: CC BY 4.0
 */

export class QueryCompressionEngine {
  constructor(clusteringRadius = 0.05) {
    this.clusteringRadius = clusteringRadius;
  }

  _dist(q1, q2) {
    const keys = Object.keys(q1).filter(k => k in q2);
    if (keys.length === 0) return 1.0;
    const sq = keys.reduce((sum, k) => sum + (q1[k] - q2[k]) ** 2, 0);
    return Math.sqrt(sq / keys.length);
  }

  compressAndSolve(queriesOrOptions, heavySolver = null) {
    let queries = queriesOrOptions;
    let solver = heavySolver;
    if (queriesOrOptions && !Array.isArray(queriesOrOptions) && queriesOrOptions.queries) {
      queries = queriesOrOptions.queries;
      solver = queriesOrOptions.heavySolver;
    }

    if (!queries || queries.length === 0) {
      return {
        originalQueryCount: 0,
        representativeCount: 0,
        compressionRatio: 1.0,
        reconstructedOutputs: [],
        computeReductionPct: 0.0
      };
    }

    const representatives = [];
    queries.forEach((q, idx) => {
      let matched = false;
      for (const rep of representatives) {
        if (this._dist(q, rep.centroidInputs) <= this.clusteringRadius) {
          rep.clusterMemberIndices.push(idx);
          matched = true;
          break;
        }
      }
      if (!matched) {
        representatives.push({
          queryId: `rep_${representatives.length}`,
          centroidInputs: q,
          computedOutput: null,
          clusterMemberIndices: [idx]
        });
      }
    });

    for (const rep of representatives) {
      rep.computedOutput = solver(rep.centroidInputs);
    }

    const reconstructed = new Array(queries.length).fill(0.0);
    for (const rep of representatives) {
      for (const idx of rep.clusterMemberIndices) {
        reconstructed[idx] = rep.computedOutput;
      }
    }

    const compRatio = representatives.length / queries.length;
    return {
      originalQueryCount: queries.length,
      representativeCount: representatives.length,
      compressionRatio: compRatio,
      reconstructedOutputs: reconstructed,
      computeReductionPct: (1.0 - compRatio) * 100.0
    };
  }
}
