/**
 * sfsa.skills — The 85-Skills Execution Registry (JavaScript)
 * ============================================================
 * Reads and executes the centralized 85-Skills Catalog from `/skills/catalog.json`.
 * Single source of truth dispatcher across computational engines.
 *
 * Part of SFSA (Standard Framework for Scientific Advancement)
 * Author & Protocol Creator: Alejo Malia
 * License: CC BY 4.0
 */

import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { TransitionStep } from './path.js';
import { QueryArchetype } from './ore.js';
import { SourceType } from './lke.js';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

function loadCatalog() {
  const possiblePaths = [
    path.resolve(__dirname, './catalog.json'),
    path.resolve(__dirname, '../../skills/catalog.json'),
    path.resolve(process.cwd(), 'skills/catalog.json')
  ];
  const errors = [];
  for (const p of possiblePaths) {
    if (!fs.existsSync(p)) continue;
    try {
      const raw = JSON.parse(fs.readFileSync(p, 'utf-8'));
      return raw.map(item => ({
        skillNumber: item.skill_number,
        name: item.name,
        category: item.category,
        description: item.description,
        targetEngine: item.target_engine || 'session',
        targetMethod: item.target_method || 'execute'
      }));
    } catch (err) {
      errors.push(`${p}: ${err.message}`);
    }
  }
  throw new Error(
    `SFSA skills catalog not found or invalid. Searched: ${possiblePaths.join(', ')}` +
    (errors.length ? `; errors: ${errors.join('; ')}` : '')
  );
}

// Loaded dynamically from /skills/catalog.json
export const SKILL_DEFINITIONS = loadCatalog();

// Required arguments per skill. Drives validateSkillCall and the pre-dispatch check, so a missing argument
// raises one clear error instead of a TypeError from deep inside an engine.
export const REQUIRED_ARGS = {
  load_session: ['path'], save_session: ['path'],
  register_layer: ['layerId'], update_layer: ['layerId', 'newState'],
  connect_layers: ['sourceId', 'targetId', 'transformer'],
  disconnect_layers: ['sourceId', 'targetId'],
  get_layer_state: ['layerId'], propagate_delta: ['layerId'], find_affected_layers: ['layerId'],
  inventory_check: ['inventory'], try_closed_form: ['inputs', 'analytical'],
  bounded_verify: ['result'], run_triada: ['inventory', 'solver'],
  declare_invariants: ['invariants'], check_invariants: ['result'],
  compute: ['taskId', 'inventory', 'solver'],
  query_cache: ['taskId', 'inputs'], store_result: ['taskId', 'inputs', 'output'],
  project_trajectory: ['taskId', 'inputs'], early_abort_check: ['taskId', 'inputs'],
  reduce_expression: ['expression'],
  check_consistency: ['layerA', 'layerB'], project_layers: ['layerA', 'layerB'],
  register_transition_step: ['stepId', 'cost', 'duration', 'feasibility', 'deltaState'],
  find_pareto_paths: ['initialState', 'targetState'], rank_pathways: ['pathways'],
  compare_states: ['stateA', 'stateB'],
  choose_fidelity: ['inputs', 'cheapSolver', 'expensiveSolver'],
  compute_multi_fidelity: ['taskId', 'inputs', 'cheapSolver', 'expensiveSolver'],
  suggest_samples: ['candidates'], run_adaptive_sampling: ['candidates', 'objectiveFn'],
  should_stop: ['iteration', 'currentValue', 'maxPlannedIterations'],
  value_of_information: ['candidateId', 'predictedValue', 'epistemicUncertainty', 'decisionThreshold'],
  warm_start: ['taskId', 'inputs'], build_surrogate: ['modelId', 'points', 'values'],
  analyze_sensitivity: ['baseInputs', 'objectiveFn'], reduce_dimensions: ['baseInputs', 'objectiveFn'],
  infer_constraints: ['failures'], apply_constraints: ['inputs'],
  extract_partial_knowledge: ['taskId'], reuse_approximate: ['taskId', 'inputs'],
  map_landscape: ['bounds', 'surrogate'],
  assess_reuse: ['taskId', 'inputs'],
  diff_model_versions: ['versionA', 'versionB'],
  link_evidence_to_gap: ['gap', 'evidence'],
  check_assumption_integrity: ['state'],
  validate_skill_call: ['skill'], batch_queries: ['queries', 'heavySolver'],
  prioritize_queries: ['queries'],
};

const isNum = (v) => typeof v === 'number' && !Number.isNaN(v);
const clone = (o) => (o === undefined ? undefined : structuredClone(o));

export class SkillRegistry {
  constructor(session) {
    this.session = session;
    this.executionLog = [];
    // Session-scoped state owned by skills
    this.invariants = new Map();
    this.versions = new Map();
    this.policy = {};
    this.evidenceLinks = [];
    this.runSnapshots = [];
  }

  listSkills(category = null) {
    if (category) {
      return SKILL_DEFINITIONS.filter(s => s.category.toLowerCase() === category.toLowerCase());
    }
    return [...SKILL_DEFINITIONS];
  }

