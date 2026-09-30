"""
Tests for the 16 newly added SFSA engines (AMF, ASG, SRA, UAS, CPE, CAE, DIE, TBE, PKE, LSE, RFE, AIE, CQE, STE, LKE, TIL)
and the 85-Skills Catalog.
"""

import pytest
from sfsa import (
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
    TagType,
    SKILL_DEFINITIONS,
)


def test_amf_adaptive_multi_fidelity():
    amf = AdaptiveMultiFidelityEngine(default_tolerance=0.05)
    
    # Case 1: cheap model is accurate (low uncertainty)
    decision = amf.evaluate(
        task_id="thermo_eval",
        inputs={"T": 300.0},
        cheap_solver=lambda inp: (inp["T"] * 2.0, 0.02),
        expensive_solver=lambda inp: inp["T"] * 2.05,
    )
    assert decision.selected_level == FidelityLevel.CHEAP
    assert not decision.escalated
    assert decision.value == 600.0

    # Case 2: cheap model has high uncertainty -> escalates
    decision2 = amf.evaluate(
        task_id="thermo_eval_2",
        inputs={"T": 300.0},
        cheap_solver=lambda inp: (inp["T"] * 2.0, 0.25),
        expensive_solver=lambda inp: inp["T"] * 2.05,
    )
    assert decision2.selected_level == FidelityLevel.HIGH
    assert decision2.escalated
    assert decision2.value == 615.0


def test_asg_adaptive_sampling():
    asg = AdaptiveSamplingEngine(min_euclidean_distance=0.1)
    pt1 = {"x": 0.0, "y": 0.0}
    pt2 = {"x": 0.02, "y": 0.01} # Very close
    pt3 = {"x": 0.8, "y": 0.9}   # Distant

    asg.record_evaluation(pt1, 10.0)
    cand_close = asg.evaluate_candidate(pt2, uncertainty_estimator=lambda p: 0.05)
    cand_far = asg.evaluate_candidate(pt3)

    assert cand_close.skip_recommended
    assert not cand_far.skip_recommended


def test_sra_sensitivity_and_reduction():
    sra = SensitivityReductionAnalyzer(sensitivity_threshold=0.1)
    
    # y = 10 * x1 + 0.001 * x2
    inputs = {"x1": 2.0, "x2": 5.0}
    fn = lambda p: 10.0 * p["x1"] + 0.001 * p["x2"]
    
    profiles = sra.analyze_one_at_a_time(inputs, fn)
    assert profiles[0].parameter_name == "x1"
    assert profiles[0].is_impactful
    assert not profiles[1].is_impactful

    red = sra.reduce_parameter_space(inputs, fn, target_variance_explained=0.9)
    assert red.reduced_dimension == 1
    assert "x1" in red.retained_parameters
    assert "x2" in red.pruned_parameters


def test_uas_uncertainty_aware_stopping():
    uas = UncertaintyAwareStoppingEngine(target_tolerance=1e-4)
    
    # Loop at iteration 5 with tiny residual
    eval_res = uas.evaluate_step(
        iteration=5,
        current_value=1.414213,
        previous_value=1.414210,
        max_planned_iterations=100,
        estimated_uncertainty=1e-5,
    )
    assert eval_res.should_stop
    assert eval_res.iterations_saved == 95


def test_cpe_provenance_and_approximate_reuse():
    cpe = ComputationalProvenanceEngine(approximate_tolerance=0.03)
    cpe.register_result(task_id="rate_calc", inputs={"T": 500.0, "P": 1.0}, output=42.0)

    # 1. Exact match
    res_exact = cpe.assess_reuse(task_id="rate_calc", target_inputs={"T": 500.0, "P": 1.0})
    assert res_exact.reuse_type == ReuseType.EXACT_CACHE
    assert res_exact.value == 42.0

    # 2. Approximate match (T = 502 -> ~0.4% diff)
    res_approx = cpe.assess_reuse(task_id="rate_calc", target_inputs={"T": 502.0, "P": 1.0})
    assert res_approx.reuse_type == ReuseType.APPROXIMATE_REUSE
    assert res_approx.value == 42.0

    # 3. Incompatible (T = 650 -> 30% diff)
    res_far = cpe.assess_reuse(task_id="rate_calc", target_inputs={"T": 650.0, "P": 1.0})
    assert res_far.reuse_type == ReuseType.FULL_COMPUTATION


def test_cae_constraint_awareness():
    cae = ConstraintAwarenessEngine(min_support_for_inference=3)
    cae.add_explicit_constraint(lambda inp: (inp.get("temp", 0) <= 600, "temp exceeds 600 K"))

    # Explicit check
    ok, err = cae.validate_inputs({"temp": 650})
    assert not ok
    assert "Explicit constraint violated" in err

    # Inferred cuts check
    for _ in range(4):
        cae.record_infeasibility({"pressure": 15.0})
    ok_p, err_p = cae.validate_inputs({"temp": 300, "pressure": 18.0})
    assert not ok_p
    assert "Inferred cut boundary violated" in err_p


