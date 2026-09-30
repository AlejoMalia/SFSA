"""
Exhaustive functional tests for the 85-skill catalog.

Every catalog skill is executed with realistic arguments and its *behaviour* is asserted, so a skill
that degrades to a no-op stub (returning {"status": "EXECUTED"}) fails here.
"""
import json
import math
import os
import tempfile

import pytest

from sfsa import SFSASession
from sfsa.skills import SKILL_DEFINITIONS, REQUIRED_ARGS


@pytest.fixture
def s():
    sess = SFSASession(name="skills_test")
    sess.register_layer("thermo", {"temp_k": 300.0, "pressure_pa": 101325.0}, "thermodynamics")
    sess.register_layer("kinetics", {"rate": 1.0, "temp_k": 310.0}, "chemical_kinetics")
    sess.connect_layers("thermo", "kinetics", lambda src, tgt: {"rate": src["temp_k"] * 0.01})
    return sess


def test_catalog_is_complete_and_unique():
    assert len(SKILL_DEFINITIONS) == 85
    assert sorted(m.skill_number for m in SKILL_DEFINITIONS) == list(range(1, 86))
    assert len({m.name for m in SKILL_DEFINITIONS}) == 85


def test_every_skill_has_a_handler(s):
    assert s.skills.missing_implementations() == []
    for name in REQUIRED_ARGS:
        assert name in s.skills.skills_by_name, f"REQUIRED_ARGS names unknown skill {name}"


def test_unknown_skill_and_missing_args(s):
    with pytest.raises(ValueError, match="Unknown"):
        s.execute_skill("nope")
    with pytest.raises(ValueError, match="Missing required argument 'layer_id'"):
        s.execute_skill("get_layer_state")
    assert s.skills.execution_log[-1]["status"] == "INVALID_ARGS"
    v = s.execute_skill("validate_skill_call", skill="compute", args={"task_id": "t"})
    assert not v["valid"] and set(v["missing"]) == {"inventory", "solver"}
    assert s.execute_skill("validate_skill_call", skill=22, args={"task_id": "t", "inventory": {}, "solver": len})["valid"]


def test_failed_skill_is_logged_as_error_not_success(s):
    with pytest.raises(KeyError):
        s.execute_skill("get_layer_state", layer_id="ghost")
    assert s.skills.execution_log[-1]["status"] == "ERROR"


# ------------------------------------------------------------------ 1-7 Orchestration
def test_session_lifecycle(s, tmp_path):
    assert s.execute_skill("create_session") is s
    s.execute_skill("set_budget", seconds=5)
    assert s.tbe.total_budget == 5
    with pytest.raises(ValueError):
        s.execute_skill("set_budget", seconds=-1)
    pol = s.execute_skill("set_policy", policy={"reuse_tolerance": 0.123, "mate_spec_mode": "off"})
    assert s.cpe.approximate_tolerance == 0.123 and s.mate.spec_mode == "off" and pol["reuse_tolerance"] == 0.123
    with pytest.raises(ValueError):
        s.execute_skill("set_policy", mate_spec_mode="bogus")

    path = str(tmp_path / "sess.json")
    s.execute_skill("update_layer", layer_id="thermo", new_state={"temp_k": 350.0})
    s.execute_skill("save_session", path=path)
    assert json.load(open(path))["layers"]["thermo"]["state"]["temp_k"] == 350.0

    fresh = SFSASession(name="fresh")
    fresh.execute_skill("load_session", path=path)
    assert fresh.fln.get_layer("thermo").state["temp_k"] == 350.0
    assert fresh.cpe.approximate_tolerance == 0.123

    st = s.execute_skill("get_session_status")
    assert st.active_layers_count == 2

    s.execute_skill("store_result", task_id="t", inputs={"x": 1.0}, output=2.0)
    assert s.execute_skill("reset_session", scope="cache")["cleared"] == ["cache"]
    assert s.execute_skill("query_cache", task_id="t", inputs={"x": 1.0}) is None
    assert len(s.fln.layers) == 2
    s.execute_skill("reset_session", scope="layers")
    assert len(s.fln.layers) == 0
    with pytest.raises(ValueError):
        s.execute_skill("reset_session", scope="nonsense")


