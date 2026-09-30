/**
 * sfsa.pke — Partial Knowledge Engine (PKE)
 * ========================================
 * Extracts and caches intermediate computation states from ongoing or interrupted solves.
 *
 * Part of SFSA (Standard Framework for Scientific Advancement)
 * Author & Protocol Creator: Alejo Malia
 * License: CC BY 4.0
 */

export class PartialKnowledgeEngine {
  constructor() {
    this.store = new Map();
  }

  capture({ taskId, iteration, estimate, lowerBound = null, upperBound = null, residual = null, metadata = {} }) {
    const pk = {
      knowledgeId: `pk_${taskId}_${iteration}_${Date.now()}`,
      taskId,
      iterationReached: iteration,
      latestEstimate: estimate,
      lowerBound,
      upperBound,
      residual,
      metadata,
      timestamp: Date.now()
    };
    if (!this.store.has(taskId)) {
      this.store.set(taskId, []);
    }
    this.store.get(taskId).push(pk);
    return pk;
  }

  getLatest(taskId) {
    const list = this.store.get(taskId);
    return list && list.length > 0 ? list[list.length - 1] : null;
  }

  getTightestBounds(taskId) {
    const list = this.store.get(taskId);
    if (!list || list.length === 0) return [null, null];
    const lowers = list.map(r => r.lowerBound).filter(v => v !== null);
    const uppers = list.map(r => r.upperBound).filter(v => v !== null);
    const bestLower = lowers.length > 0 ? Math.max(...lowers) : null;
    const bestUpper = uppers.length > 0 ? Math.min(...uppers) : null;
    return [bestLower, bestUpper];
  }
}
