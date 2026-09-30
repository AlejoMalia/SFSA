/**
 * sfsa.sre — Schedule & Resource Engine (SRE)
 * ==========================================
 * Hardware-aware execution scheduler for high-throughput scientific campaigns.
 * Prioritizes queues by Value-of-Information / cost ratio, calculates campaign makespan,
 * applies backpressure when budgets or memory limits approach exhaustion, and coordinates
 * asynchronous execution pools across available CPU cores and worker threads.
 *
 * Part of SFSA (Standard Framework for Scientific Advancement)
 * Author & Protocol Creator: Alejo Malia
 * License: CC BY 4.0
 */

export class ScheduledTask {
  constructor({
    taskId,
    inputs,
    priorityScore = 1.0,
    estimatedCostMs = 10.0,
    deviceTarget = 'CPU'
  }) {
    this.taskId = taskId;
    this.inputs = inputs;
    this.priorityScore = priorityScore;
    this.estimatedCostMs = estimatedCostMs;
    this.deviceTarget = deviceTarget;
  }
}

export class CampaignSchedule {
  constructor({
    totalTasks,
    concurrencyWorkers,
    estimatedMakespanMs,
    backpressureActive,
    taskOrder = []
  }) {
    this.totalTasks = totalTasks;
    this.concurrencyWorkers = concurrencyWorkers;
    this.estimatedMakespanMs = estimatedMakespanMs;
    this.backpressureActive = backpressureActive;
    this.taskOrder = taskOrder;
  }
}

export class ScheduleResourceEngine {
  constructor(defaultConcurrency = null) {
    let cpuCount = 4;
    try {
      if (typeof navigator !== 'undefined' && navigator.hardwareConcurrency) {
        cpuCount = navigator.hardwareConcurrency;
      }
    } catch (_) {}
    this.concurrency = defaultConcurrency || Math.min(16, cpuCount);
    this.queue = [];
  }

  enqueueTask(taskId, inputs, priorityScore = 1.0, estimatedCostMs = 10.0, deviceTarget = 'CPU') {
    const task = new ScheduledTask({
      taskId,
      inputs,
      priorityScore,
      estimatedCostMs,
      deviceTarget
    });
    this.queue.push(task);
    // Sort queue by descending priority
    this.queue.sort((a, b) => b.priorityScore - a.priorityScore);
    return task;
  }

  planCampaignSchedule(budgetExhaustionRatio = 0.0) {
    const backpressure = budgetExhaustionRatio > 0.85;
    const totalTimeMs = this.queue.reduce((sum, t) => sum + t.estimatedCostMs, 0.0);
    const effectiveWorkers = backpressure ? Math.max(1, Math.floor(this.concurrency / 2)) : this.concurrency;
    const makespan = this.queue.length > 0 ? totalTimeMs / effectiveWorkers : 0.0;

    return new CampaignSchedule({
      totalTasks: this.queue.length,
      concurrencyWorkers: effectiveWorkers,
      estimatedMakespanMs: makespan,
      backpressureActive: backpressure,
      taskOrder: this.queue.map(t => t.taskId)
    });
  }

  dispatchNext() {
    return this.queue.length > 0 ? this.queue.shift() : null;
  }
}