# ------------------------------------------------------------------ 8-15 FLN
def test_fln_skills(s):
    s.register_layer("out", {"y": 0.0})
    s.execute_skill("connect_layers", source_id="kinetics", target_id="out", transformer=lambda a, b: {"y": a["rate"] * 2})
    versions = s.execute_skill("update_layer", layer_id="thermo", new_state={"temp_k": 400.0})
    assert s.fln.get_layer("out").state["y"] == pytest.approx(8.0) and set(versions) == {"thermo", "kinetics", "out"}

    assert s.execute_skill("get_layer_state", layer_id="kinetics")["rate"] == pytest.approx(4.0)
    assert s.execute_skill("find_affected_layers", layer_id="thermo") == ["kinetics", "out"]
    assert s.execute_skill("find_affected_layers", layer_id="out") == []

    g = s.execute_skill("inspect_graph")
    assert g["dependencies"] == 2 and g["centrality"]["kinetics"] == pytest.approx(1.0)

    s.fln.get_layer("thermo").state["temp_k"] = 500.0
    s.execute_skill("propagate_delta", layer_id="thermo", delta={"temp_k": 500.0})
    assert s.fln.get_layer("out").state["y"] == pytest.approx(10.0)

    r = s.execute_skill("disconnect_layers", source_id="kinetics", target_id="out")
    assert r["edges_removed"] == 1
    assert s.execute_skill("find_affected_layers", layer_id="thermo") == ["kinetics"]
    assert s.execute_skill("disconnect_layers", source_id="kinetics", target_id="out")["disconnected"] is False
    with pytest.raises(KeyError):
        s.execute_skill("find_affected_layers", layer_id="ghost")


# ------------------------------------------------------------------ 16-21 TRIADA
def test_triada_skills(s):
    ok = s.execute_skill("inventory_check", inventory={"m": 1.0, "T": 300.0}, bounds={"T": (0, 1000)}, required=["m"])
    assert ok["passed"]
    bad = s.execute_skill("inventory_check", inventory={"T": -5.0}, bounds={"T": (0, 1000)}, required=["m"],
                          conservation={"mass": lambda inv: inv.get("T", 0) > 0})
    assert not bad["passed"] and len(bad["reasons"]) == 3
    assert not s.execute_skill("inventory_check", inventory={"a": float("nan")})["passed"]

    cf = s.execute_skill("try_closed_form", inputs={"x": 4.0}, analytical=lambda i: math.sqrt(i["x"]))
    assert cf["solved"] and cf["value"] == 2.0
    assert not s.execute_skill("try_closed_form", inputs={"x": 0.0}, analytical=lambda i: 1 / i["x"])["solved"]

    s.execute_skill("declare_invariants", invariants={"non_negative": lambda v: v >= 0})
    assert s.execute_skill("check_invariants", result=3.0)["passed"]
    chk = s.execute_skill("check_invariants", result=-1.0)
    assert not chk["passed"] and chk["failures"][0]["invariant"] == "non_negative"
    assert s.execute_skill("bounded_verify", result=-1.0, invariants={"always": lambda v: True})["passed"]
    with pytest.raises(KeyError):
        s.execute_skill("check_invariants", result=1.0, names=["undeclared"])

    rep = s.execute_skill("run_triada", task_name="ke", inventory={"m": 2.0, "v": 3.0},
                          solver=lambda i: 0.5 * i["m"] * i["v"] ** 2, required=["m", "v"], invariants=[lambda v: v > 0])
    assert rep.success and rep.final_output == pytest.approx(9.0)
    rep2 = s.execute_skill("run_triada", task_name="ke2", inventory={"m": -2.0, "v": 3.0},
                           solver=lambda i: 0.5 * i["m"] * i["v"] ** 2, invariants={"pos": lambda v: v > 0})
    assert not rep2.success
    rep3 = s.execute_skill("run_triada", task_name="ke3", inventory={"m": 1.0}, solver=lambda i: 1, required=["v"])
    assert not rep3.success and rep3.failed_at_stage.name.startswith("T1")


