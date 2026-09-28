/**
 * sfsa.triada — TRIADA 3-Stage Scientific Method Engine
 * ====================================================
 * JavaScript implementation of the TRIADA Protocol (Alejo Malia):
 * T1: Strict In-Situ Inventory & Boundary Verification
 * T2: Exact Analytical & Stoichiometric Solvers
 * T3: Bounded Projection & Global Invariant Verification
 *
 * Part of SFSA (Standard Framework for Scientific Advancement)
 * Author & Protocol Creator: Alejo Malia
 * License: CC BY 4.0
 */

import { MATEEngine, MATEStatus } from './mate.js';

export const TriadaStage = Object.freeze({
  T1_INVENTORY: "T1_INVENTORY",
  T2_ANALYTICAL_SOLVER: "T2_ANALYTICAL_SOLVER",
  T3_PROJECTION_VERIFICATION: "T3_PROJECTION_VERIFICATION",
});

export class TriadaStepOutcome {
  constructor({ stage, passed, data, elapsedMs, notes = [] }) {
    this.stage = stage;
    this.passed = passed;
    this.data = data;
    this.elapsedMs = elapsedMs;
    this.notes = notes;
  }
}

export class TriadaExecutionReport {
  constructor({
    success,
    taskName,
    finalOutput,
    failedAtStage = null,
    totalElapsedMs = 0.0,
    mateStatus = MATEStatus.R1_EXACT,
    t1Outcome = null,
    t2Outcome = null,
    t3Outcome = null,
    diagnostics = [],
  }) {
    this.success = success;
    this.taskName = taskName;
    this.finalOutput = finalOutput;
    this.failedAtStage = failedAtStage;
    this.totalElapsedMs = totalElapsedMs;
    this.mateStatus = mateStatus;
    this.t1Outcome = t1Outcome;
    this.t2Outcome = t2Outcome;
    this.t3Outcome = t3Outcome;
    this.diagnostics = diagnostics;
  }
}

export class TriadaEngine {
  constructor({ mateEngine = null } = {}) {
    this.mate = mateEngine || new MATEEngine();
  }

  runPipeline({
    taskName,
    inventoryInput,
    t1InventoryValidator,
    t2AnalyticalSolver,
    t3ProjectionVerifier,
  }) {
    const start = performance.now();
    const diagnostics = [];

    // ========================================================
    // STAGE T1: In-Situ Inventory Check
    // ========================================================
    const t1Start = performance.now();
    const [t1Valid, t1Reasons] = t1InventoryValidator(inventoryInput);
    const t1Elapsed = performance.now() - t1Start;

    const t1Outcome = new TriadaStepOutcome({
      stage: TriadaStage.T1_INVENTORY,
      passed: t1Valid,
      data: inventoryInput,
      elapsedMs: t1Elapsed,
      notes: t1Reasons,
    });

    if (!t1Valid) {
      diagnostics.push(...t1Reasons.map((r) => `T1_FAIL: ${r}`));
      return new TriadaExecutionReport({
        success: false,
        taskName,
        finalOutput: null,
        failedAtStage: TriadaStage.T1_INVENTORY,
        totalElapsedMs: performance.now() - start,
        mateStatus: MATEStatus.R3_INFEASIBLE,
        t1Outcome,
        diagnostics,
      });
    }

    // ========================================================
    // STAGE T2: Analytical & Stoichiometric Solver
    // ========================================================
    const t2Start = performance.now();
    const mateRes = this.mate.computeProjected({
      taskId: taskName,
      inputs: inventoryInput,
      solver: t2AnalyticalSolver,
    });
    const t2Elapsed = performance.now() - t2Start;

    const t2Outcome = new TriadaStepOutcome({
      stage: TriadaStage.T2_ANALYTICAL_SOLVER,
      passed: mateRes.status !== MATEStatus.R3_INFEASIBLE,
      data: mateRes.value,
      elapsedMs: t2Elapsed,
      notes: [mateRes.diagnosticMessage],
    });

    if (mateRes.status === MATEStatus.R3_INFEASIBLE) {
      diagnostics.push(`T2_FAIL: Solver aborted by MATE guard: ${mateRes.diagnosticMessage}`);
      return new TriadaExecutionReport({
        success: false,
        taskName,
        finalOutput: null,
        failedAtStage: TriadaStage.T2_ANALYTICAL_SOLVER,
        totalElapsedMs: performance.now() - start,
        mateStatus: MATEStatus.R3_INFEASIBLE,
        t1Outcome,
        t2Outcome,
        diagnostics,
      });
    }

    // ========================================================
    // STAGE T3: Bounded Projection & Global Invariant Verification
    // ========================================================
    const t3Start = performance.now();
    const [t3Valid, t3Reasons] = t3ProjectionVerifier(mateRes.value, inventoryInput);
    const t3Elapsed = performance.now() - t3Start;

    const t3Outcome = new TriadaStepOutcome({
      stage: TriadaStage.T3_PROJECTION_VERIFICATION,
      passed: t3Valid,
      data: { output: mateRes.value, verified: t3Valid },
      elapsedMs: t3Elapsed,
      notes: t3Reasons,
    });

    if (!t3Valid) {
      diagnostics.push(...t3Reasons.map((r) => `T3_FAIL: ${r}`));
      return new TriadaExecutionReport({
        success: false,
        taskName,
        finalOutput: mateRes.value,
        failedAtStage: TriadaStage.T3_PROJECTION_VERIFICATION,
        totalElapsedMs: performance.now() - start,
        mateStatus: MATEStatus.R3_INFEASIBLE,
        t1Outcome,
        t2Outcome,
        t3Outcome,
        diagnostics,
      });
    }

    diagnostics.push("TRIADA protocol executed successfully through T1, T2, and T3.");
    return new TriadaExecutionReport({
      success: true,
      taskName,
      finalOutput: mateRes.value,
      failedAtStage: null,
      totalElapsedMs: performance.now() - start,
      mateStatus: mateRes.status,
      t1Outcome,
      t2Outcome,
      t3Outcome,
      diagnostics,
    });
  }
}

export const TriadaProtocol = TriadaEngine;
