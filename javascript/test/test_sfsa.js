/**
 * test_sfsa.js — Comprehensive Test Suite for SFSA (JavaScript)
 * ==============================================================
 * Validates all 5 engines and unified SFSASession in Node.js.
 */

import assert from 'node:assert';
import {
  MATEEngine,
  MATEStatus,
  TriadaEngine,
  TriadaStage,
  AutocompleteEngine,
  ConnectionCandidate,
  FrameworkLayerNetwork,
  ICREngine,
  OptimizationLevel,
  SFSASession,
} from '../src/index.js';

console.log("Running SFSA JavaScript Test Suite...");

// -------------------------------------------------------------
// 1. MATE Engine Tests
// -------------------------------------------------------------
{
  const engine = new MATEEngine();
  let calls = 0;
  const solver = (inv) => {
    calls++;
    return inv.x * 3.0 + inv.y;
  };

  // Fresh compute
  const res1 = engine.computeProjected({
    taskId: "calc_1",
    inputs: { x: 4, y: 2 },
    solver,
  });
  assert.strictEqual(res1.status, MATEStatus.R1_EXACT);
  assert.strictEqual(res1.value, 14);
  assert.strictEqual(res1.cached, false);
  assert.strictEqual(calls, 1);

  // Memoized cache hit
  const res2 = engine.computeProjected({
    taskId: "calc_1",
    inputs: { x: 4, y: 2 },
    solver,
  });
  assert.strictEqual(res2.status, MATEStatus.R1_EXACT);
  assert.strictEqual(res2.value, 14);
  assert.strictEqual(res2.cached, true);
  assert.strictEqual(calls, 1); // Not called again!

  // Boundary abort (R3)
  const resAbort = engine.computeProjected({
    taskId: "calc_bound",
    inputs: { tempK: -10 },
    solver: () => { throw new Error("Should not run"); },
    boundaryValidator: (inputs) => [inputs.tempK >= 0, "Absolute zero violation"],
  });
  assert.strictEqual(resAbort.status, MATEStatus.R3_INFEASIBLE);
  assert.strictEqual(resAbort.value, null);
  console.log("  ✓ MATE Engine (memoization & boundary early-abort) passed");
}

// -------------------------------------------------------------
// 2. TRIADA Engine Tests
// -------------------------------------------------------------
{
  const triada = new TriadaEngine();

  const report = triada.runPipeline({
    taskName: "gravitational_potential",
    inventoryInput: { massKg: 500, radiusM: 1000 },
    t1InventoryValidator: (inv) => [inv.massKg > 0 && inv.radiusM > 0, ["Valid positive physical quantities"]],
    t2AnalyticalSolver: (inv) => (6.6743e-11 * inv.massKg) / inv.radiusM,
    t3ProjectionVerifier: (phi, inv) => [phi > 0, ["Potential is positive definite in magnitude"]],
  });

  assert.strictEqual(report.success, true);
  assert.strictEqual(report.failedAtStage, null);
  assert.ok(report.finalOutput > 0);

  // Test T1 failure early exit
  const failReport = triada.runPipeline({
    taskName: "broken_inventory",
    inventoryInput: { massKg: -5 },
    t1InventoryValidator: (inv) => [inv.massKg > 0, ["Negative mass physically impossible"]],
    t2AnalyticalSolver: () => { throw new Error("Must not run"); },
    t3ProjectionVerifier: () => [true, []],
  });

  assert.strictEqual(failReport.success, false);
  assert.strictEqual(failReport.failedAtStage, TriadaStage.T1_INVENTORY);
  console.log("  ✓ TRIADA Engine (3-stage execution & fast-fail) passed");
}

// -------------------------------------------------------------
// 3. Autocomplete Engine Tests
// -------------------------------------------------------------
{
  const auto = new AutocompleteEngine();

  auto.registerRule("ideal_gas_pressure", (ctx) => {
    if (ctx._targetGap?.targetKey === "pressurePa") {
      if (ctx.moles && ctx.volumeM3 && ctx.temperatureK) {
        return new ConnectionCandidate({
          ruleName: "ideal_gas_law",
          targetKey: "pressurePa",
          derivedValue: (ctx.moles * 8.314 * ctx.temperatureK) / ctx.volumeM3,
          confidence: 0.98,
          sourceDependencies: ["moles", "volumeM3", "temperatureK"],
          derivationNotes: "P = n R T / V",
        });
      }
    }
    return null;
  });

  const state = { moles: 10, volumeM3: 0.1, temperatureK: 300 };
  const schema = { pressurePa: "Pressure in Pascals", entropyJ_K: "System entropy" };

  const { updatedState, appliedCandidates } = auto.autoFill(state, schema);
  assert.ok(updatedState.pressurePa > 0);
  assert.strictEqual(appliedCandidates.length, 1);
  assert.strictEqual(appliedCandidates[0].ruleName, "ideal_gas_law");
  console.log("  ✓ Autocomplete Engine (gap detection & candidate connection) passed");
}