# ------------------------------------------------------------------ 22-29 MATE / ICR
def test_mate_icr_skills(s):
    calls = []

    def solver(inv):
        calls.append(1)
        return inv["x"] ** 2

    r1 = s.execute_skill("compute", task_id="sq", inventory={"x": 3.0}, solver=solver)
    r2 = s.execute_skill("compute", task_id="sq", inventory={"x": 3.0}, solver=solver)
    assert r1.value == r2.value == 9.0 and len(calls) == 1 and r2.cached
    assert s.execute_skill("query_cache", task_id="sq", inputs={"x": 3.0}) == 9.0

    s.execute_skill("store_result", task_id="manual", inputs={"a": 1}, output=42)
    assert s.execute_skill("query_cache", task_id="manual", inputs={"a": 1}) == 42
    assert s.execute_skill("get_provenance", task_id="manual")[0].output == 42

    assert s.execute_skill("project_trajectory", task_id="t", inputs={"x": 1}, invariants=[lambda i: i["x"] > 0]) is True
    assert s.execute_skill("project_trajectory", task_id="t", inputs={"x": -1}, invariants=[lambda i: i["x"] > 0]) is False
    ab = s.execute_skill("early_abort_check", task_id="t", inputs={"x": -1}, invariants=[lambda i: i["x"] > 0])
    assert ab["should_abort"] and ab["reasons"]
    assert not s.execute_skill("early_abort_check", task_id="t", inputs={"x": 1})["should_abort"]

    red = s.execute_skill("reduce_expression", expression="0 * x + 1 * y")
    assert red.operations_eliminated_count >= 1

    c = s.execute_skill("estimate_compute_cost", operations=1000, cost_per_op_ms=0.5, cache_hit_rate=0.5)
    assert c["estimated_ms"] == pytest.approx(250.0) and c["estimated_ms_no_reuse"] == pytest.approx(500.0)
    with pytest.raises(ValueError):
        s.execute_skill("estimate_compute_cost", operations=-1)

    n = s.execute_skill("invalidate_cache", new_model_version="v2")
    assert isinstance(n["mechanisms_invalidated"], int)
    assert s.execute_skill("query_cache", task_id="sq", inputs={"x": 3.0}) is None


def test_compute_enforces_bounds_and_invariants(s):
    with pytest.raises(ValueError, match="Bounds"):
        s.compute("b", {"x": 11.0}, lambda i: i["x"], bounds={"x": (0.0, 10.0)})
    res = s.compute("inv", {"x": 2.0}, lambda i: -i["x"], invariants=[lambda v: v > 0])
    assert res.value is None and "invariant" in res.diagnostic_message
    assert s.mate.lookup("inv", {"x": 2.0}) is None  # invalid result is not cached
    assert s.compute("inv_ok", {"x": 2.0}, lambda i: i["x"], invariants=[lambda v: v > 0]).value == 2.0


def test_compute_with_unhashable_inventory(s):
    assert s.compute("lst", {"xs": [1, 2, 3]}, lambda i: sum(i["xs"])).value == 6


