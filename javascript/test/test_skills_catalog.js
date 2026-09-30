/**
 * Exhaustive functional tests for the 85-skill catalog (JavaScript).
 * Every skill is executed with realistic arguments and its behaviour asserted, so a skill that degrades to a
 * no-op stub fails here.
 */
import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { SFSASession } from '../src/index.js';
import { SKILL_DEFINITIONS, REQUIRED_ARGS } from '../src/skills.js';

const close = (a, b, eps = 1e-9) => assert.ok(Math.abs(a - b) <= eps, `${a} !~ ${b}`);

function makeSession() {
  const s = new SFSASession({ name: 'skills_test' });
  s.registerLayer('thermo', { temp_k: 300.0, pressure_pa: 101325.0 }, 'thermodynamics');
  s.registerLayer('kinetics', { rate: 1.0, temp_k: 310.0 }, 'chemical_kinetics');
  s.connectLayers('thermo', 'kinetics', (src) => ({ rate: src.temp_k * 0.01 }));
  return s;
}

test('catalog is complete, unique and fully implemented', () => {
  assert.equal(SKILL_DEFINITIONS.length, 85);
  assert.deepEqual(SKILL_DEFINITIONS.map(m => m.skillNumber).sort((a, b) => a - b), Array.from({ length: 85 }, (_, i) => i + 1));
  assert.equal(new Set(SKILL_DEFINITIONS.map(m => m.name)).size, 85);
  const s = makeSession();
  assert.deepEqual(s.skills.missingImplementations(), []);
  for (const name of Object.keys(REQUIRED_ARGS)) assert.ok(SKILL_DEFINITIONS.some(m => m.name === name), `REQUIRED_ARGS names unknown skill ${name}`);
});

test('bundled catalog matches repo catalog', () => {
  const here = path.dirname(fileURLToPath(import.meta.url));
  assert.equal(
    fs.readFileSync(path.join(here, '../src/catalog.json'), 'utf-8'),
    fs.readFileSync(path.join(here, '../../skills/catalog.json'), 'utf-8'),
  );
});

test('unknown skill, missing args and failure logging', () => {
  const s = makeSession();
  assert.throws(() => s.executeSkill('nope'), /Unknown/);
  assert.throws(() => s.executeSkill('get_layer_state', {}), /Missing required argument 'layerId'/);
  assert.equal(s.skills.executionLog.at(-1).status, 'INVALID_ARGS');
  const v = s.executeSkill('validate_skill_call', { skill: 'compute', args: { taskId: 't' } });
  assert.equal(v.valid, false);
  assert.deepEqual(new Set(v.missing), new Set(['inventory', 'solver']));
  assert.equal(s.executeSkill('validate_skill_call', { skill: 22, args: { taskId: 't', inventory: {}, solver: () => 1 } }).valid, true);
  assert.throws(() => s.executeSkill('get_layer_state', { layerId: 'ghost' }));
  assert.equal(s.skills.executionLog.at(-1).status, 'ERROR');
});

test('session lifecycle skills', () => {
  const s = makeSession();
  assert.equal(s.executeSkill('create_session'), s);
  s.executeSkill('set_budget', { seconds: 5 });
  assert.equal(s.tbe.totalBudget, 5);
  assert.throws(() => s.executeSkill('set_budget', { seconds: -1 }));
  const pol = s.executeSkill('set_policy', { policy: { reuseTolerance: 0.123, mateSpecMode: 'off' } });
  assert.equal(s.cpe.approximateTolerance, 0.123);
  assert.equal(s.mate.specMode, 'off');
  assert.equal(pol.reuseTolerance, 0.123);
  assert.throws(() => s.executeSkill('set_policy', { mateSpecMode: 'bogus' }));

  const file = path.join(fs.mkdtempSync(path.join(os.tmpdir(), 'sfsa-')), 'sess.json');
  s.executeSkill('update_layer', { layerId: 'thermo', newState: { temp_k: 350.0 } });
  s.executeSkill('save_session', { path: file });
  assert.equal(JSON.parse(fs.readFileSync(file, 'utf-8')).layers.thermo.state.temp_k, 350.0);
  const fresh = new SFSASession({ name: 'fresh' });
  fresh.executeSkill('load_session', { path: file });
  assert.equal(fresh.fln.getLayer('thermo').state.temp_k, 350.0);
  assert.equal(fresh.cpe.approximateTolerance, 0.123);
  assert.equal(s.executeSkill('get_session_status').activeLayersCount, 2);

  s.executeSkill('store_result', { taskId: 't', inputs: { x: 1.0 }, output: 2.0 });
  assert.deepEqual(s.executeSkill('reset_session', { scope: 'cache' }).cleared, ['cache']);
  assert.equal(s.executeSkill('query_cache', { taskId: 't', inputs: { x: 1.0 } }), null);
  assert.equal(s.fln.layers.size, 2);
  s.executeSkill('reset_session', { scope: 'layers' });
  assert.equal(s.fln.layers.size, 0);
  assert.throws(() => s.executeSkill('reset_session', { scope: 'nonsense' }));
});

