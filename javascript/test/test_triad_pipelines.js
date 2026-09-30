import assert from 'node:assert';
import {
  MATEEngine,
  TriadaEngine,
  AdaptiveSamplingEngine,
  AdaptiveMultiFidelityEngine,
  FidelityLevel,
  SensitivityReductionAnalyzer,
  ConstraintAwarenessEngine,
  ICREngine,
  QueryCompressionEngine,
  ParallelBatchEngine,
  LaboratoryDataRepository,
  UnitDimensionalEngine,
  UncertaintyPropagationEngine,
  UncertaintyInterval,
  DataAssimilationEngine,
  SurrogateModelingEngine,
  RobustnessTestingEngine,
} from '../src/index.js';

console.log("Running SFSA Multi-Engine & Triad Pipelines JavaScript Test Suite...");

// 1. Triad: [ASG + AMF + MATE]
{
  const asg = new AdaptiveSamplingEngine(0.15);
  const amf = new AdaptiveMultiFidelityEngine(0.05);
  const mate = new MATEEngine();

  const candidates = [];
  for (let i = 0; i < 10; i++) {
    for (let j = 0; j < 10; j++) {
      candidates.push({ x: i / 10.0, y: j / 10.0 });
    }
  }

  let evaluatedCount = 0;
  for (const pt of candidates) {
    const cand = asg.evaluateCandidate(pt, () => 0.05);
    if (cand.skipRecommended) continue;

    const dec = amf.evaluate({
      taskId: "asg_amf_js",
      inputs: pt,
      cheapSolver: (p) => ({ value: p.x * 2.5 + p.y * 1.5, uncertainty: 0.03 }),
      expensiveSolver: (p) => mate.computeProjected({
        taskId: "exp_task",
        inputs: p,
        solver: (ip) => ip.x * 2.5 + ip.y * 1.5
      }).value
    });

    assert.ok(dec.value !== null && dec.value !== undefined);
    asg.recordEvaluation(pt, dec.value);
    evaluatedCount += 1;
  }

  assert.ok(evaluatedCount < candidates.length);
  assert.ok(evaluatedCount > 0);
}

// 2. Triad: [TRIADA + UDE + UQE]
{
  const ude = new UnitDimensionalEngine();
  const uqe = new UncertaintyPropagationEngine();
  const triada = new TriadaEngine();

  const rawMassG = 1500.0;
  const massKg = ude.convert(rawMassG, "g", "kg");
  assert.strictEqual(massKg, 1.5);

  const rep = triada.runPipeline({
    taskName: "kinetic_energy_js",
    inventoryInput: { mass: massKg, velocity: 20.0 },
    t1InventoryValidator: (inv) => [inv.mass > 0 && inv.velocity >= 0, []],
    t2AnalyticalSolver: (inv) => 0.5 * inv.mass * (inv.velocity ** 2),
    t3ProjectionVerifier: (res) => [res >= 0, []]
  });
  assert.strictEqual(rep.success, true);
  assert.strictEqual(rep.finalOutput, 300.0);

  const inputs = {
    m: new UncertaintyInterval({ nominal: massKg, uncertainty: 0.015 }),
    v: new UncertaintyInterval({ nominal: 20.0, uncertainty: 0.5 })
  };
  const propRep = uqe.propagateGeneral((p) => 0.5 * p.m * (p.v ** 2), inputs);
  assert.strictEqual(propRep.outputInterval.nominal, 300.0);
  assert.ok(propRep.outputInterval.uncertainty > 0);
}

// 3. Triad: [SRA + CAE + ICR]
{
  const sra = new SensitivityReductionAnalyzer();
  const cae = new ConstraintAwarenessEngine();
  const icr = new ICREngine();

  const complexObj = (p) => 5.0 * p.x1 + 2.0 * p.x2 + 0.0001 * p.x3;
  const nominal = { x1: 1.0, x2: 2.0, x3: 3.0 };

  const red = sra.reduceParameterSpace(nominal, complexObj);
  assert.ok(red.retainedParameters.includes("x1"));

  cae.addExplicitConstraint((p) => [p.x1 > 0, "x1 must be positive"]);
  const [okV] = cae.validateInputs({ x1: 2.0 });
  const [okInv] = cae.validateInputs({ x1: -1.0 });
  assert.strictEqual(okV, true);
  assert.strictEqual(okInv, false);

  const { result: res, profile } = icr.optimizeAndExecute({
    taskId: "icr_task",
    inputParams: { x1: 2.0 },
    exactSolver: (p) => p.x1 * 2.0,
    analyticalShortcut: (p) => p.x1 * 2.0,
    shortcutValidityCondition: () => true
  });
  assert.strictEqual(res, 4.0);
}

// 4. Triad: [CQE + PBE + LDR]
{
  const cqe = new QueryCompressionEngine(0.1);
  const pbe = new ParallelBatchEngine(2);
  const ldr = new LaboratoryDataRepository();

  const queries = [];
  for (let i = 0; i < 50; i++) {
    queries.push({ t: (i % 10) + (i * 0.001) });
  }

  const compRes = cqe.compressAndSolve({
    queries,
    heavySolver: (q) => Math.sin(q.t) * 10.0
  });
  assert.ok(compRes.representativeCount < queries.length);

  const table = ldr.synthesizeReferenceTable({
    tableId: "triad_tbl",
    name: "Triad Table",
    modelFn: (p) => ({ val: Math.sin(p.t) * 10.0 }),
    parameterSweeps: { t: [1.0, 2.0, 3.0] }
  });
  assert.strictEqual(table.rows.length, 3);
  const val = ldr.interpolateFromTable("triad_tbl", { t: 2.01 }, "val");
  assert.ok(val !== null);
}

// 5. Triad: [DAE + SME + RTE]
{
  const dae = new DataAssimilationEngine(1e-4, 30);
  const sme = new SurrogateModelingEngine();
  const rte = new RobustnessTestingEngine();

  const sensorData = [];
  for (let i = 1; i <= 8; i++) {
    sensorData.push({ x: i, observed: 2.5 * i });
  }

  const calib = dae.calibrate({
    experimentalData: sensorData,
    modelFn: (inp, p) => p.k * inp.x,
    initialParams: { k: 1.0 },
    targetKey: "observed",
    paramBounds: { k: [0.5, 5.0] }
  });
  assert.strictEqual(calib.converged, true);

  const trainPts = sensorData.map(d => ({ x: d.x }));
  const trainVals = sensorData.map(d => calib.calibratedParameters.k * d.x);
  const surrogate = sme.fitFromHistory("calib_surr", trainPts, trainVals);
  const pred = surrogate.predict({ x: 4 });
  assert.ok(Math.abs(pred.value - 10.0) < 0.1);

  const robust = rte.stressTest({ k: calib.calibratedParameters.k }, (p) => p.k * 10.0);
  assert.strictEqual(robust.isRobust, true);
}

console.log("✅ ALL 5 TRIAD PIPELINES VERIFIED SUCCESSFULLY IN JAVASCRIPT!");