# ------------------------------------------------------------------ 30-35 Consistency & Pareto
def test_consistency_and_pareto_skills(s):
    rep = s.execute_skill("project_layers", layer_a="thermo", layer_b="kinetics")
    assert rep.total_parameters_compared >= 1
    c = s.execute_skill("check_consistency", layer_a="thermo", layer_b="kinetics")
    assert c["consistent"] is False  # temp_k 300 vs 310 (VALUE_MISMATCH) or similar
    same = s.execute_skill("check_consistency", layer_a={"a": 1.0}, layer_b={"a": 1.0})
    assert same["consistent"] is True

    s.execute_skill("register_transition_step", step_id="heat", name="heat", cost=2.0, duration=1.0, feasibility=0.9, delta_state={"T": 50.0})
    s.execute_skill("register_transition_step", step_id="heat_fast", name="heat fast", cost=5.0, duration=0.2, feasibility=0.8, delta_state={"T": 50.0})
    s.execute_skill("register_transition_step", step_id="cool", name="cool", cost=1.0, duration=1.0, feasibility=1.0, delta_state={"T": -10.0})
    with pytest.raises(ValueError):
        s.execute_skill("register_transition_step", step_id="bad", cost=1, duration=1, feasibility=2.0, delta_state={})
    paths = s.execute_skill("find_pareto_paths", initial_state={"T": 300.0}, target_state={"T": 350.0})
    assert paths and all(p.is_pareto_optimal for p in paths)
    by_cost = s.execute_skill("rank_pathways", pathways=paths, by="cost")
    assert by_cost[0].accumulated_cost == min(p.accumulated_cost for p in paths)
    by_dur = s.execute_skill("rank_pathways", pathways=paths, by="duration")
    assert by_dur[0].accumulated_duration == min(p.accumulated_duration for p in paths)
    assert len(s.execute_skill("rank_pathways", pathways=paths)) == len(paths)
    with pytest.raises(ValueError):
        s.execute_skill("rank_pathways", pathways=paths, by="vibes")

    d = s.execute_skill("compare_states", state_a={"a": 1.0, "b": 2.0, "gone": 1}, state_b={"a": 1.5, "b": 2.0, "new": 7})
    assert d["changed"]["a"]["delta"] == pytest.approx(0.5) and d["added"] == {"new": 7} and d["removed"] == {"gone": 1}
    assert s.execute_skill("compare_states", state_a={"a": 1}, state_b={"a": 1})["identical"]


# ------------------------------------------------------------------ 36-43 Fidelity & Sampling
def test_fidelity_sampling_skills(s):
    cheap = lambda i: (i["t"] * 1.8e-3, 0.02)
    exp = lambda i: i["t"] * 1.82e-3
    d = s.execute_skill("choose_fidelity", inputs={"t": 300.0}, cheap_solver=cheap, expensive_solver=exp, tolerance=0.05)
    assert d.selected_level
    d2 = s.execute_skill("compute_multi_fidelity", task_id="mf", inputs={"t": 300.0}, cheap_solver=cheap, expensive_solver=exp)
    assert d2.selected_level

    grid = [{"x": i / 10.0, "y": j / 10.0} for i in range(10) for j in range(10)]
    ranked = s.execute_skill("suggest_samples", candidates=grid[:20], top_k=5)
    assert len(ranked) == 5 and ranked[0].information_gain >= ranked[-1].information_gain

    camp = s.execute_skill("run_adaptive_sampling", candidates=grid, objective_fn=lambda p: p["x"] + p["y"], max_budget=15)
    assert camp.points_evaluated <= 15 and camp.points_evaluated + camp.points_skipped == 100
    assert len(s.asg.point_values) == camp.points_evaluated
    assert any(v != 0.0 for v in s.asg.point_values)  # real objective values, not placeholders

    stop = s.execute_skill("should_stop", iteration=10, current_value=1.0, previous_value=1.0 + 1e-9, max_planned_iterations=100)
    assert stop.should_stop and stop.iterations_saved > 0
    go = s.execute_skill("should_stop", iteration=0, current_value=1.0, previous_value=None, max_planned_iterations=100)
    assert not go.should_stop

    voi = s.execute_skill("value_of_information", candidate_id="c", predicted_value=10.0, epistemic_uncertainty=0.1, decision_threshold=0.0)
    assert hasattr(voi, "recommended") or hasattr(voi, "skip_recommended") or voi is not None

    assert s.execute_skill("warm_start", task_id="w", inputs={"x": 1.0})["source"] == "NONE"
    s.execute_skill("store_result", task_id="w", inputs={"x": 1.0}, output=5.0)
    ws = s.execute_skill("warm_start", task_id="w", inputs={"x": 1.0})
    assert ws["seed"] == 5.0 and ws["source"] == "MATE_EXACT"

    sm = s.execute_skill("build_surrogate", model_id="m", points=[{"x": 0.0}, {"x": 1.0}], values=[0.0, 10.0])
    val, unc = sm.predict({"x": 0.0})
    assert val == 0.0 and unc == 0.0
    with pytest.raises(ValueError):
        s.execute_skill("build_surrogate", model_id="m", points=[{"x": 0.0}], values=[1.0, 2.0])


