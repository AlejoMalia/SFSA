/** Regression tests for core-engine defects found during the framework diagnosis (JavaScript). */
import test from 'node:test';
import assert from 'node:assert/strict';
import { SFSASession, ICREngine, TransitionStep } from '../src/index.js';
import { SourceType } from '../src/lke.js';

test('ICR never fabricates a zero result', () => {
  const icr = new ICREngine();
  const { result, profile } = icr.optimizeAndExecute({ taskId: 'cos0', inputParams: { x: 0.0 }, exactSolver: (p) => Math.cos(p.x) });
  assert.equal(result, 1.0);
  assert.ok(profile.optimizationsApplied.some(o => o.includes('DenseFallback')));
});

test('ICR zero pruning only with a declared answer; shortcut failures fall back', () => {
  const icr = new ICREngine();
  const z = icr.optimizeAndExecute({ taskId: 'lin', inputParams: { x: 0.0 }, exactSolver: () => 99, zeroInputResult: 0.0, estimatedDenseOps: 100 });
  assert.equal(z.result, 0.0);
  assert.equal(z.profile.executedOperations, 1);
  assert.equal(icr.totalOperationsAvoided, 99);
  const a = icr.optimizeAndExecute({ taskId: 't', inputParams: { x: 1.0 }, exactSolver: () => 7.0, analyticalShortcut: () => { throw new Error('x'); } });
  assert.equal(a.result, 7.0);
  assert.ok(a.profile.optimizationsApplied.some(o => o.includes('ShortcutRejected')));
  assert.equal(icr.optimizeAndExecute({ taskId: 't', inputParams: { x: 1.0 }, exactSolver: () => 7.0, analyticalShortcut: () => NaN }).result, 7.0);
  const b = icr.optimizeAndExecute({ taskId: 't', inputParams: { x: 1.0 }, exactSolver: () => 7.0, estimatedDenseOps: 0 });
  assert.equal(b.result, 7.0);
  assert.equal(b.profile.reductionPercentage, 0.0);
});

test('FLN rejects cycles at connect time and stays updatable', () => {
  const s = new SFSASession({ name: 't' });
  for (const n of 'abc') s.registerLayer(n, {});
  s.connectLayers('a', 'b', () => ({}));
  s.connectLayers('b', 'c', () => ({}));
  assert.throws(() => s.connectLayers('c', 'a', () => ({})), /Cyclic/);
  assert.throws(() => s.connectLayers('a', 'a', () => ({})), /Cyclic/);
  assert.deepEqual(s.updateLayer('a', { k: 1 }), { a: 2, b: 2, c: 2 });
});

test('FLN update is atomic when a transformer fails', () => {
  const s = new SFSASession({ name: 't' });
  s.registerLayer('src', { v: 1.0 });
  s.registerLayer('mid', { w: 1.0 });
  s.registerLayer('dst', { z: 1.0 });
  s.connectLayers('src', 'mid', (a) => ({ w: a.v * 2 }));
  s.connectLayers('mid', 'dst', (a) => { if (a.w === 6.0) throw new Error('singular'); return { z: 1 / (a.w - 6.0) }; });
  assert.throws(() => s.updateLayer('src', { v: 3.0 }), /singular/);
  assert.equal(s.fln.getLayer('src').state.v, 1.0);
  assert.equal(s.fln.getLayer('mid').state.w, 1.0);
  assert.deepEqual(['src', 'mid', 'dst'].map(n => s.fln.getLayer(n).version), [1, 1, 1]);
});

test('FLN diamond propagates once per layer', () => {
  const s = new SFSASession({ name: 't' });
  for (const n of ['top', 'l', 'r', 'bottom']) s.registerLayer(n, { v: 0 });
  s.connectLayers('top', 'l', (a) => ({ v: a.v + 1 }));
  s.connectLayers('top', 'r', (a) => ({ v: a.v + 10 }));
  s.connectLayers('l', 'bottom', (a) => ({ from_l: a.v }));
  s.connectLayers('r', 'bottom', (a) => ({ from_r: a.v }));
  const v = s.updateLayer('top', { v: 5 });
  assert.equal(v.bottom, 2);
  assert.deepEqual(s.fln.getLayer('bottom').state, { v: 0, from_l: 6, from_r: 15 });
});

