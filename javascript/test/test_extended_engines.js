import assert from 'node:assert';
import {
  SFSASession,
  UncertaintyPropagationEngine,
  UncertaintyInterval,
  UnitDimensionalEngine,
  DimensionVector,
  SurrogateModelingEngine,
  DataAssimilationEngine,
  SymbolicEquivalenceEngine,
  ParallelBatchEngine,
  RobustnessTestingEngine,
  ReproducibilityManifestEngine,
  LaboratoryDataRepository,
  DatasetTable
} from '../src/index.js';

console.log("Running SFSA Extended 9 Engines JavaScript Test Suite...");

// 1. UQE
{
  const uqe = new UncertaintyPropagationEngine();
  const a = new UncertaintyInterval({ nominal: 10.0, uncertainty: 1.0 });
  const b = new UncertaintyInterval({ nominal: 5.0, uncertainty: 0.5 });

  const sumRes = uqe.combineBinary(a, b, '+');
  assert.strictEqual(sumRes.nominal, 15.0);
  assert.ok(Math.abs(sumRes.uncertainty - Math.sqrt(1.25)) < 1e-4);

  const prodRes = uqe.combineBinary(a, b, '*');
  assert.strictEqual(prodRes.nominal, 50.0);

  const inputs = {
    x: new UncertaintyInterval({ nominal: 2.0, uncertainty: 0.1 }),
    y: new UncertaintyInterval({ nominal: 3.0, uncertainty: 0.2 })
  };
  const rep = uqe.propagateGeneral((p) => p.x ** 2 + p.y, inputs);
  assert.strictEqual(rep.outputInterval.nominal, 7.0);
  assert.ok(rep.outputInterval.uncertainty > 0);
  assert.strictEqual(rep.dominantContributors.length, 2);
}

// 2. UDE
{
  const ude = new UnitDimensionalEngine();
  const [dimKm, scaleKm] = ude.parseUnit("km");
  assert.strictEqual(dimKm.length, 1);
  assert.strictEqual(scaleKm, 1000.0);

  const valBars = ude.convert(200000.0, "pa", "bar");
  assert.ok(Math.abs(valBars - 2.0) < 1e-5);

  const [compat] = ude.verifyCompatibility("pa", "bar");
  assert.strictEqual(compat, true);

  const [incompat] = ude.verifyCompatibility("pa", "meter");
  assert.strictEqual(incompat, false);
}

// 3. SME
{
  const sme = new SurrogateModelingEngine();
  const points = [];
  const values = [];
  for (let i = 0; i < 10; i++) {
    points.push({ x: i });
    values.push(i ** 2);
  }

  const surrogate = sme.fitFromHistory("quad", points, values);
  const predExact = surrogate.predict({ x: 4 });
  assert.ok(Math.abs(predExact.value - 16.0) < 1e-5);
  assert.strictEqual(predExact.uncertainty, 0.0);

  const predMid = surrogate.predict({ x: 4.5 });
  assert.ok(predMid.value > 16.0 && predMid.value < 25.0);
  assert.ok(predMid.uncertainty > 0.0);

  const amfSolver = sme.createAmfSolver("quad");
  const res = amfSolver({ x: 4 });
  assert.ok(Math.abs(res.value - 16.0) < 1e-5);
}

// 4. DAE
{
  const dae = new DataAssimilationEngine(1e-4, 50);
  const experimentalData = [
    { x: 1.0, observed: 2.5 },
    { x: 2.0, observed: 5.0 },
    { x: 3.0, observed: 7.5 },
    { x: 4.0, observed: 10.0 }
  ];

  const modelFn = (inputs, params) => params.k * inputs.x;

  const result = dae.calibrate({
    experimentalData,
    modelFn,
    initialParams: { k: 1.0 },
    targetKey: "observed",
    paramBounds: { k: [0.5, 5.0] }
  });

  assert.strictEqual(result.converged, true);
  assert.ok(Math.abs(result.calibratedParameters.k - 2.5) < 0.1);
  assert.ok(result.finalRmse < 0.1);
  assert.ok(result.rSquared > 0.95);
}

