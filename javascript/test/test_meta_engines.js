import assert from 'node:assert';
import {
  SFSASession,
  OrchestrationRoutingEngine,
  QueryArchetype,
  ValueInformationEngine,
  TransferExperienceEngine,
  ExperimentLoopEngine,
  ModelRiskEngine,
  ExplanationAuditEngine,
  ScheduleResourceEngine
} from '../src/index.js';

console.log("Running SFSA Meta-Orchestration Engines (33–39) JavaScript Test Suite...");

// 1. ORE: Orchestration & Routing Engine
{
  const ore = new OrchestrationRoutingEngine();

  // Exploratory sweep with high cardinality and 5D
  const planSweep = ore.planPipeline({
    queryArchetype: QueryArchetype.EXPLORATORY_SWEEP,
    inputCardinality: 500,
    parameterDim: 5
  });
  assert.ok(planSweep.activeEngineSequence.includes('CQE'));
  assert.ok(planSweep.activeEngineSequence.includes('SRA'));
  assert.ok(planSweep.activeEngineSequence.includes('AMF'));
  assert.strictEqual(planSweep.suggestedFidelity, 'CHEAP_FIRST');
  assert.ok(planSweep.estimatedComputeReductionPct >= 90.0);

  // High precision solve
  const planSolve = ore.planPipeline({
    queryArchetype: QueryArchetype.HIGH_PRECISION_SOLVE
  });
  assert.deepStrictEqual(planSolve.activeEngineSequence, ['MRE', 'CAE', 'MATE', 'TRIADA', 'UQE']);
  assert.strictEqual(planSolve.suggestedFidelity, 'HIGH');

  // Verification audit
  const planAudit = ore.planPipeline({
    queryArchetype: QueryArchetype.VERIFICATION_AUDIT
  });
  assert.ok(planAudit.activeEngineSequence.includes('TRIADA'));
  assert.ok(planAudit.activeEngineSequence.includes('XXE'));
  console.log("  ✓ ORE (Orchestration & Routing Engine) verified.");
}

// 2. VOI: Value-of-Information Decision Engine
{
  const voi = new ValueInformationEngine({ minEvoiThreshold: 0.15 });

  // Candidate 1: Close to boundary with high uncertainty -> COMPUTE
  const evalCompute = voi.evaluateCandidate('c1', 10.1, 0.8, 10.0, 1.0);
  assert.strictEqual(evalCompute.recommendation, 'COMPUTE');
  assert.ok(evalCompute.expectedValueOfInformation > 0.3);

  // Candidate 2: Far from boundary with low uncertainty -> SKIP_LOW_VALUE
  const evalSkip = voi.evaluateCandidate('c2', 50.0, 0.01, 10.0, 1.0);
  assert.strictEqual(evalSkip.recommendation, 'SKIP_LOW_VALUE');

  // Candidate 3: High cost with moderate EVOI -> USE_CHEAP_SURROGATE
  const evalSurrogate = voi.evaluateCandidate('c3', 10.2, 0.4, 10.0, 25.0);
  assert.strictEqual(evalSurrogate.recommendation, 'USE_CHEAP_SURROGATE');

  // Filter candidates
  const candidates = [
    { id: 'A', val: 10.05, unc: 0.9, cost: 1.0 },
    { id: 'B', val: 80.0, unc: 0.05, cost: 1.0 }
  ];
  const approved = voi.filterCandidates(
    candidates,
    c => [c.val, c.unc],
    10.0,
    c => c.cost
  );
  assert.strictEqual(approved.length, 1);
  assert.strictEqual(approved[0].id, 'A');
  console.log("  ✓ VOI (Value-of-Information Decision Engine) verified.");
}

// 3. TXE: Transfer & Cross-Session Experience Engine
{
  const txe = new TransferExperienceEngine();

  const sessionA = new SFSASession({ name: "Thermodynamics_Campaign" });
  sessionA.cae.minSupport = 2;
  sessionA.cae.recordInfeasibility({ temperature: -5.0 });
  sessionA.cae.recordInfeasibility({ temperature: -20.0 });
  sessionA.registerLayer("heat_layer", { temp: 300 }, "Thermal Dynamics");

  // Capture snapshot
  const snapshot = txe.captureSessionExperience(sessionA);
  assert.ok(snapshot.priors.length >= 1);
  assert.strictEqual(snapshot.frameworkName, "Thermodynamics_Campaign");

  // Warm-start session B
  const sessionB = new SFSASession({ name: "Propulsion_Design" });
  const transferred = txe.warmStartSession(sessionB, ["Thermal Dynamics"]);
  assert.ok(transferred >= 1);
  console.log("  ✓ TXE (Transfer Experience Engine) verified.");
}