test('TBE rejects invalid requests', () => {
  const s = new SFSASession({ name: 't' });
  assert.throws(() => s.tbe.requestAllocation('t', -1.0));
  assert.throws(() => s.tbe.requestAllocation('t', 1.0, 0.0));
  assert.ok(s.tbe.requestAllocation('t', 1.0).allocatedSeconds > 0);
});

test('AIE and CAE fail closed on broken rules', () => {
  const s = new SFSASession({ name: 't' });
  s.aie.registerAssumption('bad', 'Broken', () => { throw new Error('nope'); }, 'FAIL_STOP');
  const viol = s.aie.auditState({});
  assert.ok(viol.length === 1 && viol[0].diagnosticMessage.includes('could not be evaluated'));
  s.cae.addExplicitConstraint(() => { throw new Error('nope'); });
  const [ok, why] = s.cae.validateInputs({});
  assert.ok(!ok && why.includes('raised'));
});

test('RTE reports singularities as fragile instead of crashing', () => {
  const s = new SFSASession({ name: 't' });
  const rep = s.rte.stressTest({ a: 2.0 }, (p) => { if (Math.abs(p.a - 2.0) > 0) throw new Error('singular'); return 1.0; });
  assert.equal(rep.isRobust, false);
  assert.ok(rep.diagnosticDetails.some(d => d.includes('Singularity')));
  assert.equal(s.rte.stressTest({ a: 2.0 }, (p) => p.a * 3.0).isRobust, true);
});

test('LKE source type filter applies before the limit', () => {
  const s = new SFSASession({ name: 't' });
  const out = s.lke.proposeResources(['physics'], 2, [SourceType.CODE_METHODS]);
  assert.ok(out.length > 0 && out.every(p => p.sourceType === SourceType.CODE_METHODS));
});

test('MATE projectTrajectory is a real check', () => {
  const s = new SFSASession({ name: 't' });
  assert.equal(s.mate.projectTrajectory('t', { x: 1 }, [(i) => i.x > 0]), true);
  assert.equal(s.mate.projectTrajectory('t', { x: -1 }, [(i) => i.x > 0]), false);
  assert.equal(s.mate.projectTrajectory('t', {}, [(i) => { if (i.missing === undefined) throw new Error('m'); return true; }]), false);
  assert.equal(s.mate.projectTrajectory('t', { x: 1 }, [() => [false, 'no']]), false);
});

test('session Pareto / projection wrappers work', () => {
  const s = new SFSASession({ name: 't' });
  s.registerLayer('a', { x: 1.0, y: 2.0 });
  s.registerLayer('b', { x: 1.0, y: 2.0 });
  assert.ok(Math.abs(s.projectLayers('a', 'b').normalizedVectorDistance) < 1e-9);
  assert.throws(() => s.projectLayers('a', 'ghost'));
  s.path.registerStep(new TransitionStep({ stepId: 'up', name: 'up', cost: 1, duration: 1, feasibility: 1, deltaState: { T: 10 } }));
  const paths = s.findParetoPathways({ T: 0.0 }, { T: 30.0 });
  assert.ok(paths.length > 0);
  assert.equal(paths[0].steps.length, 3);
});

test('RME seal covers nested fields and verifies', () => {
  const s = new SFSASession({ name: 't' });
  const m1 = s.rme.generateManifest('x', 39, { note: 'a' });
  assert.ok(s.rme.verifyManifest(m1));
  const tampered = { ...m1, environmentMetadata: { note: 'b' } };
  assert.equal(s.rme.verifyManifest(tampered), false);
  const tampered2 = { ...m1, platformInfo: { ...m1.platformInfo, machine: 'other' } };
  assert.equal(s.rme.verifyManifest(tampered2), false);
});

