"""Regression tests for core-engine defects found during the framework diagnosis."""
import math

import pytest

from sfsa import SFSASession
from sfsa.icr import ICREngine
from sfsa.lke import SourceType


def test_icr_never_fabricates_zero_result():
    icr = ICREngine()
    value, prof = icr.optimize_and_execute("cos0", {"x": 0.0}, lambda p: math.cos(p["x"]))
    assert value == 1.0
    assert any("DenseFallback" in o for o in prof.optimizations_applied)


def test_icr_zero_pruning_only_with_declared_answer():
    icr = ICREngine()
    value, prof = icr.optimize_and_execute("lin", {"x": 0.0}, lambda p: 99, zero_input_result=0.0, estimated_dense_ops=100)
    assert value == 0.0 and prof.executed_operations == 1 and icr.total_operations_avoided == 99


def test_icr_shortcut_failure_falls_back_to_exact_solver():
    icr = ICREngine()
    v, prof = icr.optimize_and_execute("t", {"x": 1.0}, lambda p: 7.0, lambda p: 1 / 0, lambda p: True)
    assert v == 7.0 and any("ShortcutRejected" in o for o in prof.optimizations_applied)
    v, _ = icr.optimize_and_execute("t", {"x": 1.0}, lambda p: 7.0, lambda p: float("nan"))
    assert v == 7.0
    v, prof = icr.optimize_and_execute("t", {"x": 1.0}, lambda p: 7.0, estimated_dense_ops=0)
    assert v == 7.0 and prof.reduction_percentage == 0.0


def test_compute_with_analytical_shortcut_accumulates_avoided_ops():
    s = SFSASession(name="t")
    res = s.compute("sum", {"n": 100.0}, solver=lambda i: sum(range(int(i["n"]) + 1)),
                    analytical_shortcut=lambda i: i["n"] * (i["n"] + 1) / 2, estimated_dense_ops=500)
    assert res.value == 5050.0
    assert s.icr.total_operations_avoided == 500


def test_fln_rejects_cycles_at_connect_time():
    s = SFSASession(name="t")
    for n in "abc":
        s.register_layer(n, {})
    s.connect_layers("a", "b", lambda x, y: {})
    s.connect_layers("b", "c", lambda x, y: {})
    with pytest.raises(ValueError, match="Cyclic"):
        s.connect_layers("c", "a", lambda x, y: {})
    with pytest.raises(ValueError, match="Cyclic"):
        s.connect_layers("a", "a", lambda x, y: {})
    assert s.update_layer("a", {"k": 1}) == {"a": 2, "b": 2, "c": 2}  # still updatable


def test_fln_update_is_atomic_when_transformer_fails():
    s = SFSASession(name="t")
    s.register_layer("src", {"v": 1.0})
    s.register_layer("mid", {"w": 1.0})
    s.register_layer("dst", {"z": 1.0})
    s.connect_layers("src", "mid", lambda a, b: {"w": a["v"] * 2})
    s.connect_layers("mid", "dst", lambda a, b: {"z": 1 / (a["w"] - 6.0)})  # singular when v == 3
    with pytest.raises(ZeroDivisionError):
        s.update_layer("src", {"v": 3.0})
    assert s.fln.get_layer("src").state["v"] == 1.0
    assert s.fln.get_layer("mid").state["w"] == 1.0
    assert [s.fln.get_layer(n).version for n in ("src", "mid", "dst")] == [1, 1, 1]


def test_fln_diamond_propagates_once_per_layer():
    s = SFSASession(name="t")
    for n in ("top", "l", "r", "bottom"):
        s.register_layer(n, {"v": 0})
    s.connect_layers("top", "l", lambda a, b: {"v": a["v"] + 1})
    s.connect_layers("top", "r", lambda a, b: {"v": a["v"] + 10})
    s.connect_layers("l", "bottom", lambda a, b: {"from_l": a["v"]})
    s.connect_layers("r", "bottom", lambda a, b: {"from_r": a["v"]})
    v = s.update_layer("top", {"v": 5})
    assert v["bottom"] == 2 and s.fln.get_layer("bottom").state == {"v": 0, "from_l": 6, "from_r": 15}