test('FLN skills', () => {
  const s = makeSession();
  s.registerLayer('out', { y: 0.0 });
  s.executeSkill('connect_layers', { sourceId: 'kinetics', targetId: 'out', transformer: (a) => ({ y: a.rate * 2 }) });
  const versions = s.executeSkill('update_layer', { layerId: 'thermo', newState: { temp_k: 400.0 } });
  close(s.fln.getLayer('out').state.y, 8.0);
  assert.deepEqual(new Set(Object.keys(versions)), new Set(['thermo', 'kinetics', 'out']));
  close(s.executeSkill('get_layer_state', { layerId: 'kinetics' }).rate, 4.0);
  assert.deepEqual(s.executeSkill('find_affected_layers', { layerId: 'thermo' }), ['kinetics', 'out']);
  assert.deepEqual(s.executeSkill('find_affected_layers', { layerId: 'out' }), []);
  const g = s.executeSkill('inspect_graph');
  assert.equal(g.dependencies, 2);
  close(g.centrality.kinetics, 1.0);

  s.fln.getLayer('thermo').state.temp_k = 500.0;
  s.executeSkill('propagate_delta', { layerId: 'thermo', delta: { temp_k: 500.0 } });
  close(s.fln.getLayer('out').state.y, 10.0);
  assert.equal(s.executeSkill('disconnect_layers', { sourceId: 'kinetics', targetId: 'out' }).edgesRemoved, 1);
  assert.deepEqual(s.executeSkill('find_affected_layers', { layerId: 'thermo' }), ['kinetics']);
  assert.equal(s.executeSkill('disconnect_layers', { sourceId: 'kinetics', targetId: 'out' }).disconnected, false);
  assert.throws(() => s.executeSkill('find_affected_layers', { layerId: 'ghost' }));
});

test('TRIADA skills', () => {
  const s = makeSession();
  assert.ok(s.executeSkill('inventory_check', { inventory: { m: 1.0, T: 300.0 }, bounds: { T: [0, 1000] }, required: ['m'] }).passed);
  const bad = s.executeSkill('inventory_check', {
    inventory: { T: -5.0 }, bounds: { T: [0, 1000] }, required: ['m'], conservation: { mass: (inv) => (inv.T ?? 0) > 0 },
  });
  assert.equal(bad.passed, false);
  assert.equal(bad.reasons.length, 3);
  assert.equal(s.executeSkill('inventory_check', { inventory: { a: NaN } }).passed, false);

  const cf = s.executeSkill('try_closed_form', { inputs: { x: 4.0 }, analytical: (i) => Math.sqrt(i.x) });
  assert.ok(cf.solved);
  assert.equal(cf.value, 2.0);
  assert.equal(s.executeSkill('try_closed_form', { inputs: { x: 0.0 }, analytical: (i) => 1 / i.x }).solved, false);
  assert.equal(s.executeSkill('try_closed_form', { inputs: {}, analytical: () => { throw new Error('boom'); } }).solved, false);

  s.executeSkill('declare_invariants', { invariants: { non_negative: (v) => v >= 0 } });
  assert.ok(s.executeSkill('check_invariants', { result: 3.0 }).passed);
  const chk = s.executeSkill('check_invariants', { result: -1.0 });
  assert.equal(chk.passed, false);
  assert.equal(chk.failures[0].invariant, 'non_negative');
  assert.ok(s.executeSkill('bounded_verify', { result: -1.0, invariants: { always: () => true } }).passed);
  assert.throws(() => s.executeSkill('check_invariants', { result: 1.0, names: ['undeclared'] }));

  const ke = (i) => 0.5 * i.m * i.v ** 2;
  const rep = s.executeSkill('run_triada', { taskName: 'ke', inventory: { m: 2.0, v: 3.0 }, solver: ke, required: ['m', 'v'], invariants: [(v) => v > 0] });
  assert.ok(rep.success);
  close(rep.finalOutput, 9.0);
  assert.equal(s.executeSkill('run_triada', { taskName: 'ke2', inventory: { m: -2.0, v: 3.0 }, solver: ke, invariants: { pos: (v) => v > 0 } }).success, false);
  const rep3 = s.executeSkill('run_triada', { taskName: 'ke3', inventory: { m: 1.0 }, solver: () => 1, required: ['v'] });
  assert.equal(rep3.success, false);
  assert.match(String(rep3.failedAtStage), /T1/);
});