  /** Catalog skills with no `_skill_<name>` handler (must always be empty). */
  missingImplementations() {
    return SKILL_DEFINITIONS.filter(s => typeof this[`_skill_${s.name}`] !== 'function').map(s => s.name);
  }

  _meta(skill) {
    return typeof skill === 'number'
      ? SKILL_DEFINITIONS.find(s => s.skillNumber === skill)
      : SKILL_DEFINITIONS.find(s => s.name === skill);
  }

  validate(skill, args = {}) {
    const meta = this._meta(skill);
    if (!meta) return { valid: false, skill, missing: [], errors: [`Unknown SFSA skill: ${skill}`] };
    const missing = (REQUIRED_ARGS[meta.name] || []).filter(a => !(a in args) || args[a] === undefined);
    const errors = missing.map(m => `Missing required argument '${m}'`);
    return { valid: errors.length === 0, skill: meta.name, missing, errors };
  }

  execute(skillNameOrNumber, args = {}) {
    const meta = this._meta(skillNameOrNumber);
    if (!meta) throw new Error(`Unknown SFSA skill: ${skillNameOrNumber}`);

    const entry = { skill: meta.name, skillNumber: meta.skillNumber, args: Object.keys(args), timestamp: Date.now() };
    const check = this.validate(meta.name, args);
    if (!check.valid) {
      entry.status = 'INVALID_ARGS';
      this.executionLog.push(entry);
      throw new Error(`Skill '${meta.name}': ${check.errors.join('; ')}`);
    }
    const handler = this[`_skill_${meta.name}`];
    if (typeof handler !== 'function') {
      entry.status = 'NOT_IMPLEMENTED';
      this.executionLog.push(entry);
      throw new Error(`Skill '${meta.name}' has no implementation`);
    }
    let result;
    try {
      result = handler.call(this, args);
    } catch (err) {
      entry.status = 'ERROR';
      entry.error = `${err.name}: ${err.message}`;
      this.executionLog.push(entry);
      throw err;
    }
    entry.status = 'SUCCESS';
    this.executionLog.push(entry);
    return result;
  }

  // ------------------------------------------------------------------ helpers
  _layer(layerId) {
    const l = this.session.fln.getLayer(layerId);
    if (!l) throw new Error(`Layer '${layerId}' not found`);
    return l;
  }

  _layerState(ref) {
    return typeof ref === 'object' && ref !== null ? { ...ref } : { ...this._layer(ref).state };
  }

  _checkInvariants(value, names = null, extra = null) {
    const checks = new Map();
    if (names === null) {
      for (const [k, v] of this.invariants) checks.set(k, v);
    } else {
      for (const n of names) {
        if (!this.invariants.has(n)) throw new Error(`Invariant '${n}' is not declared`);
        checks.set(n, this.invariants.get(n));
      }
    }
    if (Array.isArray(extra)) extra.forEach((f, i) => checks.set(f.name || `inv_${i}`, f));
    else if (extra && typeof extra === 'object') for (const [k, f] of Object.entries(extra)) checks.set(k, f);

    const failures = [];
    for (const [name, fn] of checks) {
      let ok, why = '';
      try {
        const res = fn(value);
        if (Array.isArray(res)) { ok = Boolean(res[0]); why = res[1] || ''; } else ok = Boolean(res);
      } catch (err) {
        ok = false;
        why = `raised ${err.name}: ${err.message}`;
      }
      if (!ok) failures.push({ invariant: name, reason: why });
    }
    return { passed: failures.length === 0, checked: checks.size, failures };
  }

  _inventoryReport(inventory, bounds = {}, required = [], conservation = {}) {
    const reasons = [];
    for (const key of required || []) {
      if (!(key in inventory) || inventory[key] === null || inventory[key] === undefined) {
        reasons.push(`missing variable '${key}'`);
      }
    }
    for (const [key, val] of Object.entries(inventory)) {
      if (typeof val === 'number' && !Number.isFinite(val)) reasons.push(`non-finite value for '${key}'`);
    }
    for (const [key, range] of Object.entries(bounds || {})) {
      if (!(key in inventory)) reasons.push(`bounded variable '${key}' missing`);
      else if (isNum(inventory[key]) && !(inventory[key] >= range[0] && inventory[key] <= range[1])) {
        reasons.push(`'${key}'=${inventory[key]} outside [${range[0]}, ${range[1]}]`);
      }
    }
    for (const [name, fn] of Object.entries(conservation || {})) {
      try {
        if (!fn(inventory)) reasons.push(`conservation law '${name}' violated`);
      } catch (err) {
        reasons.push(`conservation law '${name}' raised ${err.name}: ${err.message}`);
      }
    }
    return { passed: reasons.length === 0, reasons };
  }

  // ============================================================ 1. Orchestration
  _skill_create_session() { return this.session; }

