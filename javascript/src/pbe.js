/**
 * sfsa.pbe — Parallel Batch & Dispatch Engine (PBE)
 * ================================================
 * Concurrent scientific workload dispatcher. Distributes heavy query batches, centroid evaluations (CQE),
 * and adaptive sampling candidates (ASG) across parallel asynchronous workers.
 *
 * Part of SFSA (Standard Framework for Scientific Advancement)
 * Author & Protocol Creator: Alejo Malia
 * License: CC BY 4.0
 */

export class ParallelBatchEngine {
  constructor(concurrency = 4) {
    this.concurrency = concurrency;
  }

  async mapConcurrent(items, workerFn, concurrency = null) {
    const limit = concurrency || this.concurrency;
    const t0 = Date.now();
    const results = new Array(items.length);
    let successes = 0;
    let failures = 0;

    let currentIndex = 0;
    const workers = [];

    const worker = async () => {
      while (currentIndex < items.length) {
        const idx = currentIndex++;
        try {
          results[idx] = await workerFn(items[idx]);
          successes += 1;
        } catch (err) {
          results[idx] = { error: String(err) };
          failures += 1;
        }
      }
    };

    const activeWorkersCount = Math.min(limit, Math.max(1, items.length));
    for (let i = 0; i < activeWorkersCount; i++) {
      workers.push(worker());
    }

    await Promise.all(workers);
    const wallClockMs = Date.now() - t0;

    return {
      totalItems: items.length,
      successfulItems: successes,
      failedItems: failures,
      concurrencyLevel: activeWorkersCount,
      wallClockMs,
      results
    };
  }
}