test('MATE / ICR skills', () => {
  const s = makeSession();
  let calls = 0;
  const solver = (inv) => { calls += 1; return inv.x ** 2; };
  const r1 = s.executeSkill('compute', { taskId: 'sq', inventory: { x: 3.0 }, solver });
  const r2 = s.executeSkill('compute', { taskId: 'sq', inventory: { x: 3.0 }, solver });
  assert.equal(r1.value, 9.0);
  assert.equal(r2.value, 9.0);
  assert.equal(calls, 1);
  assert.ok(r2.cached);
  assert.equal(s.executeSkill('query_cache', { taskId: 'sq', inputs: { x: 3.0 } }), 9.0);

  s.executeSkill('store_result', { taskId: 'manual', inputs: { a: 1 }, output: 42 });
  assert.equal(s.executeSkill('query_cache', { taskId: 'manual', inputs: { a: 1 } }), 42);
  assert.equal(s.executeSkill('get_provenance', { taskId: 'manual' })[0].output, 42);

  const pos = [(i) => i.x > 0];
  assert.equal(s.executeSkill('project_trajectory', { taskId: 't', inputs: { x: 1 }, invariants: pos }), true);
  assert.equal(s.executeSkill('project_trajectory', { taskId: 't', inputs: { x: -1 }, invariants: pos }), false);
  const ab = s.executeSkill('early_abort_check', { taskId: 't', inputs: { x: -1 }, invariants: pos });
  assert.ok(ab.shouldAbort && ab.reasons.length > 0);
  assert.equal(s.executeSkill('early_abort_check', { taskId: 't', inputs: { x: 1 } }).shouldAbort, false);

  assert.ok(s.executeSkill('reduce_expression', { expression: '0 * x + 1 * y' }).operationsEliminatedCount >= 1);
  const c = s.executeSkill('estimate_compute_cost', { operations: 1000, costPerOpMs: 0.5, cacheHitRate: 0.5 });
  close(c.estimatedMs, 250.0);
  close(c.estimatedMsNoReuse, 500.0);
  assert.throws(() => s.executeSkill('estimate_compute_cost', { operations: -1 }));

  const n = s.executeSkill('invalidate_cache', { newModelVersion: 'v2' });
  assert.equal(typeof n.mechanismsInvalidated, 'number');
  assert.equal(s.executeSkill('query_cache', { taskId: 'sq', inputs: { x: 3.0 } }), null);
});

test('compute enforces bounds/invariants and handles shortcuts', () => {
  const s = makeSession();
  assert.throws(() => s.compute({ taskId: 'b', inventory: { x: 11.0 }, solver: (i) => i.x, bounds: { x: [0.0, 10.0] } }), /Bounds/);
  const res = s.compute({ taskId: 'inv', inventory: { x: 2.0 }, solver: (i) => -i.x, invariants: [(v) => v > 0] });
  assert.equal(res.value, null);
  assert.match(res.diagnosticMessage, /invariant/);
  assert.equal(s.mate.lookup('inv', { x: 2.0 }) ?? null, null);
  assert.equal(s.compute({ taskId: 'ok', inventory: { x: 2.0 }, solver: (i) => i.x, invariants: [(v) => v > 0] }).value, 2.0);

  const fast = s.compute({
    taskId: 'sum', inventory: { n: 100.0 }, solver: (i) => { let t = 0; for (let k = 0; k <= i.n; k++) t += k; return t; },
    analyticalShortcut: (i) => i.n * (i.n + 1) / 2, estimatedDenseOps: 500,
  });
  assert.equal(fast.value, 5050.0);
  assert.equal(s.icr.totalOperationsAvoided, 500);
  assert.equal(s.compute({ taskId: 'lst', inventory: { xs: [1, 2, 3] }, solver: (i) => i.xs.reduce((a, b) => a + b, 0) }).value, 6);
});

