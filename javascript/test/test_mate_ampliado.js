import assert from 'node:assert';
import {
  MATEEngine,
  MATEStatus,
  ReuseLevel,
  MechanismStatus,
  MechanismCard,
} from '../src/index.js';

console.log("Running SFSA MATE Ampliado JavaScript Test Suite...");

// 1. Multilevel Lookup (L0 and L1)
{
  const mate = new MATEEngine({ cachePrecisionDecimals: 4 });

  // Fresh run (L5 Full compute)
  const res1 = mate.computeProjected({
    taskId: "kinetic_energy",
    inputs: { mass: 2.0, velocity: 10.0 },
    solver: inp => 0.5 * inp.mass * (inp.velocity ** 2),
  });
  assert.strictEqual(res1.value, 100.0);
  assert.strictEqual(res1.cached, false);
  assert.strictEqual(res1.reuseLevel, ReuseLevel.L5);

  // Exact match (L0 Zero-compute)
  const resL0 = mate.computeProjected({
    taskId: "kinetic_energy",
    inputs: { mass: 2.0, velocity: 10.0 },
    solver: () => { throw new Error("Should not be called"); },
  });
  assert.strictEqual(resL0.value, 100.0);
  assert.strictEqual(resL0.cached, true);
  assert.strictEqual(resL0.reuseLevel, ReuseLevel.L0);
  assert.strictEqual(mate.stats().l0ExactHits, 1);

  // Approximate neighbor match (L1 within tolerance)
  const resL1 = mate.computeProjected({
    taskId: "kinetic_energy",
    inputs: { mass: 2.01, velocity: 10.02 },
    solver: () => { throw new Error("Should not be called"); },
  });
  assert.strictEqual(resL1.value, 100.0);
  assert.strictEqual(resL1.cached, true);
  assert.strictEqual(resL1.reuseLevel, ReuseLevel.L1);
  assert.strictEqual(mate.stats().l1ApproxHits, 1);
  console.log("  ✓ MATE-Core Multilevel Lookup (L0 & L1) verified.");
}

// 2. Speculative Execution Battery (MATE-Spec)
{
  const mate = new MATEEngine({ specMode: "bounded", maxSpecChains: 2 });

  const denseSolver = inp => inp.x * 10.0 + 5.0;

  const candidates = [
    {
      chain: ["AMF_LOW", "UAS"],
      evalFn: inp => inp.x * 10.0 + 5.02,
      costFactor: 0.25,
      tolerance: 0.05,
      shortcuts: { fidelity: "LOW", earlyStop: true },
    },
    {
      chain: ["BAD_CHAIN"],
      evalFn: inp => inp.x * 2.0,
      costFactor: 0.10,
      tolerance: 0.05,
    },
  ];

  const res = mate.computeProjected({
    taskId: "fluid_pressure",
    inputs: { x: 3.0 },
    solver: denseSolver,
    candidateChains: candidates,
  });

  assert.strictEqual(res.value, 35.0);
  assert.strictEqual(res.speculativeDiscoveries.length, 1);
  const discovered = res.speculativeDiscoveries[0];
  assert.deepStrictEqual(discovered.chain, ["AMF_LOW", "UAS"]);
  assert.strictEqual(discovered.status, MechanismStatus.CANDIDATE);
  assert.strictEqual(discovered.expectedCost, 0.25);

  // Negative knowledge captured for BAD_CHAIN
  const pattern = mate.synthesizePatternSignature("fluid_pressure", { x: 3.0 });
  assert.ok(mate.negativeKnowledge.has(pattern));
  const failures = mate.negativeKnowledge.get(pattern);
  assert.ok(failures.some(f => f.chain.includes("BAD_CHAIN")));
  console.log("  ✓ MATE-Spec Speculative Battery & Negative Knowledge verified.");
}

// 3. MATE-Policy Promotion & Governance
{
  const mate = new MATEEngine();

  const card = new MechanismCard({
    id: "mech_flow_opt",
    pattern: "navier_stokes::laminar",
    chain: ["SRA_REDUCE", "AMF_MID"],
    expectedCost: 0.30,
    expectedQuality: 0.98,
    status: MechanismStatus.CANDIDATE,
    modelVersion: "v1.0",
  });
  mate.cards.set(card.id, card);
  mate.plansByPattern.set("navier_stokes::laminar", [card.id]);

  // Promote to TRUSTED
  assert.strictEqual(mate.promote("mech_flow_opt"), true);
  assert.strictEqual(mate.cards.get("mech_flow_opt").status, MechanismStatus.TRUSTED);

  // Promote to DEFAULT
  mate.promote("mech_flow_opt", true);
  assert.strictEqual(mate.cards.get("mech_flow_opt").status, MechanismStatus.DEFAULT);

  // Explain mechanism
  const explanation = mate.explain("mech_flow_opt");
  assert.ok(explanation.includes("mech_flow_opt"));
  assert.ok(explanation.includes("SRA_REDUCE -> AMF_MID"));
  assert.ok(explanation.toLowerCase().includes("speedup"));

  // Reject mechanism
  mate.reject("mech_flow_opt", "Turbulence transition observed");
  assert.strictEqual(mate.cards.get("mech_flow_opt").status, MechanismStatus.REJECTED);
  assert.strictEqual(mate.cards.get("mech_flow_opt").failures.length, 1);

  // Invalidate by model version upgrade
  const card2 = new MechanismCard({ id: "mech_v1", pattern: "heat", chain: ["ICR"], modelVersion: "v1.0" });
  mate.cards.set(card2.id, card2);
  const invalidated = mate.invalidate("v2.0");
  assert.ok(invalidated >= 1);
  assert.strictEqual(mate.cards.get("mech_v1").status, MechanismStatus.REJECTED);
  console.log("  ✓ MATE-Policy Governance, Promotion & Invalidation verified.");
}

console.log("🎉 ALL MATE AMPLIADO CAPABILITIES VERIFIED IN JAVASCRIPT!");