def test_tbe_rejects_invalid_requests():
    s = SFSASession(name="t")
    with pytest.raises(ValueError):
        s.tbe.request_allocation("t", -1.0)
    with pytest.raises(ValueError):
        s.tbe.request_allocation("t", 1.0, 0.0)
    assert s.tbe.request_allocation("t", 1.0).allocated_seconds > 0


def test_aie_and_cae_fail_closed_on_broken_rules():
    s = SFSASession(name="t")
    s.aie.register_assumption("bad", "Broken", lambda st: 1 / 0, "FAIL_STOP")
    viol = s.aie.audit_state({})
    assert viol and "could not be evaluated" in viol[0].diagnostic_message
    s.cae.add_explicit_constraint(lambda i: 1 / 0)
    ok, why = s.cae.validate_inputs({})
    assert not ok and "raised" in why


def test_rte_reports_singularity_as_fragile_instead_of_crashing():
    s = SFSASession(name="t")
    rep = s.rte.stress_test({"a": 1.0 + 1e-9}, lambda p: 1.0 / (p["a"] - 1.0) if p["a"] != 1.0 else 1 / 0)
    assert isinstance(rep.is_robust, bool)
    rep = s.rte.stress_test({"a": 2.0, "b": 1.0}, lambda p: 1.0 / (p["a"] - 2.0 * (p["b"] - 1.0) - 2.0 + 1e-300) if False else (
        (_ for _ in ()).throw(ZeroDivisionError()) if abs(p["a"] - 2.0) > 0 else 1.0))
    assert not rep.is_robust and any("Singularity" in d for d in rep.diagnostic_details)
    stable = s.rte.stress_test({"a": 2.0}, lambda p: p["a"] * 3.0)
    assert stable.is_robust


def test_lke_source_type_filter_applies_before_limit():
    s = SFSASession(name="t")
    out = s.lke.propose_resources(["physics"], limit=2, source_types=[SourceType.CODE_METHODS])
    assert out and all(p.source_type == SourceType.CODE_METHODS for p in out)


def test_mate_project_trajectory_is_a_real_check():
    s = SFSASession(name="t")
    assert s.mate.project_trajectory("t", {"x": 1}, [lambda i: i["x"] > 0])
    assert not s.mate.project_trajectory("t", {"x": -1}, [lambda i: i["x"] > 0])
    assert not s.mate.project_trajectory("t", {}, [lambda i: i["missing"] > 0])  # raising invariant = violated
    assert s.mate.project_trajectory("t", {"x": 1}, [lambda i: (True, "")])
    assert not s.mate.project_trajectory("t", {"x": 1}, [lambda i: (False, "no")])


def test_session_pareto_and_projection_wrappers_work():
    from sfsa.path import TransitionStep
    s = SFSASession(name="t")
    s.register_layer("a", {"x": 1.0, "y": 2.0})
    s.register_layer("b", {"x": 1.0, "y": 2.0})
    assert s.project_layers("a", "b").normalized_vector_distance == pytest.approx(0.0, abs=1e-9)
    with pytest.raises(KeyError):
        s.project_layers("a", "ghost")
    s.path.register_step(TransitionStep("up", "up", 1.0, 1.0, 1.0, {"T": 10.0}))
    paths = s.find_pareto_pathways({"T": 0.0}, {"T": 30.0})
    assert paths and len(paths[0].steps) == 3


def test_rme_seal_covers_all_fields_and_verifies():
    import dataclasses
    s = SFSASession(name="t")
    m = s.rme.generate_manifest("x", 39, {"note": "a"})
    assert s.rme.verify_manifest(m)
    assert not s.rme.verify_manifest(dataclasses.replace(m, environment_metadata={"note": "b"}))
    assert not s.rme.verify_manifest(dataclasses.replace(m, platform_info={**m.platform_info, "machine": "other"}))
    assert not s.rme.verify_manifest(dataclasses.replace(m, active_engine_count=1))