  _skill_load_session({ path: file }) {
    const data = JSON.parse(fs.readFileSync(file, 'utf-8'));
    const s = this.session;
    for (const [lid, info] of Object.entries(data.layers || {})) {
      const layer = s.fln.getLayer(lid) || s.registerLayer(lid, {}, info.name);
      for (const k of Object.keys(layer.state)) delete layer.state[k];
      Object.assign(layer.state, info.state || {});
      layer.version = info.version ?? layer.version;
    }
    Object.assign(this.policy, data.policy || {});
    this._applyPolicy(this.policy);
    if (data.budgetSeconds !== undefined) this._skill_set_budget({ seconds: data.budgetSeconds });
    for (const [k, v] of Object.entries(data.versions || {})) this.versions.set(k, v);
    return { loadedLayers: Object.keys(data.layers || {}).length, name: data.name };
  }

  _skill_save_session({ path: file }) {
    const s = this.session;
    const layers = {};
    for (const l of s.fln.layers.values()) layers[l.layerId] = { name: l.name, state: l.state, version: l.version };
    const data = {
      format: 'sfsa-session/1', name: s.name, layers, policy: this.policy,
      budgetSeconds: s.tbe.totalBudget, versions: Object.fromEntries(this.versions),
    };
    fs.writeFileSync(file, JSON.stringify(data, null, 2));
    return { saved: file, layers: Object.keys(layers).length };
  }

  _skill_reset_session({ scope = 'all' } = {}) {
    if (!['all', 'cache', 'history', 'layers'].includes(scope)) {
      throw new Error('scope must be one of: all, cache, history, layers');
    }
    const s = this.session;
    const cleared = [];
    if (scope === 'all' || scope === 'cache') {
      s.mate.clearCache();
      s.cpe.records.clear();
      s.rfe.entryMetadata.clear();
      cleared.push('cache');
    }
    if (scope === 'all' || scope === 'history') {
      s.xxe.decisionLog.length = 0;
      this.runSnapshots.length = 0;
      this.evidenceLinks.length = 0;
      cleared.push('history');
    }
    if (scope === 'all' || scope === 'layers') {
      s.fln._layers.clear();
      s.fln._dependencies.length = 0;
      cleared.push('layers');
    }
    return { cleared };
  }

  _skill_get_session_status() { return this.session.generateReport(); }

  _skill_set_budget({ seconds = 60.0 } = {}) {
    if (!isNum(seconds) || !(seconds > 0)) throw new Error('budget seconds must be a positive number');
    const tbe = this.session.tbe;
    tbe.totalBudget = seconds;
    tbe.spentSeconds = 0.0;
    tbe.startTimestamp = Date.now();
    return { budgetSeconds: tbe.totalBudget };
  }

  _applyPolicy(policy) {
    const s = this.session;
    if ('mateSpecMode' in policy) {
      if (!['off', 'idle_only', 'bounded', 'aggressive'].includes(policy.mateSpecMode)) {
        throw new Error('mateSpecMode must be off|idle_only|bounded|aggressive');
      }
      s.mate.specMode = policy.mateSpecMode;
    }
    if ('reuseTolerance' in policy) s.cpe.approximateTolerance = Number(policy.reuseTolerance);
    if ('stoppingTolerance' in policy) s.uas.targetTolerance = Number(policy.stoppingTolerance);
    if ('minSampleDistance' in policy) s.asg.minEuclideanDistance = Number(policy.minSampleDistance);
  }

  _skill_set_policy({ policy = null, ...rest } = {}) {
    const next = { ...(policy || {}), ...rest };
    this._applyPolicy(next);
    Object.assign(this.policy, next);
    return { ...this.policy };
  }

  // ============================================================ 2. FLN
  _skill_register_layer({ layerId, initialState, name }) {
    return this.session.registerLayer(layerId, initialState, name);
  }

  _skill_update_layer({ layerId, newState }) { return this.session.updateLayer(layerId, newState); }

  _skill_connect_layers({ sourceId, targetId, transformer, desc = '' }) {
    this.session.connectLayers(sourceId, targetId, transformer, desc);
    return { connected: true };
  }

  _skill_disconnect_layers({ sourceId, targetId }) {
    const removed = this.session.fln.disconnectLayers(sourceId, targetId);
    return { disconnected: removed > 0, edgesRemoved: removed };
  }

  _skill_inspect_graph() {
    const g = this.session.fln.exportGraph();
    const n = g.nodes.length;
    const degree = Object.fromEntries(g.nodes.map(x => [x.id, 0]));
    for (const e of g.edges) { degree[e.source] += 1; degree[e.target] += 1; }
    const centrality = Object.fromEntries(Object.entries(degree).map(([k, v]) => [k, n > 1 ? v / (n - 1) : 0.0]));
    return { layers: g.nodes.map(x => x.id), dependencies: g.edges.length, edges: g.edges, centrality };
  }

  _skill_get_layer_state({ layerId }) { return clone(this._layer(layerId).state); }

  _skill_propagate_delta({ layerId, delta = {} }) {
    this._layer(layerId);
    return this.session.fln.updateLayer(layerId, delta || {}, true);
  }

  _skill_find_affected_layers({ layerId }) { return this.session.fln.getDownstream(layerId); }

