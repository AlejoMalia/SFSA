/**
 * sfsa.rfe — Result Forgetting Engine (RFE)
 * ========================================
 * Cache lifecycle manager and cost-weighted eviction policy.
 *
 * Part of SFSA (Standard Framework for Scientific Advancement)
 * Author & Protocol Creator: Alejo Malia
 * License: CC BY 4.0
 */

export class ResultForgettingEngine {
  constructor(maxEntries = 10000, maxAgeSeconds = 86400) {
    this.maxEntries = maxEntries;
    this.maxAgeSeconds = maxAgeSeconds;
    this.entryMetadata = new Map();
  }

  trackEntry(key, costMs = 1.0) {
    this.entryMetadata.set(key, {
      createdAt: Date.now(),
      lastAccessed: Date.now(),
      accessCount: 1,
      costMs
    });
  }

  recordAccess(key) {
    const meta = this.entryMetadata.get(key);
    if (meta) {
      meta.lastAccessed = Date.now();
      meta.accessCount += 1;
    }
  }

  assessRetention(key) {
    const meta = this.entryMetadata.get(key);
    if (!meta) return null;

    const idle = (Date.now() - meta.lastAccessed) / 1000.0;
    const score = (meta.accessCount * 2.0 + Math.log1p(meta.costMs)) / (1.0 + idle / 3600.0);
    return {
      key,
      reuseCount: meta.accessCount,
      recomputeCostEstimate: meta.costMs,
      retentionScore: score,
      evictRecommended: idle > this.maxAgeSeconds || (meta.accessCount <= 1 && idle > 300 && meta.costMs < 5)
    };
  }

  identifyEvictionCandidates(countToPrune) {
    const scored = [];
    for (const k of this.entryMetadata.keys()) {
      const sc = this.assessRetention(k);
      if (sc) scored.push(sc);
    }
    scored.sort((a, b) => a.retentionScore - b.retentionScore);
    return scored.slice(0, countToPrune).map((x) => x.key);
  }
}