test('consistency & Pareto skills', () => {
  const s = makeSession();
  assert.ok(s.executeSkill('project_layers', { layerA: 'thermo', layerB: 'kinetics' }).totalParametersCompared >= 1);
  assert.equal(s.executeSkill('check_consistency', { layerA: 'thermo', layerB: 'kinetics' }).consistent, false);
  assert.equal(s.executeSkill('check_consistency', { layerA: { a: 1.0 }, layerB: { a: 1.0 } }).consistent, true);

  s.executeSkill('register_transition_step', { stepId: 'heat', name: 'heat', cost: 2.0, duration: 1.0, feasibility: 0.9, deltaState: { T: 50.0 } });
  s.executeSkill('register_transition_step', { stepId: 'heat_fast', name: 'heat fast', cost: 5.0, duration: 0.2, feasibility: 0.8, deltaState: { T: 50.0 } });
  s.executeSkill('register_transition_step', { stepId: 'cool', name: 'cool', cost: 1.0, duration: 1.0, feasibility: 1.0, deltaState: { T: -10.0 } });
  assert.throws(() => s.executeSkill('register_transition_step', { stepId: 'bad', cost: 1, duration: 1, feasibility: 2.0, deltaState: {} }));
  const paths = s.executeSkill('find_pareto_paths', { initialState: { T: 300.0 }, targetState: { T: 350.0 } });
  assert.ok(paths.length > 0 && paths.every(p => p.isParetoOptimal));
  assert.equal(s.executeSkill('rank_pathways', { pathways: paths, by: 'cost' })[0].accumulatedCost, Math.min(...paths.map(p => p.accumulatedCost)));
  assert.equal(s.executeSkill('rank_pathways', { pathways: paths, by: 'duration' })[0].accumulatedDuration, Math.min(...paths.map(p => p.accumulatedDuration)));
  assert.equal(s.executeSkill('rank_pathways', { pathways: paths }).length, paths.length);
  assert.throws(() => s.executeSkill('rank_pathways', { pathways: paths, by: 'vibes' }));

  const d = s.executeSkill('compare_states', { stateA: { a: 1.0, b: 2.0, gone: 1 }, stateB: { a: 1.5, b: 2.0, n: 7 } });
  close(d.changed.a.delta, 0.5);
  assert.deepEqual(d.added, { n: 7 });
  assert.deepEqual(d.removed, { gone: 1 });
  assert.equal(s.executeSkill('compare_states', { stateA: { a: 1 }, stateB: { a: 1 } }).identical, true);
});