  // ============================================================ 3. TRIADA
  _skill_inventory_check({ inventory, bounds = {}, required = [], conservation = {}, taskId = 'inv_check' }) {
    return { ...this._inventoryReport(inventory, bounds, required, conservation), taskId, stage: 'T1_INVENTORY' };
  }

  _skill_try_closed_form({ inputs, analytical }) {
    let value;
    try {
      value = analytical(inputs);
    } catch (err) {
      return { solved: false, value: null, error: `${err.name}: ${err.message}`, stage: 'T2' };
    }
    const ok = value !== null && value !== undefined && !(typeof value === 'number' && !Number.isFinite(value));
    return { solved: ok, value: ok ? value : null, error: ok ? null : 'closed form returned no finite value', stage: 'T2' };
  }

  _skill_bounded_verify({ result, invariants = null, names = null }) {
    const rep = this._checkInvariants(result, invariants !== null ? (names || []) : names, invariants);
    rep.stage = 'T3';
    return rep;
  }

  _skill_run_triada({ inventory, solver, taskId = null, taskName = null, bounds = {}, required = [], invariants = null }) {
    const name = taskName || taskId || 'triada_task';
    const t1 = (inv) => { const r = this._inventoryReport(inv, bounds, required); return [r.passed, r.reasons]; };
    const t3 = (out) => {
      const r = this._checkInvariants(out, invariants ? [] : null, invariants);
      return [r.passed, r.failures.map(f => `${f.invariant}: ${f.reason}`)];
    };
    const report = this.session.triada.runPipeline({
      taskName: name, inventoryInput: inventory, t1InventoryValidator: t1,
      t2AnalyticalSolver: solver, t3ProjectionVerifier: t3,
    });
    this.session.xxe.recordDecision('TRIADA', report.success ? 'RUN_PIPELINE' : 'PIPELINE_FAILED',
      `Task '${name}' success=${report.success}`, 0.0, { taskId: name });
    return report;
  }

  _skill_declare_invariants({ invariants }) {
    const items = Array.isArray(invariants)
      ? invariants.map((f, i) => [f.name || `invariant_${this.invariants.size + i}`, f])
      : Object.entries(invariants);
    for (const [name, fn] of items) {
      if (typeof fn !== 'function') throw new Error(`Invariant '${name}' must be callable`);
      this.invariants.set(name, fn);
    }
    return { declared: [...this.invariants.keys()].sort() };
  }

  _skill_check_invariants({ result, names = null }) { return this._checkInvariants(result, names); }

  // ============================================================ 4. MATE / ICR
  _skill_compute(args) {
    const res = this.session.compute(args);
    this.session.xxe.recordDecision('MATE', res.cached ? 'CACHE_HIT' : 'COMPUTE',
      res.diagnosticMessage || res.diagnostic || 'computed', 0.0, { taskId: args.taskId });
    return res;
  }

  _skill_query_cache({ taskId, inputs }) {
    const v = this.session.mate.lookup(taskId, inputs);
    return v === undefined ? null : v;
  }

  _skill_store_result({ taskId, inputs, output, modelVersion = null, recomputeCostMs = 1.0 }) {
    const s = this.session;
    const key = s.mate.store(taskId, inputs, output);
    s.rfe.trackEntry(key, recomputeCostMs);
    return s.cpe.registerResult({ taskId, inputs, output, modelVersion: modelVersion || s.mate.modelVersion });
  }

  _skill_invalidate_cache({ newModelVersion = null } = {}) {
    const mate = this.session.mate;
    const version = newModelVersion || `${mate.modelVersion}+`;
    const count = mate.invalidate(version);
    this.session.cpe.records.clear();
    return { modelVersion: version, mechanismsInvalidated: count };
  }

  _skill_project_trajectory({ taskId, inputs, invariants = [] }) {
    return this.session.mate.projectTrajectory(taskId, inputs, invariants || []);
  }

  _skill_early_abort_check({ taskId, inputs, invariants = [], bounds = {} }) {
    const [okCae, reason] = this.session.cae.validateInputs(inputs);
    const inv = this._inventoryReport(inputs, bounds);
    const feasible = this.session.mate.projectTrajectory(taskId, inputs, invariants || []);
    const reasons = [...(okCae ? [] : [reason]), ...inv.reasons, ...(feasible ? [] : ['trajectory invariant violated'])];
    if (reasons.length > 0) this.session.mate.recordEarlyAbort();
    return { shouldAbort: reasons.length > 0, reasons };
  }

  _skill_reduce_expression({ expression }) { return this.session.sye.simplify(expression); }

  _skill_estimate_compute_cost({ operations = null, gridPoints = null, costPerOpMs = 0.001, cacheHitRate = null } = {}) {
    const ops = operations ?? gridPoints ?? 1000;
    if (ops < 0 || costPerOpMs < 0) throw new Error('operations and costPerOpMs must be non-negative');
    let rate = cacheHitRate;
    if (rate === null) {
      const st = this.session.mate.stats();
      rate = st.totalLookups ? st.cacheHits / st.totalLookups : 0.0;
    }
    rate = Math.min(Math.max(rate, 0.0), 1.0);
    const effective = ops * (1.0 - rate);
    return {
      operations: ops, estimatedMsNoReuse: ops * costPerOpMs, cacheHitRate: rate,
      effectiveOperations: effective, estimatedMs: effective * costPerOpMs,
    };
  }