test('CAE cut is revoked by feasible points in the blocked region', async () => {
  const { ConstraintAwarenessEngine } = await import('../src/cae.js');
  const cae = new ConstraintAwarenessEngine(3);
  for (const p of [10.0, 11.0, 12.0]) cae.recordInfeasibility({ p });
  assert.equal(cae.inferredConstraints[0].conditionOp, '>=');
  assert.equal(cae.validateInputs({ p: 50.0 })[0], false);
  assert.equal(cae.validateInputs({ p: 5.0 })[0], true);
  cae.recordFeasibility({ p: 40.0 });
  assert.equal(cae.inferredConstraints[0].conditionOp, '<=');
  assert.equal(cae.validateInputs({ p: 50.0 })[0], true);
  assert.equal(cae.validateInputs({ p: 5.0 })[0], false);
  cae.recordFeasibility({ p: 2.0 });
  assert.deepEqual(cae.inferredConstraints, []);
});

test('CAE makes no cut when failures interleave with successes; lower cut works', async () => {
  const { ConstraintAwarenessEngine } = await import('../src/cae.js');
  const a = new ConstraintAwarenessEngine(3);
  for (const p of [1.0, 5.0, 9.0]) a.recordFeasibility({ p });
  for (const p of [3.0, 7.0, 8.0]) a.recordInfeasibility({ p });
  assert.deepEqual(a.inferredConstraints, []);
  const b = new ConstraintAwarenessEngine(3);
  for (const t of [-5.0, -20.0, -1.0]) b.recordInfeasibility({ t });
  b.recordFeasibility({ t: 300.0 });
  assert.equal(b.inferredConstraints[0].conditionOp, '<=');
  assert.equal(b.validateInputs({ t: -3.0 })[0], false);
  assert.equal(b.validateInputs({ t: 0.5 })[0], true);
});

test('compute feeds CAE with feasible points', () => {
  const s = new SFSASession({ name: 't' });
  s.compute({ taskId: 'c', inventory: { x: 1.0 }, solver: (i) => i.x });
  assert.deepEqual(s.cae.feasibleHistory, [{ x: 1.0 }]);
});

test('compute approximate reuse is opt-in and version-bound', () => {
  const s = new SFSASession({ name: 't' });
  const calls = [];
  const solver = (i) => { calls.push(i.x); return i.x * 2; };
  s.compute({ taskId: 'r', inventory: { x: 100.0 }, solver });
  assert.equal(s.compute({ taskId: 'r', inventory: { x: 100.5 }, solver }).value, 201.0);
  assert.equal(calls.length, 2);
  const res = s.compute({ taskId: 'r', inventory: { x: 100.4 }, solver, approximateReuseTolerance: 0.01 });
  assert.ok(res.cached);
  assert.equal(calls.length, 2);
  assert.equal(s.compute({ taskId: 'r', inventory: { x: 150.0 }, solver, approximateReuseTolerance: 0.01 }).value, 300.0);
  s.mate.invalidate('v2');
  const before = calls.length;
  s.compute({ taskId: 'r', inventory: { x: 100.4 }, solver, approximateReuseTolerance: 0.01 });
  assert.equal(calls.length, before + 1);
});

test('TXE transferred cut semantics', async () => {
  const { TransferExperienceEngine } = await import('../src/txe.js');
  const a = new SFSASession({ name: 'A' });
  a.cae.minSupport = 2;
  a.cae.recordInfeasibility({ temperature: 900.0 });
  a.cae.recordInfeasibility({ temperature: 950.0 });
  a.registerLayer('heat', { temp: 1 }, 'Thermal Dynamics');
  const txe = new TransferExperienceEngine();
  txe.captureSessionExperience(a);
  const b = new SFSASession({ name: 'B' });
  assert.ok(txe.warmStartSession(b, ['Thermal Dynamics']) >= 1);
  assert.equal(b.cae.validateInputs({ temperature: 1000.0 })[0], false);
  assert.equal(b.cae.validateInputs({ temperature: 300.0 })[0], true);
  assert.equal(b.cae.validateInputs({ other: 1.0 })[0], true);
});

test('version is consistent everywhere', async () => {
  const fs = await import('node:fs');
  const { VERSION } = await import('../src/index.js');
  const pkg = JSON.parse(fs.readFileSync(new URL('../package.json', import.meta.url), 'utf-8'));
  assert.equal(VERSION, pkg.version);
  assert.equal(VERSION, '0.2.0');
});