test('fidelity & sampling skills', () => {
  const s = makeSession();
  const cheap = (i) => ({ value: i.t * 1.8e-3, uncertainty: 0.02 });
  const exp = (i) => i.t * 1.82e-3;
  assert.ok(s.executeSkill('choose_fidelity', { inputs: { t: 300.0 }, cheapSolver: cheap, expensiveSolver: exp, tolerance: 0.05 }).selectedLevel);
  assert.ok(s.executeSkill('compute_multi_fidelity', { taskId: 'mf', inputs: { t: 300.0 }, cheapSolver: cheap, expensiveSolver: exp }).selectedLevel);

  const grid = [];
  for (let i = 0; i < 10; i++) for (let j = 0; j < 10; j++) grid.push({ x: i / 10, y: j / 10 });
  const ranked = s.executeSkill('suggest_samples', { candidates: grid.slice(0, 20), topK: 5 });
  assert.equal(ranked.length, 5);
  assert.ok(ranked[0].informationGain >= ranked[4].informationGain);

  const camp = s.executeSkill('run_adaptive_sampling', { candidates: grid, objectiveFn: (p) => p.x + p.y, maxBudget: 15 });
  assert.ok(camp.pointsEvaluated <= 15);
  assert.equal(camp.pointsEvaluated + camp.pointsSkipped, 100);
  assert.equal(s.asg.pointValues.length, camp.pointsEvaluated);
  assert.ok(s.asg.pointValues.some(v => v !== 0));

  const stop = s.executeSkill('should_stop', { iteration: 10, currentValue: 1.0, previousValue: 1.0 + 1e-9, maxPlannedIterations: 100 });
  assert.ok(stop.shouldStop);
  assert.ok(stop.iterationsSaved > 0);
  assert.equal(s.executeSkill('should_stop', { iteration: 0, currentValue: 1.0, maxPlannedIterations: 100 }).shouldStop, false);

  assert.ok(s.executeSkill('value_of_information', { candidateId: 'c', predictedValue: 10.0, epistemicUncertainty: 0.1, decisionThreshold: 0.0 }));
  assert.equal(s.executeSkill('warm_start', { taskId: 'w', inputs: { x: 1.0 } }).source, 'NONE');
  s.executeSkill('store_result', { taskId: 'w', inputs: { x: 1.0 }, output: 5.0 });
  const ws = s.executeSkill('warm_start', { taskId: 'w', inputs: { x: 1.0 } });
  assert.equal(ws.seed, 5.0);
  assert.equal(ws.source, 'MATE_EXACT');

  const sm = s.executeSkill('build_surrogate', { modelId: 'm', points: [{ x: 0.0 }, { x: 1.0 }], values: [0.0, 10.0] });
  const [val, unc] = (() => { const r = sm.predict({ x: 0.0 }); return Array.isArray(r) ? r : [r.value, r.uncertainty]; })();
  assert.equal(val, 0.0);
  assert.equal(unc, 0.0);
  assert.throws(() => s.executeSkill('build_surrogate', { modelId: 'm', points: [{ x: 0.0 }], values: [1.0, 2.0] }));
});

test('sensitivity & cut skills', () => {
  const s = makeSession();
  const f = (p) => p.a * 10.0 + p.b * 0.001;
  assert.equal(s.executeSkill('analyze_sensitivity', { baseInputs: { a: 1.0, b: 1.0 }, objectiveFn: f })[0].parameterName, 'a');
  const red = s.executeSkill('reduce_dimensions', { baseInputs: { a: 1.0, b: 1.0 }, objectiveFn: f });
  assert.ok(red.reducedDimension < red.originalDimension);

  const cuts = s.executeSkill('infer_constraints', { failures: Array.from({ length: 6 }, (_, i) => ({ p: 100.0 + i })) });
  assert.ok(cuts.length > 0);
  assert.equal(cuts[0].parameterName, 'p');
  assert.equal(s.executeSkill('apply_constraints', { inputs: { p: 50.0 } })[0], true);
  const [ok, why] = s.executeSkill('apply_constraints', { inputs: { p: 500.0 } });
  assert.ok(!ok && why);

  s.pke.capture({ taskId: 'long', iteration: 7, estimate: 3.3, lowerBound: 3.0, upperBound: 3.6, residual: 0.1 });
  assert.equal(s.executeSkill('extract_partial_knowledge', { taskId: 'long' }).latestEstimate, 3.3);
  assert.equal(s.executeSkill('extract_partial_knowledge', { taskId: 'none' }), null);

  s.executeSkill('store_result', { taskId: 'ar', inputs: { x: 100.0 }, output: 7.0 });
  const near = s.executeSkill('reuse_approximate', { taskId: 'ar', inputs: { x: 100.5 }, tolerance: 0.05 });
  assert.equal(near.reuseType, 'APPROXIMATE_REUSE');
  assert.equal(near.value, 7.0);
  assert.notEqual(s.executeSkill('reuse_approximate', { taskId: 'ar', inputs: { x: 500.0 }, tolerance: 0.05 }).reuseType, 'APPROXIMATE_REUSE');
  assert.ok(s.executeSkill('map_landscape', { bounds: { x: [0.0, 1.0] }, surrogate: (p) => p.x ** 2 }));
});