// 5. SYE
{
  const sye = new SymbolicEquivalenceEngine();
  const simp = sye.simplify("0 * x + 1 * y + 0");
  assert.strictEqual(simp.simplifiedExpression, "y");
  assert.ok(simp.operationsEliminatedCount >= 2);

  assert.strictEqual(sye.areEquivalent("0 * a + b", "1 * b"), true);
  assert.strictEqual(sye.areEquivalent("x + 1", "x + 2"), false);
}

// 6. PBE
{
  const pbe = new ParallelBatchEngine(2);
  const tasks = [0, 1, 2, 3, 4];
  const summary = await pbe.mapConcurrent(tasks, async (t) => t * 3);

  assert.strictEqual(summary.totalItems, 5);
  assert.strictEqual(summary.successfulItems, 5);
  assert.strictEqual(summary.results[3], 9);
}

// 7. RTE
{
  const rte = new RobustnessTestingEngine();
  const rep = rte.stressTest(
    { x: 10.0, y: 5.0 },
    (p) => p.x * 2.0 + p.y,
    [0.01, 0.05]
  );
  assert.strictEqual(rep.isRobust, true);
  assert.ok(rep.fragilityScore < 0.5);
  assert.ok(rep.conditionNumber > 0.0);
}

// 8. RME
{
  const rme = new ReproducibilityManifestEngine();
  const manifest = rme.generateManifest("VerificationSession", 32, { runId: "EXP-1" });
  assert.strictEqual(manifest.sessionName, "VerificationSession");
  assert.strictEqual(manifest.activeEngineCount, 32);
  assert.ok(manifest.cryptographicSeal.length > 0);
  assert.ok(manifest.platformInfo.system.length > 0);
}

// 9. LDR
{
  const ldr = new LaboratoryDataRepository();
  const solarFluxModel = (p) => {
    const flux = (1361.0 / (p.distanceAu ** 2)) * (1.0 - p.albedo);
    const tempEq = (flux / (4.0 * 5.67e-8)) ** 0.25;
    return { absorbedFlux: flux, tempEquilibriumK: tempEq };
  };

  const table = ldr.synthesizeReferenceTable({
    tableId: "planetary_radiation_baseline",
    name: "Planetary Absorbed Flux and Equilibrium Temp Dataset",
    modelFn: solarFluxModel,
    parameterSweeps: {
      distanceAu: [0.72, 1.0, 1.52],
      albedo: [0.1, 0.3, 0.6]
    },
    description: "Planetary radiation dataset"
  });

  assert.strictEqual(table.tableId, "planetary_radiation_baseline");
  assert.strictEqual(table.rows.length, 9);
  assert.ok(table.columns.includes("distanceAu"));
  assert.ok(table.columns.includes("tempEquilibriumK"));
  assert.ok(table.summaryStats.tempEquilibriumK.min > 0);

  // Markdown
  const md = table.toMarkdown(5);
  assert.ok(md.includes("| distanceAu |"));
  assert.ok(md.includes("additional rows in repository"));

  // Interpolation
  const interpTemp = ldr.interpolateFromTable(
    "planetary_radiation_baseline",
    { distanceAu: 1.0, albedo: 0.3 },
    "tempEquilibriumK"
  );
  assert.ok(interpTemp !== null);
  assert.ok(interpTemp > 240.0 && interpTemp < 270.0);

  // CSV
  const csv = ldr.exportCsv("planetary_radiation_baseline");
  assert.ok(csv.includes("distanceAu,albedo,absorbedFlux,tempEquilibriumK"));
}

// Session Integration
{
  const session = new SFSASession({ name: "JSScienceSession" });
  const rep = session.generateReport();
  assert.strictEqual(rep.activeEnginesCount, 39);

  const table = session.synthesizeDataset({
    tableId: "session_tbl",
    name: "Session Table",
    modelFn: (p) => ({ metric: p.x * 10 }),
    parameterSweeps: { x: [1, 2, 3] }
  });
  assert.strictEqual(table.rows.length, 3);
  assert.ok(session.getDataset("session_tbl") !== null);
}

console.log("✅ ALL 9 EXTENDED ENGINES (INCLUDING LDR) VERIFIED IN JAVASCRIPT!");
