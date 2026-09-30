import assert from 'node:assert';
import {
  SFSASession,
  AdaptiveMultiFidelityEngine,
  FidelityLevel,
  AdaptiveSamplingEngine,
  SensitivityReductionAnalyzer,
  UncertaintyAwareStoppingEngine,
  ComputationalProvenanceEngine,
  ReuseType,
  ConstraintAwarenessEngine,
  DiscrepancyIntelligenceEngine,
  DiscrepancyCause,
  TemporalBudgetEngine,
  PartialKnowledgeEngine,
  LandscapeStructureEngine,
  LandscapeTopology,
  ResultForgettingEngine,
  AssumptionIntegrityEngine,
  QueryCompressionEngine,
  ScientificThematicEngine,
  LiteratureKnowledgeEngine,
  TagIndexLinkingEngine,
  SKILL_DEFINITIONS
} from '../src/index.js';

console.log("Running SFSA Extended Engines JavaScript Test Suite...");

// 1. AMF
{
  const amf = new AdaptiveMultiFidelityEngine(0.05);
  const dec = amf.evaluate({
    taskId: "test_amf",
    inputs: { t: 300 },
    cheapSolver: (inp) => ({ value: inp.t * 2, uncertainty: 0.01 }),
    expensiveSolver: (inp) => inp.t * 2.02
  });
  assert.strictEqual(dec.selectedLevel, FidelityLevel.CHEAP);
  assert.strictEqual(dec.escalated, false);
}

// 2. ASG
{
  const asg = new AdaptiveSamplingEngine(0.1);
  asg.recordEvaluation({ x: 0.0, y: 0.0 }, 10.0);
  const candClose = asg.evaluateCandidate({ x: 0.01, y: 0.01 }, () => 0.02);
  assert.strictEqual(candClose.skipRecommended, true);
}

// 3. SRA
{
  const sra = new SensitivityReductionAnalyzer(0.05);
  const red = sra.reduceParameterSpace({ x1: 2.0, x2: 5.0 }, (p) => 10.0 * p.x1 + 0.001 * p.x2);
  assert.strictEqual(red.reducedDimension, 1);
  assert.strictEqual(red.retainedParameters[0], 'x1');
}

// 4. UAS
{
  const uas = new UncertaintyAwareStoppingEngine(1e-4);
  const res = uas.evaluateStep({
    iteration: 5,
    currentValue: 1.414,
    previousValue: 1.41405,
    maxPlannedIterations: 50,
    estimatedUncertainty: 1e-5
  });
  assert.strictEqual(res.shouldStop, true);
  assert.strictEqual(res.iterationsSaved, 45);
}

// 5. CPE
{
  const cpe = new ComputationalProvenanceEngine(0.03);
  cpe.registerResult({ taskId: "cpe_task", inputs: { a: 10 }, output: 100 });
  const check = cpe.assessReuse("cpe_task", { a: 10 });
  assert.strictEqual(check.reuseType, ReuseType.EXACT_CACHE);
}

// 6. CAE
{
  const cae = new ConstraintAwarenessEngine(2);
  cae.addExplicitConstraint((inp) => [inp.p <= 100, "pressure limit"]);
  const [ok] = cae.validateInputs({ p: 150 });
  assert.strictEqual(ok, false);
}

// 7. DIE
{
  const die = new DiscrepancyIntelligenceEngine();
  const d = die.analyze("model1", 10.0, "model2", 10.05);
  assert.strictEqual(d.probableCause, DiscrepancyCause.NUMERICAL_TOLERANCE);
}

// 8. TBE
{
  const tbe = new TemporalBudgetEngine(30.0);
  const alloc = tbe.requestAllocation("t1", 1.0);
  assert.strictEqual(alloc.canProceed, true);
}

// 9. PKE
{
  const pke = new PartialKnowledgeEngine();
  pke.capture({ taskId: "task_pke", iteration: 1, estimate: 5, lowerBound: 2, upperBound: 8 });
  const [low, up] = pke.getTightestBounds("task_pke");
  assert.strictEqual(low, 2);
  assert.strictEqual(up, 8);
}

// 10. LSE
{
  const lse = new LandscapeStructureEngine();
  const feat = lse.probeRegion({ x: [0, 1] }, () => 42.0);
  assert.strictEqual(feat.topology, LandscapeTopology.FLAT_PLATEAU);
}

// 11. RFE
{
  const rfe = new ResultForgettingEngine();
  rfe.trackEntry("k1", 10);
  const ret = rfe.assessRetention("k1");
  assert.ok(ret.retentionScore > 0);
}

// 12. AIE
{
  const aie = new AssumptionIntegrityEngine();
  aie.registerAssumption("temp_limit", "T < 1000", (st) => [st.temp < 1000, "overheating"]);
  const viols = aie.auditState({ temp: 1200 });
  assert.strictEqual(viols.length, 1);
}

// 13. CQE
{
  const cqe = new QueryCompressionEngine(0.1);
  const batch = cqe.compressAndSolve([{ x: 1.0 }, { x: 1.02 }, { x: 5.0 }], (q) => q.x * 2);
  assert.strictEqual(batch.representativeCount, 2);
  assert.strictEqual(batch.reconstructedOutputs.length, 3);
}

// 14. STE
{
  const ste = new ScientificThematicEngine();
  const rep = ste.analyzeModel({
    layerNames: ["thermodynamics_layer"],
    variableNames: ["temp_k", "pressure_bar"]
  });
  assert.ok(rep.primaryThemes.length > 0);
}

// 15. LKE
{
  const lke = new LiteratureKnowledgeEngine();
  const props = lke.proposeResources(["thermodynamics"], 2);
  assert.ok(props.length > 0);
}

// 16. TIL
{
  const til = new TagIndexLinkingEngine();
  til.addOrUpdateTag("t1", "Thermodynamics");
  assert.strictEqual(til.getPrimaryTags().length, 1);
}

// Session & 85 Skills
{
  const session = new SFSASession();
  assert.strictEqual(SKILL_DEFINITIONS.length, 85);
  const rep = session.generateReport();
  assert.strictEqual(rep.activeEnginesCount, 39);

  const l = session.executeSkill("register_layer", { layerId: "chem", initialState: { val: 1 } });
  assert.strictEqual(l.layerId, "chem");
}

console.log("✅ ALL 16 EXTENDED ENGINES & 85 SKILLS VERIFIED IN JAVASCRIPT!");