// -------------------------------------------------------------
// 4. Framework Layer Network (FLN) Tests
// -------------------------------------------------------------
{
  const fln = new FrameworkLayerNetwork();

  fln.registerLayer("inputs", { baseValue: 10 });
  fln.registerLayer("layer_alpha", { alphaValue: 0 });
  fln.registerLayer("layer_beta", { betaValue: 0 });

  // inputs -> alpha
  fln.connectLayers("inputs", "layer_alpha", (src) => ({ alphaValue: src.baseValue * 2 }));
  // alpha -> beta
  fln.connectLayers("layer_alpha", "layer_beta", (src) => ({ betaValue: src.alphaValue + 5 }));

  // Update root layer
  const versions = fln.updateLayer("inputs", { baseValue: 25 });
  const alpha = fln.getLayer("layer_alpha");
  const beta = fln.getLayer("layer_beta");

  assert.strictEqual(alpha.state.alphaValue, 50); // 25 * 2
  assert.strictEqual(beta.state.betaValue, 55);    // 50 + 5
  assert.ok(versions.layer_beta >= 2);
  console.log("  ✓ FLN Engine (reactive DAG cascading propagation) passed");
}

// -------------------------------------------------------------
// 5. In-Frame Computer Reduction (ICR) Tests
// -------------------------------------------------------------
{
  const icr = new ICREngine({ level: OptimizationLevel.O2_ANALYTICAL });

  const denseSolver = (inputs) => {
    let acc = 0;
    for (let i = 0; i < 500; i++) acc += inputs.val;
    return acc;
  };

  const analyticalShortcut = (inputs) => inputs.val * 500;

  const { result, profile } = icr.optimizeAndExecute({
    taskId: "reduction_test",
    inputParams: { val: 2 },
    exactSolver: denseSolver,
    analyticalShortcut,
    estimatedDenseOps: 500,
  });

  assert.strictEqual(result, 1000);
  assert.ok(profile.operationsEliminated >= 490);
  assert.ok(profile.reductionPercentage >= 95.0);
  console.log("  ✓ ICR Engine (in-frame computational reduction & shortcut) passed");
}

// -------------------------------------------------------------
// 6. SFSASession Unified Orchestrator Tests
// -------------------------------------------------------------
{
  const session = new SFSASession({ name: "Astrochemistry_Study" });

  session.registerLayer("cosmic_abundance", { h2_fraction: 0.75, he_fraction: 0.25 });
  session.registerLayer("metallicity", {});

  session.connectLayers("cosmic_abundance", "metallicity", (src) => ({
    metal_fraction: Math.max(0, 1.0 - src.h2_fraction - src.he_fraction),
  }));

  session.updateLayer("cosmic_abundance", { h2_fraction: 0.70, he_fraction: 0.28 });
  const met = session.fln.getLayer("metallicity");
  assert.ok(Math.abs(met.state.metal_fraction - 0.02) < 1e-6);

  const res = session.compute({
    taskId: "metallicity_mass",
    inventory: { metal_frac: 0.02, totalMass: 1000 },
    solver: (inv) => inv.metal_frac * inv.totalMass,
  });

  assert.strictEqual(res.value, 20);

  const report = session.sessionReport();
  assert.strictEqual(report.sessionName, "Astrochemistry_Study");
  assert.strictEqual(report.activeLayersCount, 2);
  assert.ok(report.totalQueries >= 1);
  console.log("  ✓ SFSASession (orchestration across all engines) passed");
}

// -------------------------------------------------------------
// 7. ParetoPathEngine Tests
// -------------------------------------------------------------
{
  const { ParetoPathEngine, TransitionStep } = await import('../src/index.js');
  const engine = new ParetoPathEngine();

  engine.registerStep(
    new TransitionStep({
      stepId: "step_fast",
      name: "Fast Step",
      cost: 50,
      duration: 2,
      feasibility: 0.95,
      deltaState: { tempK: 20 },
    })
  );
  engine.registerStep(
    new TransitionStep({
      stepId: "step_cheap",
      name: "Cheap Step",
      cost: 10,
      duration: 15,
      feasibility: 0.90,
      deltaState: { tempK: 20 },
    })
  );

  const paths = engine.findPathways({
    initialState: { tempK: 280 },
    targetState: { tempK: 300 },
    maxSteps: 2,
  });

  assert.ok(paths.length >= 2);
  assert.ok(paths.every((p) => p.isParetoOptimal));
  console.log("  ✓ ParetoPathEngine (Pareto frontier discovery) passed");
}

// -------------------------------------------------------------
// 8. LayerConsistencyProjector Tests
// -------------------------------------------------------------
{
  const { LayerConsistencyProjector } = await import('../src/index.js');
  const projector = new LayerConsistencyProjector();

  const report = projector.projectAndIntersect({
    layerAId: "kinetics",
    layerAState: { reactionRate: 25.0, activationEnergy: 45000, tempK: 350 },
    layerBId: "viscosity",
    layerBState: { dynamicViscosity: 0.001, tempK: 300 }, // tempK mismatch
    knownBounds: { dynamicViscosity: [0.0001, 0.05] },
  });

  assert.strictEqual(report.totalParametersCompared, 5);
  assert.ok(report.stronglyCoupledPairs.length > 0);
  assert.ok(report.normalizedVectorDistance >= 0.0);
  assert.strictEqual(report.inconsistencies.length, 1);
  assert.strictEqual(report.inconsistencies[0].conflictType, "VALUE_MISMATCH");
  assert.strictEqual(report.inconsistencies[0].parameterName, "tempK");
  console.log("  ✓ LayerConsistencyProjector (parameter consistency & coupling check) passed");
}

console.log("\n=======================================================");
console.log("ALL SFSA JAVASCRIPT TESTS PASSED SUCCESSFULLY! (100%)");
console.log("=======================================================");