// 4. ELE: Experiment Loop Engine
{
  const ele = new ExperimentLoopEngine();
  const session = new SFSASession({ name: "Optics_Lab" });

  const candidateSpace = [
    { x: 1.0, wavelength: 400.0 },
    { x: 2.5, wavelength: 550.0 },
    { x: 4.0, wavelength: 700.0 }
  ];

  const proposal = ele.proposeNextExperiment(
    candidateSpace,
    c => c.x * 2.0,
    c => c.x * 0.5 // x=4.0 has max uncertainty 2.0
  );
  assert.strictEqual(proposal.targetParameters.x, 4.0);
  assert.strictEqual(proposal.predictedTheoreticalOutput, 8.0);

  // Lab measurement assimilates observed value
  const res = ele.closeLoop(proposal, 8.4, session);
  assert.strictEqual(res.iterationIndex, 1);
  assert.ok(Math.abs(res.discrepancyDelta - 0.4) < 1e-4);
  assert.strictEqual(ele.iterations.length, 1);
  console.log("  ✓ ELE (Experiment Loop Engine) verified.");
}

// 5. MRE: Model Risk & Validity Engine
{
  const mre = new ModelRiskEngine({ extrapolationThreshold: 0.20 });
  mre.registerEnvelope("pressure", 1.0, 10.0, 0.0, 100.0);

  // 1. Safe input
  const repSafe = mre.assessRisk({ pressure: 5.0 });
  assert.strictEqual(repSafe.isSafe, true);
  assert.strictEqual(repSafe.verdict, "COMPUTE_SAFE");

  // 2. Caution extrapolation
  const mreTight = new ModelRiskEngine({ extrapolationThreshold: 0.10 });
  mreTight.registerEnvelope("pressure", 1.0, 10.0, 0.0, 100.0);
  const repExtrap = mreTight.assessRisk({ pressure: 11.5 });
  assert.strictEqual(repExtrap.isSafe, true);
  assert.strictEqual(repExtrap.verdict, "CAUTION_EXTRAPOLATION");

  // 3. Hard limit violation
  const repAbort = mre.assessRisk({ pressure: -2.0 });
  assert.strictEqual(repAbort.isSafe, false);
  assert.strictEqual(repAbort.verdict, "ABORT_INVALID_REGIME");
  assert.ok(repAbort.warnings.length >= 1);
  console.log("  ✓ MRE (Model Risk & Validity Engine) verified.");
}

// 6. XXE: Explanation & Audit Engine
{
  const xxe = new ExplanationAuditEngine();
  xxe.recordDecision("MATE", "CACHE_HIT", "Exact trajectory match found in R1 memoization", 95.0, { taskId: "solve_t1" });
  xxe.recordDecision("CAE", "CUT_DOMAIN", "Pruned negative concentration subspace", 40.0, { taskId: "solve_t1" });

  const explanation = xxe.explainTask("solve_t1");
  assert.strictEqual(explanation.summaryVerdict, "OPTIMIZED_AND_VERIFIED");
  assert.strictEqual(explanation.decisions.length, 2);
  assert.ok(explanation.narrative.includes("MATE"));
  assert.ok(explanation.narrative.includes("CAE"));

  const md = xxe.exportAuditMarkdown();
  assert.ok(md.includes("# SFSA Computational Audit Trail"));
  assert.ok(md.includes("CACHE_HIT"));
  console.log("  ✓ XXE (Explanation & Audit Engine) verified.");
}

// 7. SRE: Schedule & Resource Engine
{
  const sre = new ScheduleResourceEngine(4);

  sre.enqueueTask("task_low", {}, 0.2, 50.0);
  sre.enqueueTask("task_high", {}, 0.9, 10.0);
  sre.enqueueTask("task_mid", {}, 0.5, 20.0);

  // Highest priority task should be first
  const schedule = sre.planCampaignSchedule(0.5);
  assert.strictEqual(schedule.taskOrder[0], "task_high");
  assert.strictEqual(schedule.concurrencyWorkers, 4);
  assert.strictEqual(schedule.backpressureActive, false);

  // Backpressure triggers when budget exhaustion > 0.85
  const scheduleThrottled = sre.planCampaignSchedule(0.90);
  assert.strictEqual(scheduleThrottled.backpressureActive, true);
  assert.strictEqual(scheduleThrottled.concurrencyWorkers, 2);

  // Dispatch in order
  const first = sre.dispatchNext();
  assert.strictEqual(first.taskId, "task_high");
  console.log("  ✓ SRE (Schedule & Resource Engine) verified.");
}

// 8. Session 39 Engines Integration
{
  const session = new SFSASession({ name: "Unified_Meta_Session" });
  const report = session.generateReport();
  assert.strictEqual(report.activeEnginesCount, 39);
  assert.ok(session.ore !== undefined);
  assert.ok(session.voi !== undefined);
  assert.ok(session.txe !== undefined);
  assert.ok(session.ele !== undefined);
  assert.ok(session.mre !== undefined);
  assert.ok(session.xxe !== undefined);
  assert.ok(session.sre !== undefined);
  console.log("  ✓ Unified SFSASession (39 Engines) verified.");
}

console.log("🎉 ALL 7 META-ENGINES SUCCESSFULLY VERIFIED IN JAVASCRIPT!");
