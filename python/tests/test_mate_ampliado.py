"""
Tests for MATE Ampliado (Operational Memory & Speculative Mechanism Battery).

Part of SFSA (Standard Framework for Scientific Advancement)
Author & Protocol Creator: Alejo Malia
License: CC BY 4.0
"""

import pytest
from sfsa.mate import (
    MATEEngine,
    MATEStatus,
    ReuseLevel,
    MechanismStatus,
    MechanismCard,
)


def test_mate_multilevel_lookup_l0_and_l1():
    mate = MATEEngine(cache_precision_decimals=4)

    # 1. Fresh run (L5 Full compute)
    res1 = mate.compute_projected(
        task_id="kinetic_energy",
        inputs={"mass": 2.0, "velocity": 10.0},
        solver=lambda inp: 0.5 * inp["mass"] * (inp["velocity"] ** 2),
    )
    assert res1.value == 100.0
    assert res1.cached is False
    assert res1.reuse_level == ReuseLevel.L5

    # 2. Exact match (L0 Zero-compute)
    res_l0 = mate.compute_projected(
        task_id="kinetic_energy",
        inputs={"mass": 2.0, "velocity": 10.0},
        solver=lambda inp: (_ for _ in ()).throw(RuntimeError("Should not be called")),
    )
    assert res_l0.value == 100.0
    assert res_l0.cached is True
    assert res_l0.reuse_level == ReuseLevel.L0
    assert mate.stats().l0_exact_hits == 1

    # 3. Approximate neighbor match (L1 within 2% tolerance)
    res_l1 = mate.compute_projected(
        task_id="kinetic_energy",
        inputs={"mass": 2.01, "velocity": 10.02}, # ~0.5% perturbation
        solver=lambda inp: (_ for _ in ()).throw(RuntimeError("Should not be called")),
    )
    assert res_l1.value == 100.0
    assert res_l1.cached is True
    assert res_l1.reuse_level == ReuseLevel.L1
    assert mate.stats().l1_approx_hits == 1


def test_mate_speculative_battery_and_mechanism_learning():
    mate = MATEEngine(spec_mode="bounded", max_spec_chains=2)

    # Define official heavy solver
    def dense_solver(inp):
        return inp["x"] * 10.0 + 5.0

    # Define candidate alternative chains
    candidates = [
        {
            "chain": ["AMF_LOW", "UAS"],
            "eval_fn": lambda inp: inp["x"] * 10.0 + 5.02, # Very close (~0.2% error)
            "cost_factor": 0.25, # 4x cheaper
            "tolerance": 0.05,
            "shortcuts": {"fidelity": "LOW", "early_stop": True},
        },
        {
            "chain": ["BAD_CHAIN"],
            "eval_fn": lambda inp: inp["x"] * 2.0, # Completely wrong output
            "cost_factor": 0.10,
            "tolerance": 0.05,
        },
    ]

    res = mate.compute_projected(
        task_id="fluid_pressure",
        inputs={"x": 3.0},
        solver=dense_solver,
        candidate_chains=candidates,
    )

    assert res.value == 35.0
    assert len(res.speculative_discoveries) == 1
    discovered_card = res.speculative_discoveries[0]
    assert discovered_card.chain == ["AMF_LOW", "UAS"]
    assert discovered_card.status == MechanismStatus.CANDIDATE
    assert discovered_card.expected_cost == 0.25

    # Check negative knowledge captured for BAD_CHAIN
    pattern = mate.synthesize_pattern_signature("fluid_pressure", {"x": 3.0})
    assert pattern in mate.negative_knowledge
    assert any("BAD_CHAIN" in f["chain"] for f in mate.negative_knowledge[pattern])


def test_mate_policy_promotion_and_governance():
    mate = MATEEngine()

    card = MechanismCard(
        id="mech_flow_opt",
        pattern="navier_stokes::laminar",
        chain=["SRA_REDUCE", "AMF_MID"],
        expected_cost=0.30,
        expected_quality=0.98,
        status=MechanismStatus.CANDIDATE,
        model_version="v1.0",
    )
    mate.cards[card.id] = card
    mate.plans_by_pattern["navier_stokes::laminar"] = [card.id]

    # Promote to TRUSTED
    promoted = mate.promote("mech_flow_opt")
    assert promoted is True
    assert mate.cards["mech_flow_opt"].status == MechanismStatus.TRUSTED

    # Promote to DEFAULT
    mate.promote("mech_flow_opt", to_default=True)
    assert mate.cards["mech_flow_opt"].status == MechanismStatus.DEFAULT

    # Explain mechanism
    explanation = mate.explain("mech_flow_opt")
    assert "mech_flow_opt" in explanation
    assert "SRA_REDUCE -> AMF_MID" in explanation
    assert "speedup" in explanation.lower()

    # Reject mechanism
    mate.reject("mech_flow_opt", reason="Turbulence transition observed")
    assert mate.cards["mech_flow_opt"].status == MechanismStatus.REJECTED
    assert len(mate.cards["mech_flow_opt"].failures) == 1

    # Invalidate by model version upgrade
    card2 = MechanismCard(id="mech_v1", pattern="heat", chain=["ICR"], model_version="v1.0")
    mate.cards[card2.id] = card2
    invalidated = mate.invalidate("v2.0")
    assert invalidated >= 1
    assert mate.cards["mech_v1"].status == MechanismStatus.REJECTED