  // ============================================================ 5. Consistency & Pareto
  _skill_check_consistency({ layerA, layerB, knownBounds = {} }) {
    const rep = this.session.projector.projectAndIntersect({
      layerAId: typeof layerA === 'string' ? layerA : 'layer_a', layerAState: this._layerState(layerA),
      layerBId: typeof layerB === 'string' ? layerB : 'layer_b', layerBState: this._layerState(layerB),
      knownBounds,
    });
    return {
      consistent: rep.inconsistencies.length === 0, inconsistencies: rep.inconsistencies,
      distance: rep.normalizedVectorDistance, report: rep,
    };
  }

  _skill_project_layers({ layerA, layerB }) { return this.session.projectLayers(layerA, layerB); }

  _skill_register_transition_step({ step = null, stepId, name = null, cost = 0, duration = 0, feasibility = 1.0, deltaState = {} }) {
    let st = step;
    if (!st) {
      if (!(feasibility >= 0 && feasibility <= 1)) throw new Error('feasibility must be in [0, 1]');
      st = new TransitionStep({ stepId, name: name || stepId, cost, duration, feasibility, deltaState: { ...deltaState } });
    }
    this.session.path.registerStep(st);
    return st;
  }

  _skill_find_pareto_paths({ initialState, targetState, maxDepth = 5 }) {
    return this.session.findParetoPathways(initialState, targetState, maxDepth);
  }

  _skill_rank_pathways({ pathways, by = 'balanced' }) {
    const keys = {
      cost: p => p.accumulatedCost,
      duration: p => p.accumulatedDuration,
      feasibility: p => -p.jointFeasibility,
    };
    if (by === 'balanced') {
      if (pathways.length === 0) return [];
      const norm = (vals) => {
        const lo = Math.min(...vals), hi = Math.max(...vals);
        return vals.map(v => (hi === lo ? 0.0 : (v - lo) / (hi - lo)));
      };
      const c = norm(pathways.map(p => p.accumulatedCost));
      const d = norm(pathways.map(p => p.accumulatedDuration));
      const f = norm(pathways.map(p => -p.jointFeasibility));
      return pathways.map((p, i) => [p, c[i] + d[i] + f[i]]).sort((a, b) => a[1] - b[1]).map(x => x[0]);
    }
    if (!(by in keys)) throw new Error('by must be one of: cost, duration, feasibility, balanced');
    return [...pathways].sort((a, b) => keys[by](a) - keys[by](b));
  }

  _skill_compare_states({ stateA, stateB }) {
    const changed = {};
    for (const k of Object.keys(stateA).filter(k => k in stateB).sort()) {
      const a = stateA[k], b = stateB[k];
      if (isNum(a) && isNum(b)) {
        if (a !== b) changed[k] = { from: a, to: b, delta: b - a, relative: a ? (b - a) / Math.abs(a) : null };
      } else if (JSON.stringify(a) !== JSON.stringify(b)) {
        changed[k] = { from: a, to: b };
      }
    }
    const added = Object.fromEntries(Object.entries(stateB).filter(([k]) => !(k in stateA)));
    const removed = Object.fromEntries(Object.entries(stateA).filter(([k]) => !(k in stateB)));
    return {
      changed, added, removed,
      identical: Object.keys(changed).length === 0 && Object.keys(added).length === 0 && Object.keys(removed).length === 0,
    };
  }

  // ============================================================ 6. Fidelity & Sampling
  _skill_choose_fidelity({ inputs, cheapSolver, expensiveSolver, taskId = 'fidelity_eval', intermediateSolver = null, tolerance = null }) {
    return this.session.amf.evaluate({ taskId, inputs, cheapSolver, expensiveSolver, intermediateSolver, tolerance });
  }

  _skill_compute_multi_fidelity({ taskId, inputs, cheapSolver, expensiveSolver, intermediateSolver = null, tolerance = null }) {
    return this.session.amf.evaluate({ taskId, inputs, cheapSolver, expensiveSolver, intermediateSolver, tolerance });
  }

  _skill_suggest_samples({ candidates, topK = null }) {
    const ranked = candidates.map(pt => this.session.asg.evaluateCandidate(pt))
      .sort((a, b) => b.informationGain - a.informationGain);
    return topK ? ranked.slice(0, topK) : ranked;
  }

  _skill_run_adaptive_sampling({ candidates, objectiveFn, maxBudget = null }) {
    const asg = this.session.asg;
    const selected = [];
    for (const cand of candidates) {
      if (maxBudget && selected.length >= maxBudget) break;
      if (!asg.evaluateCandidate(cand).skipRecommended) {
        selected.push(cand);
        asg.recordEvaluation(cand, objectiveFn(cand));
      }
    }
    const total = candidates.length;
    return {
      totalGridPointsPossible: total, pointsEvaluated: selected.length,
      pointsSkipped: total - selected.length,
      pointsSavedPct: total ? ((total - selected.length) / total) * 100.0 : 0.0,
      activeSamples: selected,
    };
  }