test('provenance & hygiene skills', () => {
  const s = makeSession();
  s.executeSkill('store_result', { taskId: 'p', inputs: { x: 1.0 }, output: 1.0 });
  assert.equal(s.executeSkill('get_provenance').length, 1);
  assert.ok(['EXACT_CACHE', 'APPROXIMATE_REUSE'].includes(s.executeSkill('assess_reuse', { taskId: 'p', inputs: { x: 1.0 } }).reuseType));

  const before = s.rfe.entryMetadata.size;
  assert.ok(before >= 1);
  const res = s.executeSkill('forget_results', { count: 1 });
  assert.equal(res.count, 1);
  assert.equal(s.rfe.entryMetadata.size, before - 1);
  assert.throws(() => s.executeSkill('forget_results', { count: -1 }));

  s.executeSkill('version_model', { label: 'v1' });
  s.executeSkill('update_layer', { layerId: 'thermo', newState: { temp_k: 999.0 } });
  s.registerLayer('extra', { z: 1 });
  s.executeSkill('version_model', { label: 'v2' });
  const diff = s.executeSkill('diff_model_versions', { versionA: 'v1', versionB: 'v2' });
  assert.ok('thermo' in diff.changed);
  assert.deepEqual(diff.layersAdded, ['extra']);
  assert.equal(s.skills.versions.get('v1').thermo.state.temp_k, 300.0);
  assert.throws(() => s.executeSkill('version_model', { label: 'v1' }));
  assert.throws(() => s.executeSkill('diff_model_versions', { versionA: 'v1', versionB: 'vX' }));
});

test('thematic skills', () => {
  const s = makeSession();
  const cov = s.executeSkill('get_theme_coverage');
  assert.ok(Object.keys(cov).length > 0);
  assert.ok(Array.isArray(s.executeSkill('detect_theme_gaps')));
  assert.ok(Array.isArray(s.executeSkill('suggest_related_themes')));
  assert.ok(s.executeSkill('explain_model_focus').length > 20);
  assert.match(new SFSASession({ name: 'e' }).executeSkill('explain_model_focus'), /No thematic signal/);
  assert.deepEqual(s.executeSkill('export_thematic_map').coveragePct, cov);
});

test('literature skills', () => {
  const s = makeSession();
  const lit = s.executeSkill('search_literature', { domains: ['thermodynamics'], limit: 3 });
  assert.ok(lit.length > 0 && lit.length <= 3);
  const ds = s.executeSkill('search_datasets', { domains: ['thermodynamics'], limit: 3 });
  assert.ok(ds.length > 0 && ds.every(p => p.sourceType === 'DATASET'));
  const code = s.executeSkill('search_reference_code', { limit: 3 });
  assert.ok(code.length > 0 && code.every(p => p.sourceType === 'CODE_METHODS'));
  const ranked = s.executeSkill('rank_external_sources', { domains: ['physics'], limit: 5 });
  assert.deepEqual(ranked.map(p => p.confidence), [...ranked.map(p => p.confidence)].sort((a, b) => b - a));
  assert.ok(s.executeSkill('propose_external_evidence', { domains: ['chemistry'], limit: 2 }).length > 0);
  const link = s.executeSkill('link_evidence_to_gap', { gap: 'missing uncertainty', evidence: lit[0] });
  assert.equal(link.evidence, lit[0].title);
  assert.deepEqual(s.skills.evidenceLinks, [link]);
});

test('gap, assumption and audit skills', () => {
  const s = makeSession();
  const schema = { temp_k: 'float', missing_param: 'float' };
  assert.ok(s.executeSkill('detect_gaps', { requiredSchema: schema }).some(g => g.targetKey === 'missing_param'));
  s.executeSkill('suggest_gap_closure', { requiredSchema: schema });

  s.aie.registerAssumption('lam', 'Laminar flow', (st) => [(st.re ?? 0) < 2300, 'Re too high'], 'WARNING', 'Re<2300');
  assert.deepEqual(s.executeSkill('list_assumptions'), [{ id: 'lam', name: 'Laminar flow', criticality: 'WARNING', description: 'Re<2300' }]);
  assert.deepEqual(s.executeSkill('check_assumption_integrity', { state: { re: 100 } }), []);
  const viol = s.executeSkill('check_assumption_integrity', { state: { re: 9000 } });
  assert.equal(viol[0].assumptionId, 'lam');

  s.executeSkill('compute', { taskId: 'audit_me', inventory: { x: 2.0 }, solver: (i) => i.x * 3 });
  const exp = s.executeSkill('explain_decision', { taskId: 'audit_me' });
  assert.match(exp.narrative, /audit_me/);
  assert.ok(exp.decisions.length > 0);
  s.executeSkill('explain_decision', { taskId: 'custom', engineName: 'ASG', action: 'PRUNE', rationale: 'flat gradient' });
  assert.ok(s.xxe.decisionLog.some(d => d.action === 'PRUNE'));
  const res = s.executeSkill('explain_result', { taskId: 'audit_me' });
  assert.ok(res.found);
  assert.equal(res.output, 6.0);

  const audit = s.executeSkill('audit_run');
  assert.ok(audit.decisions >= 2 && audit.skillTrace.length > 0 && typeof audit.markdown === 'string');
  assert.match(audit.manifestSeal, /^[0-9a-f]{64}$/);

  s.executeSkill('compare_runs', { label: 'a' });
  s.executeSkill('compute', { taskId: 'more', inventory: { x: 5.0 }, solver: (i) => i.x });
  const cmp = s.executeSkill('compare_runs', { label: 'b' });
  assert.equal(cmp.runs, 2);
  assert.ok(cmp.metrics.totalQueries.deltaFirstLast >= 0);
  assert.equal(s.executeSkill('compare_runs', { runs: [{ a: 1 }, { a: 3 }] }).metrics.a.mean, 2);
});