def test_cae_cut_is_revoked_by_feasible_points_in_blocked_region():
    from sfsa.cae import ConstraintAwarenessEngine
    cae = ConstraintAwarenessEngine(min_support_for_inference=3)
    for p in (10.0, 11.0, 12.0):
        cae.record_infeasibility({"p": p})
    assert cae.inferred_constraints[0].condition_op == ">="
    assert not cae.validate_inputs({"p": 50.0})[0]
    assert cae.validate_inputs({"p": 5.0})[0]
    cae.record_feasibility({"p": 40.0})  # success above the failures: the upper cut is no longer sound
    assert cae.inferred_constraints[0].condition_op == "<="  # only the lower cut remains valid
    assert cae.validate_inputs({"p": 50.0})[0]
    assert not cae.validate_inputs({"p": 5.0})[0]
    cae.record_feasibility({"p": 2.0})  # success below the failures too: no sound cut at all
    assert cae.inferred_constraints == []


def test_cae_no_cut_when_failures_interleave_with_successes():
    from sfsa.cae import ConstraintAwarenessEngine
    cae = ConstraintAwarenessEngine(min_support_for_inference=3)
    for p in (1.0, 5.0, 9.0):
        cae.record_feasibility({"p": p})
    for p in (3.0, 7.0, 8.0):
        cae.record_infeasibility({"p": p})
    assert cae.inferred_constraints == []


def test_cae_lower_cut():
    from sfsa.cae import ConstraintAwarenessEngine
    cae = ConstraintAwarenessEngine(min_support_for_inference=3)
    for t in (-5.0, -20.0, -1.0):
        cae.record_infeasibility({"t": t})
    cae.record_feasibility({"t": 300.0})
    assert cae.inferred_constraints[0].condition_op == "<="
    assert not cae.validate_inputs({"t": -3.0})[0]
    assert cae.validate_inputs({"t": 0.5})[0]


def test_compute_feeds_cae_with_feasible_points():
    s = SFSASession(name="t")
    s.compute("c", {"x": 1.0}, lambda i: i["x"])
    assert s.cae.feasible_history == [{"x": 1.0}]


def test_compute_approximate_reuse_is_opt_in_and_version_bound():
    s = SFSASession(name="t")
    calls = []

    def solver(i):
        calls.append(i["x"])
        return i["x"] * 2

    s.compute("r", {"x": 100.0}, solver)
    assert s.compute("r", {"x": 100.5}, solver).value == 201.0 and len(calls) == 2  # default: exact only
    res = s.compute("r", {"x": 100.4}, solver, approximate_reuse_tolerance=0.01)
    assert res.cached and len(calls) == 2
    assert s.compute("r", {"x": 150.0}, solver, approximate_reuse_tolerance=0.01).value == 300.0
    s.mate.invalidate("v2")  # model changed: old provenance must not be reused
    before = len(calls)
    s.compute("r", {"x": 100.4}, solver, approximate_reuse_tolerance=0.01)
    assert len(calls) == before + 1


def test_txe_transferred_cut_semantics():
    from sfsa.txe import TransferExperienceEngine
    a = SFSASession(name="A")
    a.cae.min_support = 2
    a.cae.record_infeasibility({"temperature": 900.0})
    a.cae.record_infeasibility({"temperature": 950.0})
    a.register_layer("heat", {"temp": 1}, name="Thermal Dynamics")
    txe = TransferExperienceEngine()
    txe.capture_session_experience(a)
    b = SFSASession(name="B")
    assert txe.warm_start_session(b, domain_keywords=["Thermal Dynamics"]) >= 1
    assert not b.cae.validate_inputs({"temperature": 1000.0})[0]
    assert b.cae.validate_inputs({"temperature": 300.0})[0]
    assert b.cae.validate_inputs({"other": 1.0})[0]


def test_version_is_consistent_everywhere():
    import json
    import re
    from pathlib import Path
    import sfsa
    root = Path(__file__).resolve().parents[2]
    pyproject = (root / "python" / "pyproject.toml").read_text()
    assert re.search(r'^version = "%s"$' % re.escape(sfsa.__version__), pyproject, re.M)
    assert json.loads((root / "javascript" / "package.json").read_text())["version"] == sfsa.__version__
    assert sfsa.__version__ == "0.2.0"