  _skill_should_stop({ previousValue = null, ...rest }) {
    return this.session.uas.evaluateStep({ previousValue, ...rest });
  }

  _skill_value_of_information({ candidateId, predictedValue, epistemicUncertainty, decisionThreshold, estimatedCost = 1.0 }) {
    return this.session.voi.evaluateCandidate(candidateId, predictedValue, epistemicUncertainty, decisionThreshold, estimatedCost);
  }

  _skill_warm_start({ taskId, inputs }) {
    const s = this.session;
    const exact = s.mate.lookup(taskId, inputs);
    if (exact !== undefined && exact !== null) return { seed: exact, source: 'MATE_EXACT', confidence: 1.0 };
    const a = s.cpe.assessReuse(taskId, inputs);
    if (a.value !== null && a.value !== undefined && a.reuseType !== 'FULL_COMPUTATION') {
      return { seed: a.value, source: `CPE_${a.reuseType}`, confidence: a.confidence };
    }
    const pk = s.pke.getLatest(taskId);
    if (pk) return { seed: pk.latestEstimate, source: 'PKE_PARTIAL', confidence: 0.5 };
    return { seed: null, source: 'NONE', confidence: 0.0 };
  }

  _skill_build_surrogate({ modelId, points, values }) {
    if (points.length !== values.length) throw new Error('points and values must have the same length');
    if (points.length === 0) throw new Error('at least one sample point is required');
    return this.session.sme.fitFromHistory(modelId, points, values);
  }

  // ============================================================ 7. Sensitivity & Cuts
  _skill_analyze_sensitivity({ baseInputs, objectiveFn, perturbationDelta = 0.01 }) {
    return this.session.sra.analyzeOneAtATime(baseInputs, objectiveFn, perturbationDelta);
  }

  _skill_reduce_dimensions({ baseInputs, objectiveFn, targetVarianceExplained = 0.95 }) {
    return this.session.sra.reduceParameterSpace(baseInputs, objectiveFn, targetVarianceExplained);
  }

  _skill_infer_constraints({ failures }) {
    for (const f of failures) this.session.cae.recordInfeasibility(f);
    return [...this.session.cae.inferredConstraints];
  }

  _skill_apply_constraints({ inputs }) { return this.session.cae.validateInputs(inputs); }

  _skill_extract_partial_knowledge({ taskId }) { return this.session.pke.getLatest(taskId) ?? null; }

  _skill_reuse_approximate({ taskId, inputs, tolerance = null }) {
    return this.session.cpe.assessReuse(taskId, inputs, tolerance);
  }

  _skill_map_landscape({ bounds, surrogate }) { return this.session.lse.probeRegion(bounds, surrogate); }

  // ============================================================ 8. Provenance & Hygiene
  _skill_get_provenance({ taskId = null, recordId = null } = {}) {
    let recs = [...this.session.cpe.records.values()];
    if (recordId) recs = recs.filter(r => r.recordId === recordId);
    if (taskId) recs = recs.filter(r => r.taskId === taskId);
    return recs;
  }

  _skill_assess_reuse({ taskId, inputs, customTolerance = null }) {
    return this.session.cpe.assessReuse(taskId, inputs, customTolerance);
  }

  _skill_forget_results({ count = 10 } = {}) {
    if (count < 0) throw new Error('count must be non-negative');
    const s = this.session;
    const victims = s.rfe.identifyEvictionCandidates(count);
    for (const key of victims) {
      s.rfe.entryMetadata.delete(key);
      s.mate._cache.delete(key);
    }
    return { evicted: victims, count: victims.length };
  }

  _skill_version_model({ label = null } = {}) {
    const name = label || `v${this.versions.size + 1}`;
    if (this.versions.has(name)) throw new Error(`Version '${name}' already exists`);
    const snap = {};
    for (const l of this.session.fln.layers.values()) snap[l.layerId] = { version: l.version, state: clone(l.state) };
    this.versions.set(name, snap);
    return { version: name, layers: Object.keys(snap).length };
  }

  _skill_diff_model_versions({ versionA, versionB }) {
    for (const v of [versionA, versionB]) if (!this.versions.has(v)) throw new Error(`Unknown model version '${v}'`);
    const a = this.versions.get(versionA), b = this.versions.get(versionB);
    const out = {
      layersAdded: Object.keys(b).filter(k => !(k in a)).sort(),
      layersRemoved: Object.keys(a).filter(k => !(k in b)).sort(),
      changed: {},
    };
    for (const lid of Object.keys(a).filter(k => k in b).sort()) {
      const d = this._skill_compare_states({ stateA: a[lid].state, stateB: b[lid].state });
      if (!d.identical) out.changed[lid] = d;
    }
    return out;
  }

  // ============================================================ 9. Thematic (STE)
  _skill_analyze_themes() { return this.session.analyzeThemes(); }
  _skill_get_theme_coverage() { return this.session.analyzeThemes().coveragePct; }
  _skill_detect_theme_gaps() { return this.session.analyzeThemes().thematicGaps; }
  _skill_suggest_related_themes() { return this.session.analyzeThemes().relatedSuggestions; }

