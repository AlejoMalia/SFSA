"""
Tests for SFSA Meta-Orchestration, Progress & Experimental Engines (33–39):
ORE, VOI, TXE, ELE, MRE, XXE, SRE.

Part of SFSA (Standard Framework for Scientific Advancement)
Author & Protocol Creator: Alejo Malia
License: CC BY 4.0
"""

import pytest
from sfsa.session import SFSASession
from sfsa.ore import OrchestrationRoutingEngine, QueryArchetype
from sfsa.voi import ValueInformationEngine
from sfsa.txe import TransferExperienceEngine
from sfsa.ele import ExperimentLoopEngine
from sfsa.mre import ModelRiskEngine
from sfsa.xxe import ExplanationAuditEngine
from sfsa.sre import ScheduleResourceEngine


def test_ore_pipeline_planning():
    ore = OrchestrationRoutingEngine()

    # 1. Exploratory sweep with high cardinality and 5D parameter space
    plan_sweep = ore.plan_pipeline(
        query_archetype=QueryArchetype.EXPLORATORY_SWEEP,
        input_cardinality=500,
        parameter_dim=5,
    )
    assert "CQE" in plan_sweep.active_engine_sequence
    assert "SRA" in plan_sweep.active_engine_sequence
    assert "AMF" in plan_sweep.active_engine_sequence
    assert plan_sweep.suggested_fidelity == "CHEAP_FIRST"
    assert plan_sweep.estimated_compute_reduction_pct >= 90.0

    # 2. High precision solve
    plan_solve = ore.plan_pipeline(
        query_archetype=QueryArchetype.HIGH_PRECISION_SOLVE,
    )
    assert plan_solve.active_engine_sequence == ["MRE", "CAE", "MATE", "TRIADA", "UQE"]
    assert plan_solve.suggested_fidelity == "HIGH"

    # 3. Verification audit
    plan_audit = ore.plan_pipeline(
        query_archetype=QueryArchetype.VERIFICATION_AUDIT,
    )
    assert "TRIADA" in plan_audit.active_engine_sequence
    assert "XXE" in plan_audit.active_engine_sequence


def test_voi_epistemic_decision():
    voi = ValueInformationEngine(min_evoi_threshold=0.15)

    # Candidate 1: Close to boundary (value 10.1, threshold 10.0) with high uncertainty (0.8) -> COMPUTE
    eval_compute = voi.evaluate_candidate(
        candidate_id="c1",
        predicted_value=10.1,
        epistemic_uncertainty=0.8,
        decision_threshold=10.0,
        estimated_cost=1.0,
    )
    assert eval_compute.recommendation == "COMPUTE"
    assert eval_compute.expected_value_of_information > 0.3

    # Candidate 2: Far from boundary (value 50.0, threshold 10.0) with low uncertainty (0.01) -> SKIP_LOW_VALUE
    eval_skip = voi.evaluate_candidate(
        candidate_id="c2",
        predicted_value=50.0,
        epistemic_uncertainty=0.01,
        decision_threshold=10.0,
        estimated_cost=1.0,
    )
    assert eval_skip.recommendation == "SKIP_LOW_VALUE"

    # Candidate 3: High cost with moderate EVOI -> USE_CHEAP_SURROGATE
    eval_surrogate = voi.evaluate_candidate(
        candidate_id="c3",
        predicted_value=10.2,
        epistemic_uncertainty=0.4,
        decision_threshold=10.0,
        estimated_cost=25.0,
    )
    assert eval_surrogate.recommendation == "USE_CHEAP_SURROGATE"

    # Filter candidates
    candidates = [
        {"id": "A", "val": 10.05, "unc": 0.9, "cost": 1.0},
        {"id": "B", "val": 80.0, "unc": 0.05, "cost": 1.0},
    ]
    approved = voi.filter_candidates(
        candidates=candidates,
        predict_fn=lambda c: (c["val"], c["unc"]),
        decision_threshold=10.0,
        cost_fn=lambda c: c["cost"],
    )
    assert len(approved) == 1
    assert approved[0]["id"] == "A"


def test_txe_cross_session_transfer():
    txe = TransferExperienceEngine()

    session_a = SFSASession(name="Thermodynamics_Campaign")
    session_a.cae.min_support = 2
    session_a.cae.record_infeasibility({"temperature": -5.0})
    session_a.cae.record_infeasibility({"temperature": -20.0})
    session_a.register_layer("heat_layer", {"temp": 300}, name="Thermal Dynamics")

    # Capture snapshot
    snapshot = txe.capture_session_experience(session_a)
    assert len(snapshot.priors) >= 1
    assert snapshot.framework_name == "Thermodynamics_Campaign"

    # Warm-start session B
    session_b = SFSASession(name="Propulsion_Design")
    transferred = txe.warm_start_session(session_b, domain_keywords=["Thermal Dynamics"])
    assert transferred >= 1