def test_die_discrepancy_intelligence():
    die = DiscrepancyIntelligenceEngine()
    
    # Case 1: negligible noise
    analysis_num = die.analyze("solver_a", 100.0, "solver_b", 100.5)
    assert analysis_num.probable_cause == DiscrepancyCause.NUMERICAL_TOLERANCE
    assert analysis_num.reconciled_value == 100.25

    # Case 2: severe divergence
    analysis_sev = die.analyze("solver_a", 100.0, "solver_b", 250.0, reference_solver=lambda: 245.0)
    assert analysis_sev.probable_cause == DiscrepancyCause.REGIME_BREAKDOWN
    assert analysis_sev.reconciled_value == 245.0


def test_tbe_temporal_budget():
    tbe = TemporalBudgetEngine(total_budget_seconds=10.0)
    alloc = tbe.request_allocation("task_1", expected_cost_seconds=1.0)
    assert alloc.can_proceed
    assert alloc.allocated_seconds > 0.0


def test_pke_partial_knowledge():
    pke = PartialKnowledgeEngine()
    pke.capture("sim_opt", iteration=10, estimate=35.0, lower_bound=30.0, upper_bound=45.0)
    pke.capture("sim_opt", iteration=20, estimate=38.0, lower_bound=36.0, upper_bound=41.0)

    best_low, best_up = pke.get_tightest_bounds("sim_opt")
    assert best_low == 36.0
    assert best_up == 41.0


def test_lse_landscape_structure():
    lse = LandscapeStructureEngine()
    bounds = {"x": (0.0, 1.0), "y": (0.0, 1.0)}
    # Flat function
    feat_flat = lse.probe_region(bounds, lambda p: 5.0)
    assert feat_flat.topology == LandscapeTopology.FLAT_PLATEAU


def test_rfe_result_forgetting():
    rfe = ResultForgettingEngine()
    rfe.track_entry("key_cheap", recompute_cost_ms=0.5)
    score = rfe.assess_retention("key_cheap")
    assert score is not None
    assert score.retention_score > 0.0


def test_aie_assumption_integrity():
    aie = AssumptionIntegrityEngine()
    aie.register_assumption(
        assumption_id="laminar_flow",
        name="Laminar Flow Limit",
        condition_fn=lambda st: (st.get("reynolds", 0) < 2300, "Reynolds number exceeds laminar limit (Re >= 2300)"),
        criticality="SWITCH_MODEL",
    )
    violations = aie.audit_state({"reynolds": 3500})
    assert len(violations) == 1
    assert violations[0].assumption_id == "laminar_flow"


def test_cqe_query_compression():
    cqe = QueryCompressionEngine(clustering_radius=0.1)
    queries = [
        {"temp": 300.0},
        {"temp": 301.0},
        {"temp": 302.0},
        {"temp": 500.0},
        {"temp": 501.0},
    ]
    res = cqe.compress_and_solve(queries, lambda q: q["temp"] * 2.0)
    assert res.representative_count == 2
    assert len(res.reconstructed_outputs) == 5
    assert res.compute_reduction_pct == 60.0


def test_ste_scientific_thematic():
    ste = ScientificThematicEngine()
    report = ste.analyze_model(
        layer_names=["chemical_kinetics_layer", "reaction_rate"],
        variable_names=["arrhenius_activation_energy", "temp_k", "catalysis_flux"],
    )
    assert len(report.primary_themes) > 0
    assert report.primary_themes[0][0] in ("chemical_kinetics", "thermodynamics")
    assert len(report.thematic_gaps) > 0


def test_lke_literature_knowledge():
    lke = LiteratureKnowledgeEngine()
    proposals = lke.propose_resources(primary_domains=["chemical_kinetics", "thermodynamics"], limit=3)
    assert len(proposals) > 0
    assert proposals[0].url.startswith("http")


def test_til_tag_index_linking():
    til = TagIndexLinkingEngine()
    t1 = til.add_or_update_tag("kinetics", "Chemical Kinetics", TagType.DOMAIN, weight_increment=0.5)
    assert t1.weight == 0.5
    til.pin_tag("kinetics")
    assert t1.status == "pinned"

    profile = til.make_search_profile()
    assert "Chemical Kinetics" in profile.must_include

    lib = til.export_tag_library()
    assert lib["total_tags"] == 1


def test_session_orchestrator_and_85_skills():
    session = SFSASession(name="Comprehensive_SFSA_Test")
    assert session.generate_report().active_engines_count == 39
    assert len(SKILL_DEFINITIONS) == 85

    # Test skills dispatch
    # Skill 1: create_session
    res1 = session.execute_skill(1)
    assert res1 == session

    # Skill 8: register_layer
    layer = session.execute_skill("register_layer", layer_id="thermo", initial_state={"temp": 300.0})
    assert layer.layer_id == "thermo"

    # Skill 44: analyze_sensitivity
    sens = session.execute_skill(
        "analyze_sensitivity",
        base_inputs={"a": 1.0, "b": 10.0},
        objective_fn=lambda p: p["a"] * 5.0 + p["b"] * 0.1,
    )
    assert len(sens) == 2

    # Skill 56: analyze_themes
    thematic = session.execute_skill("analyze_themes")
    assert thematic.confidence > 0.0

    # Skill 61: search_literature
    lit = session.execute_skill("search_literature", domains=["thermodynamics"], limit=2)
    assert len(lit) > 0

    # Verify skill execution audit trace
    rep = session.generate_report()
    assert rep.skills_executed_count >= 5