  _skill_explain_model_focus() {
    const rep = this.session.analyzeThemes();
    const lead = rep.primaryThemes.length ? rep.primaryThemes : rep.secondaryThemes;
    if (lead.length === 0) {
      return 'No thematic signal detected yet: register layers with descriptive names and variables.';
    }
    let text = `The model is mainly about ${lead.slice(0, 3).map(([k, v]) => `${k} (${v.toFixed(0)}%)`).join(', ')}.`;
    if (rep.thematicGaps.length) text += ` Gaps: ${rep.thematicGaps.join('; ')}.`;
    if (rep.biasWarnings.length) text += ` Warnings: ${rep.biasWarnings.join('; ')}.`;
    return text;
  }

  // ============================================================ 10. Literature (LKE)
  _domains(domains) {
    if (domains && domains.length) return domains;
    const primary = this.session.analyzeThemes().primaryThemes.map(t => t[0]);
    return primary.length ? primary : ['multidisciplinary'];
  }

  _skill_search_literature({ domains = null, limit = 5 } = {}) { return this.session.searchLiterature(domains, limit); }

  _skill_search_datasets({ domains = null, limit = 5 } = {}) {
    return this.session.lke.proposeResources(this._domains(domains), limit, [SourceType.DATASET_PROPERTIES]);
  }

  _skill_search_reference_code({ domains = null, limit = 5 } = {}) {
    return this.session.lke.proposeResources(this._domains(domains), limit, [SourceType.CODE_METHODS]);
  }

  _skill_rank_external_sources({ domains = null, limit = 10 } = {}) {
    return this.session.lke.proposeResources(this._domains(domains), Math.max(limit, 50))
      .sort((a, b) => b.confidence - a.confidence).slice(0, limit);
  }

  _skill_propose_external_evidence({ domains = null, limit = 5 } = {}) {
    return this.session.lke.proposeResources(this._domains(domains), limit);
  }

  _skill_link_evidence_to_gap({ gap, evidence }) {
    const link = {
      gap: (gap && (gap.description || gap.targetKey)) || String(gap),
      evidence: (evidence && evidence.title) || String(evidence),
      url: (evidence && evidence.url) || null,
    };
    this.evidenceLinks.push(link);
    return link;
  }

  // ============================================================ 11. Gaps & Assumptions
  _skill_detect_gaps({ requiredSchema = {} } = {}) {
    return this.session.autocomplete.detectGaps(this.session._mergedLayerState(), requiredSchema || {});
  }

  _skill_suggest_gap_closure({ requiredSchema = {}, gaps = null } = {}) {
    const merged = this.session._mergedLayerState();
    const g = gaps ?? this.session.autocomplete.detectGaps(merged, requiredSchema || {});
    return this.session.autocomplete.suggestConnections(g, merged);
  }

  _skill_list_assumptions() {
    return [...this.session.aie.assumptions.values()].map(a => ({
      id: a.assumptionId, name: a.name, criticality: a.criticality, description: a.description || '',
    }));
  }

  _skill_check_assumption_integrity({ state }) { return this.session.aie.auditState(state); }

  // ============================================================ 12. Explanation & Audit
  _skill_explain_decision({ taskId = null, engineName = null, action = null, rationale = null } = {}) {
    const xxe = this.session.xxe;
    if (action && rationale) xxe.recordDecision(engineName || 'USER', action, rationale, 0.0, taskId ? { taskId } : {});
    return xxe.explainTask(taskId || 'latest');
  }

  _skill_explain_result({ taskId = 'latest' } = {}) {
    const s = this.session;
    const recs = [...s.cpe.records.values()].filter(r => taskId === 'latest' || r.taskId === taskId);
    const last = recs.length ? recs[recs.length - 1] : null;
    const exp = s.xxe.explainTask(taskId);
    return {
      taskId, found: last !== null,
      inputs: last ? last.inputs : null, output: last ? last.output : null,
      method: last ? last.numericalMethod : null,
      narrative: exp.narrative, invariantsDeclared: [...this.invariants.keys()].sort(),
    };
  }

  _skill_audit_run() {
    const s = this.session;
    const manifest = s.rme.generateManifest(s.name);
    return {
      session: s.name, report: s.generateReport(), decisions: s.xxe.decisionLog.length,
      skillTrace: [...this.executionLog],
      failedSkills: this.executionLog.filter(e => e.status !== 'SUCCESS'),
      manifestSeal: manifest.cryptographicSeal, markdown: s.xxe.exportAuditMarkdown(),
    };
  }