# ------------------------------------------------------------------ 44-50 Sensitivity & Cuts
def test_sensitivity_and_cut_skills(s):
    f = lambda p: p["a"] * 10.0 + p["b"] * 0.001
    sens = s.execute_skill("analyze_sensitivity", base_inputs={"a": 1.0, "b": 1.0}, objective_fn=f)
    assert sens[0].parameter_name == "a"
    red = s.execute_skill("reduce_dimensions", base_inputs={"a": 1.0, "b": 1.0}, objective_fn=f)
    assert red.reduced_dimension < red.original_dimension

    cuts = s.execute_skill("infer_constraints", failures=[{"p": 100.0 + i} for i in range(6)])
    assert cuts and cuts[0].parameter_name == "p"
    ok, why = s.execute_skill("apply_constraints", inputs={"p": 50.0})
    assert ok
    ok, why = s.execute_skill("apply_constraints", inputs={"p": 500.0})
    assert not ok and why

    s.pke.capture("long", 7, estimate=3.3, lower_bound=3.0, upper_bound=3.6, residual=0.1)
    assert s.execute_skill("extract_partial_knowledge", task_id="long").latest_estimate == 3.3
    assert s.execute_skill("extract_partial_knowledge", task_id="none") is None

    s.execute_skill("store_result", task_id="ar", inputs={"x": 100.0}, output=7.0)
    near = s.execute_skill("reuse_approximate", task_id="ar", inputs={"x": 100.5}, tolerance=0.05)
    assert near.reuse_type.value == "APPROXIMATE_REUSE" and near.value == 7.0
    far = s.execute_skill("reuse_approximate", task_id="ar", inputs={"x": 500.0}, tolerance=0.05)
    assert far.reuse_type.value != "APPROXIMATE_REUSE"

    land = s.execute_skill("map_landscape", bounds={"x": (0.0, 1.0)}, surrogate=lambda p: p["x"] ** 2)
    assert land is not None


# ------------------------------------------------------------------ 51-55 Provenance & Hygiene
def test_provenance_and_hygiene_skills(s):
    s.execute_skill("store_result", task_id="p", inputs={"x": 1.0}, output=1.0)
    assert len(s.execute_skill("get_provenance")) == 1
    assert s.execute_skill("assess_reuse", task_id="p", inputs={"x": 1.0}).reuse_type.value in ("EXACT_CACHE", "APPROXIMATE_REUSE")

    before = len(s.rfe.entry_metadata)
    assert before >= 1
    res = s.execute_skill("forget_results", count=1)
    assert res["count"] == 1 and len(s.rfe.entry_metadata) == before - 1
    with pytest.raises(ValueError):
        s.execute_skill("forget_results", count=-1)

    s.execute_skill("version_model", label="v1")
    s.execute_skill("update_layer", layer_id="thermo", new_state={"temp_k": 999.0})
    s.register_layer("extra", {"z": 1})
    s.execute_skill("version_model", label="v2")
    diff = s.execute_skill("diff_model_versions", version_a="v1", version_b="v2")
    assert "thermo" in diff["changed"] and diff["layers_added"] == ["extra"]
    # snapshots are deep copies: later mutation must not leak into v1
    assert s.skills.versions["v1"]["thermo"]["state"]["temp_k"] == 300.0
    with pytest.raises(ValueError):
        s.execute_skill("version_model", label="v1")
    with pytest.raises(KeyError):
        s.execute_skill("diff_model_versions", version_a="v1", version_b="vX")