def test_ele_experiment_loop():
    ele = ExperimentLoopEngine()
    session = SFSASession(name="Optics_Lab")

    candidate_space = [
        {"x": 1.0, "wavelength": 400.0},
        {"x": 2.5, "wavelength": 550.0},
        {"x": 4.0, "wavelength": 700.0},
    ]

    proposal = ele.propose_next_experiment(
        candidate_space=candidate_space,
        theory_model=lambda c: c["x"] * 2.0,
        uncertainty_estimator=lambda c: c["x"] * 0.5, # x=4.0 has max uncertainty 2.0
    )
    assert proposal.target_parameters["x"] == 4.0
    assert proposal.predicted_theoretical_output == 8.0

    # Lab measurement assimilates observed value
    res = ele.close_loop(proposal, measured_lab_value=8.4, session=session)
    assert res.iteration_index == 1
    assert abs(res.discrepancy_delta - 0.4) < 1e-4
    assert len(ele.iterations) == 1


def test_mre_epistemic_validity():
    mre = ModelRiskEngine(extrapolation_threshold=0.20)
    mre.register_envelope("pressure", safe_min=1.0, safe_max=10.0, hard_min=0.0, hard_max=100.0)

    # 1. Safe input
    rep_safe = mre.assess_risk({"pressure": 5.0})
    assert rep_safe.is_safe is True
    assert rep_safe.verdict == "COMPUTE_SAFE"

    # 2. Caution extrapolation (pressure 11.5, safe range [1, 10], span 9, ratio 1.5/9 = 16.7%)
    mre_tight = ModelRiskEngine(extrapolation_threshold=0.10)
    mre_tight.register_envelope("pressure", safe_min=1.0, safe_max=10.0, hard_min=0.0, hard_max=100.0)
    rep_extrap = mre_tight.assess_risk({"pressure": 11.5})
    assert rep_extrap.is_safe is True
    assert rep_extrap.verdict == "CAUTION_EXTRAPOLATION"

    # 3. Hard limit violation
    rep_abort = mre.assess_risk({"pressure": -2.0})
    assert rep_abort.is_safe is False
    assert rep_abort.verdict == "ABORT_INVALID_REGIME"
    assert len(rep_abort.warnings) >= 1


def test_xxe_audit_narrative():
    xxe = ExplanationAuditEngine()
    xxe.record_decision("MATE", "CACHE_HIT", "Exact trajectory match found in R1 memoization", saved_operations_or_time=95.0, metadata={"task_id": "solve_t1"})
    xxe.record_decision("CAE", "CUT_DOMAIN", "Pruned negative concentration subspace", saved_operations_or_time=40.0, metadata={"task_id": "solve_t1"})

    explanation = xxe.explain_task("solve_t1")
    assert explanation.summary_verdict == "OPTIMIZED_AND_VERIFIED"
    assert len(explanation.decisions) == 2
    assert "MATE" in explanation.narrative
    assert "CAE" in explanation.narrative

    md = xxe.export_audit_markdown()
    assert "# SFSA Computational Audit Trail" in md
    assert "CACHE_HIT" in md


def test_sre_campaign_scheduler():
    sre = ScheduleResourceEngine(default_concurrency=4)

    sre.enqueue_task("task_low", inputs={}, priority_score=0.2, estimated_cost_ms=50.0)
    sre.enqueue_task("task_high", inputs={}, priority_score=0.9, estimated_cost_ms=10.0)
    sre.enqueue_task("task_mid", inputs={}, priority_score=0.5, estimated_cost_ms=20.0)

    # Highest priority task should be first
    schedule = sre.plan_campaign_schedule(budget_exhaustion_ratio=0.5)
    assert schedule.task_order[0] == "task_high"
    assert schedule.concurrency_workers == 4
    assert schedule.backpressure_active is False

    # Backpressure triggers when budget exhaustion > 0.85
    schedule_throttled = sre.plan_campaign_schedule(budget_exhaustion_ratio=0.90)
    assert schedule_throttled.backpressure_active is True
    assert schedule_throttled.concurrency_workers == 2

    # Dispatch in order
    first = sre.dispatch_next()
    assert first.task_id == "task_high"


def test_session_39_engines_integrated():
    session = SFSASession(name="Unified_Meta_Session")
    report = session.generate_report()
    assert report.active_engines_count == 39
    assert hasattr(session, "ore")
    assert hasattr(session, "voi")
    assert hasattr(session, "txe")
    assert hasattr(session, "ele")
    assert hasattr(session, "mre")
    assert hasattr(session, "xxe")
    assert hasattr(session, "sre")