  _skill_compare_runs({ runs = null, label = null } = {}) {
    let snaps = runs ? runs.map(r => ({ ...r })) : null;
    if (snaps === null) {
      this.runSnapshots.push({ label: label || `run_${this.runSnapshots.length + 1}`, ...this.session.generateReport() });
      snaps = this.runSnapshots;
    }
    const metrics = [...new Set(snaps.flatMap(r => Object.entries(r).filter(([, v]) => isNum(v)).map(([k]) => k)))].sort();
    const out = {};
    for (const m of metrics) {
      const vals = snaps.map(r => r[m]).filter(isNum);
      out[m] = {
        min: Math.min(...vals), max: Math.max(...vals),
        mean: vals.reduce((a, b) => a + b, 0) / vals.length, deltaFirstLast: vals[vals.length - 1] - vals[0],
      };
    }
    return { runs: snaps.length, metrics: out };
  }

  // ============================================================ 13. Reporting & Export
  _skill_generate_report({ format = 'object' } = {}) {
    const rep = this.session.generateReport();
    if (format === 'object') return rep;
    if (format !== 'markdown') throw new Error("format must be 'object' or 'markdown'");
    const lines = [`# SFSA Report — ${rep.sessionName}`, ''];
    for (const [k, v] of Object.entries(rep)) if (k !== 'sessionName') lines.push(`- **${k}**: ${v}`);
    return lines.join('\n');
  }

  _skill_export_graph() { return this.session.fln.exportGraph(); }

  _skill_export_cache_manifest() {
    const s = this.session;
    const m = s.mate.exportManifest();
    m.provenance = [...s.cpe.records.values()].map(r => ({
      recordId: r.recordId, taskId: r.taskId, modelVersion: r.modelVersion, reuseCount: r.reuseCount,
    }));
    return m;
  }

  _skill_export_thematic_map() {
    const r = this.session.analyzeThemes();
    return { coveragePct: r.coveragePct, primary: r.primaryThemes, secondary: r.secondaryThemes, gaps: r.thematicGaps };
  }

  _skill_export_skill_trace() { return [...this.executionLog]; }

  // ============================================================ 14. Agent Planning
  _skill_plan_computation({ archetype = 'HIGH_PRECISION_SOLVE', inputCardinality = 1, parameterDim = 2, budgetRemainingSeconds = null, tolerance = 0.05 } = {}) {
    if (!(archetype in QueryArchetype)) {
      throw new Error(`Unknown archetype '${archetype}'. Valid: ${Object.keys(QueryArchetype).join(', ')}`);
    }
    return this.session.ore.planPipeline({
      queryArchetype: QueryArchetype[archetype], inputCardinality, parameterDim,
      budgetRemainingSeconds: budgetRemainingSeconds ?? this.session.tbe.getRemainingSeconds(), tolerance,
    });
  }

  _skill_select_next_action() {
    const s = this.session;
    if (s.fln.layers.size === 0) return { skill: 'register_layer', reason: 'No layers registered: define the model first.' };
    if (this.invariants.size === 0) return { skill: 'declare_invariants', reason: 'No physical invariants declared for T3 verification.' };
    if (s.aie.assumptions.size === 0) return { skill: 'check_assumption_integrity', reason: 'No assumptions registered to audit.' };
    if (this._skill_detect_gaps().length > 0) return { skill: 'suggest_gap_closure', reason: 'Model has parameter gaps.' };
    if (s.mate.stats().totalLookups === 0) return { skill: 'compute', reason: 'Nothing computed yet.' };
    if (s.analyzeThemes().thematicGaps.some(g => g.toLowerCase().includes('uncertainty'))) {
      return { skill: 'analyze_sensitivity', reason: 'Uncertainty/sensitivity coverage is low.' };
    }
    return { skill: 'generate_report', reason: 'Model is set up and exercised: summarize results.' };
  }

  // Predicts what compute() would do, without running any solver or mutating caches/metrics.
  _skill_dry_run({ taskId = 'dry_run', inputs = {}, operations = 1000 } = {}) {
    const s = this.session;
    const [ok, reason] = s.cae.validateInputs(inputs);
    const key = s.mate._hashKey(taskId, inputs);
    const cached = s.mate.memoizedGet(key) !== undefined && s.mate.memoizedGet(key) !== null;
    const reuse = s.cpe.assessReuse(taskId, inputs);
    let action;
    if (!ok) action = 'ABORT_CONSTRAINT';
    else if (cached) action = 'CACHE_HIT';
    else if (reuse.reuseType === 'APPROXIMATE_REUSE') action = 'APPROXIMATE_REUSE';
    else action = 'FULL_COMPUTE';
    return {
      predictedAction: action, constraintReason: reason, cached, reuseType: reuse.reuseType,
      estimatedOperations: action === 'FULL_COMPUTE' ? operations : 0,
    };
  }

  _skill_validate_skill_call({ skill, args = {} }) { return this.validate(skill, args); }

  _skill_batch_queries({ queries, heavySolver }) { return this.session.cqe.compressAndSolve(queries, heavySolver); }

  _skill_prioritize_queries({ queries, costFn = null }) {
    return queries.map(q => {
      const cost = Math.max(costFn ? Number(costFn(q)) : 1.0, 1e-9);
      const gain = this.session.asg.evaluateCandidate(q).informationGain;
      return { query: q, informationGain: gain, cost, score: gain / cost };
    }).sort((a, b) => b.score - a.score);
  }
}