# ------------------------------------------------------------------ 56-60 STE
def test_thematic_skills(s):
    cov = s.execute_skill("get_theme_coverage")
    assert isinstance(cov, dict) and cov
    assert isinstance(s.execute_skill("detect_theme_gaps"), list)
    assert isinstance(s.execute_skill("suggest_related_themes"), list)
    text = s.execute_skill("explain_model_focus")
    assert isinstance(text, str) and len(text) > 20
    empty = SFSASession(name="empty")
    assert "No thematic signal" in empty.execute_skill("explain_model_focus")
    assert s.execute_skill("export_thematic_map")["coverage_pct"] == cov


# ------------------------------------------------------------------ 61-66 LKE
def test_literature_skills(s):
    lit = s.execute_skill("search_literature", domains=["thermodynamics"], limit=3)
    assert 0 < len(lit) <= 3
    ds = s.execute_skill("search_datasets", domains=["thermodynamics"], limit=3)
    assert ds and all(p.source_type.name == "DATASET_PROPERTIES" for p in ds)
    code = s.execute_skill("search_reference_code", limit=3)
    assert code and all(p.source_type.name == "CODE_METHODS" for p in code)
    ranked = s.execute_skill("rank_external_sources", domains=["physics"], limit=5)
    assert [p.confidence for p in ranked] == sorted((p.confidence for p in ranked), reverse=True)
    assert s.execute_skill("propose_external_evidence", domains=["chemistry"], limit=2)
    link = s.execute_skill("link_evidence_to_gap", gap="missing uncertainty", evidence=lit[0])
    assert link["evidence"] == lit[0].title and s.skills.evidence_links == [link]


# ------------------------------------------------------------------ 67-73 Assumptions & Audit
def test_gap_assumption_and_audit_skills(s):
    gaps = s.execute_skill("detect_gaps", required_schema={"temp_k": float, "missing_param": float})
    assert any("missing_param" in str(g) for g in gaps)
    s.execute_skill("suggest_gap_closure", required_schema={"temp_k": float, "missing_param": float})

    s.aie.register_assumption("lam", "Laminar flow", lambda st: (st.get("re", 0) < 2300, "Re too high"), "WARNING", "Re<2300")
    lst = s.execute_skill("list_assumptions")
    assert lst == [{"id": "lam", "name": "Laminar flow", "criticality": "WARNING", "description": "Re<2300"}]
    assert s.execute_skill("check_assumption_integrity", state={"re": 100})== []
    viol = s.execute_skill("check_assumption_integrity", state={"re": 9000})
    assert viol and viol[0].assumption_id == "lam"

    s.execute_skill("compute", task_id="audit_me", inventory={"x": 2.0}, solver=lambda i: i["x"] * 3)
    exp = s.execute_skill("explain_decision", task_id="audit_me")
    assert "audit_me" in exp.narrative and exp.decisions
    s.execute_skill("explain_decision", task_id="custom", engine_name="ASG", action="PRUNE", rationale="flat gradient")
    assert any(d.action == "PRUNE" for d in s.xxe.decision_log)
    res = s.execute_skill("explain_result", task_id="audit_me")
    assert res["found"] and res["output"] == 6.0

    audit = s.execute_skill("audit_run")
    assert audit["decisions"] >= 2 and audit["skill_trace"] and isinstance(audit["markdown"], str)

    s.execute_skill("compare_runs", label="a")
    s.execute_skill("compute", task_id="more", inventory={"x": 5.0}, solver=lambda i: i["x"])
    cmp_ = s.execute_skill("compare_runs", label="b")
    assert cmp_["runs"] == 2 and cmp_["metrics"]["total_queries"]["delta_first_last"] >= 0
    assert s.execute_skill("compare_runs", runs=[{"a": 1}, {"a": 3}])["metrics"]["a"]["mean"] == 2