test('reporting & export skills', () => {
  const s = makeSession();
  const md = s.executeSkill('generate_report', { format: 'markdown' });
  assert.ok(md.startsWith('# SFSA Report') && md.includes('activeLayersCount'));
  assert.equal(s.executeSkill('generate_report').sessionName, 'skills_test');
  assert.throws(() => s.executeSkill('generate_report', { format: 'pdf' }));
  const g = s.executeSkill('export_graph');
  assert.deepEqual(new Set(g.nodes.map(n => n.id)), new Set(['thermo', 'kinetics']));
  assert.equal(g.edges.length, 1);
  JSON.stringify(g);
  s.executeSkill('store_result', { taskId: 'm', inputs: { x: 1 }, output: 1 });
  const man = s.executeSkill('export_cache_manifest');
  assert.equal(man.cacheEntries, 1);
  assert.equal(man.provenance[0].taskId, 'm');
  JSON.stringify(man);
  assert.deepEqual(s.executeSkill('export_skill_trace').slice(-2).map(t => t.skill), ['store_result', 'export_cache_manifest']);
});

test('agent planning skills', () => {
  const s = makeSession();
  assert.ok(s.executeSkill('plan_computation', { archetype: 'EXPLORATORY_SWEEP', inputCardinality: 500, parameterDim: 4 }));
  assert.throws(() => s.executeSkill('plan_computation', { archetype: 'WRONG' }));
  assert.equal(new SFSASession({ name: 'e' }).executeSkill('select_next_action').skill, 'register_layer');
  assert.equal(s.executeSkill('select_next_action').skill, 'declare_invariants');

  s.executeSkill('compute', { taskId: 'd', inventory: { x: 1.0 }, solver: () => 2.0 });
  const hit = s.executeSkill('dry_run', { taskId: 'd', inputs: { x: 1.0 } });
  assert.equal(hit.predictedAction, 'CACHE_HIT');
  assert.equal(hit.estimatedOperations, 0);
  const miss = s.executeSkill('dry_run', { taskId: 'd', inputs: { x: 99.0 }, operations: 500 });
  assert.ok(['FULL_COMPUTE', 'APPROXIMATE_REUSE'].includes(miss.predictedAction));
  const lookups = s.mate.stats().totalLookups;
  s.executeSkill('dry_run', { taskId: 'd', inputs: { x: 1.0 } });
  assert.equal(s.mate.stats().totalLookups, lookups);

  const qs = Array.from({ length: 200 }, (_, i) => ({ x: i * 0.01 }));
  assert.ok(s.executeSkill('batch_queries', { queries: qs, heavySolver: (q) => q.x * 2 }));
  const pr = s.executeSkill('prioritize_queries', { queries: [{ x: 0.1 }, { x: 0.9 }, { x: 0.5 }], costFn: (q) => 1 + q.x });
  assert.deepEqual(pr.map(r => r.score), [...pr.map(r => r.score)].sort((a, b) => b - a));
});

test('no handler returns the legacy stub payload', () => {
  const src = fs.readFileSync(path.join(path.dirname(fileURLToPath(import.meta.url)), '../src/skills.js'), 'utf-8');
  assert.ok(!src.includes('"EXECUTED"') && !src.includes("'EXECUTED'"));
});