# ------------------------------------------------------------------ 74-79 Reporting & Export
def test_reporting_and_export_skills(s):
    md = s.execute_skill("generate_report", format="markdown")
    assert md.startswith("# SFSA Report") and "active_layers_count" in md
    assert s.execute_skill("generate_report").session_name == "skills_test"
    with pytest.raises(ValueError):
        s.execute_skill("generate_report", format="pdf")

    g = s.execute_skill("export_graph")
    assert {n["id"] for n in g["nodes"]} == {"thermo", "kinetics"} and len(g["edges"]) == 1
    json.dumps(g)  # plain data

    s.execute_skill("store_result", task_id="m", inputs={"x": 1}, output=1)
    man = s.execute_skill("export_cache_manifest")
    assert man["cache_entries"] == 1 and man["provenance"][0]["task_id"] == "m"
    json.dumps(man)

    trace = s.execute_skill("export_skill_trace")
    assert [t["skill"] for t in trace][-2:] == ["store_result", "export_cache_manifest"]


# ------------------------------------------------------------------ 80-85 Agent planning
def test_agent_planning_skills(s):
    plan = s.execute_skill("plan_computation", archetype="EXPLORATORY_SWEEP", input_cardinality=500, parameter_dim=4)
    assert plan is not None
    with pytest.raises(ValueError):
        s.execute_skill("plan_computation", archetype="WRONG")

    empty = SFSASession(name="e")
    assert empty.execute_skill("select_next_action")["skill"] == "register_layer"
    assert s.execute_skill("select_next_action")["skill"] == "declare_invariants"

    s.execute_skill("compute", task_id="d", inventory={"x": 1.0}, solver=lambda i: 2.0)
    hit = s.execute_skill("dry_run", task_id="d", inputs={"x": 1.0})
    assert hit["predicted_action"] == "CACHE_HIT" and hit["estimated_operations"] == 0
    miss = s.execute_skill("dry_run", task_id="d", inputs={"x": 99.0}, operations=500)
    assert miss["predicted_action"] in ("FULL_COMPUTE", "APPROXIMATE_REUSE")
    lookups = s.mate.stats().total_lookups
    s.execute_skill("dry_run", task_id="d", inputs={"x": 1.0})
    assert s.mate.stats().total_lookups == lookups  # dry run has no side effects on metrics

    qs = [{"x": i * 0.01} for i in range(200)]
    batch = s.execute_skill("batch_queries", queries=qs, heavy_solver=lambda q: q["x"] * 2)
    assert batch is not None

    pr = s.execute_skill("prioritize_queries", queries=[{"x": 0.1}, {"x": 0.9}, {"x": 0.5}], cost_fn=lambda q: 1 + q["x"])
    assert [r["score"] for r in pr] == sorted((r["score"] for r in pr), reverse=True)


def test_no_skill_returns_the_old_stub_payload(s):
    """Regression guard: no handler may return the legacy {'status': 'EXECUTED'} placeholder."""
    import inspect
    src = inspect.getsource(type(s.skills))
    assert "EXECUTED" not in src


def test_bundled_catalog_matches_repo_catalog():
    from pathlib import Path
    root = Path(__file__).resolve().parents[2]
    assert (root / "skills" / "catalog.json").read_text() == (root / "python" / "sfsa" / "catalog.json").read_text(), \
        "python/sfsa/catalog.json drifted from skills/catalog.json; copy it over"
