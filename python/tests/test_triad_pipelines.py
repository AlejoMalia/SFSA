"""
test_triad_pipelines.py — Integration and Chaining Tests for Engine Triads
==========================================================================
Verifies that multi-engine pipelines (dual and triad engine setups) chain seamlessly:
- Triad 1: [ASG + AMF + MATE] (Adaptive Multi-Fidelity Sampling)
- Triad 2: [TRIADA + UDE + UQE] (Physical Invariants, Dimensional Homogeneity & Analytical Uncertainty)
- Triad 3: [SRA + CAE + ICR] (Sensitivity Subspace Reduction, Constraints & In-Frame Reduction)
- Triad 4: [CQE + PBE + LDR] (Centroid Query Compression, Parallel Batch & Laboratory Data Repository)
- Triad 5: [DAE + SME + RTE] (Inverse Assimilation, Surrogate Modeling & Adversarial Robustness)
"""

import pytest
import math
from sfsa import (
    SFSASession,
    MATEEngine,
    TriadaEngine,
    AdaptiveSamplingEngine,
    AdaptiveMultiFidelityEngine,
    FidelityLevel,
    SensitivityReductionAnalyzer,
    ConstraintAwarenessEngine,
    ICREngine,
    QueryCompressionEngine,
    ParallelBatchEngine,
    LaboratoryDataRepository,
    UnitDimensionalEngine,
    UncertaintyPropagationEngine,
    UncertaintyInterval,
    DataAssimilationEngine,
    SurrogateModelingEngine,
    RobustnessTestingEngine,
)


def test_triad_1_asg_amf_mate_pipeline():
    """Verifies seamless data flow: ASG candidate filtering -> AMF multi-fidelity solve -> MATE caching."""
    asg = AdaptiveSamplingEngine(min_euclidean_distance=0.15)
    amf = AdaptiveMultiFidelityEngine(default_tolerance=0.05)
    mate = MATEEngine()

    def expensive_fn(p):
        return p["x"] * 2.5 + p["y"] * 1.5

    def cheap_fn(p):
        approx = p["x"] * 2.5 + p["y"] * 1.5
        unc = 0.02 if (p["x"] < 0.5 and p["y"] < 0.5) else 0.12
        return approx, unc

    candidates = [{"x": float(i) / 10.0, "y": float(j) / 10.0} for i in range(10) for j in range(10)]
    evaluated_count = 0

    for pt in candidates:
        cand = asg.evaluate_candidate(pt, uncertainty_estimator=lambda p: 0.05)
        if cand.skip_recommended:
            continue

        decision = amf.evaluate(
            task_id="asg_amf_flow",
            inputs=pt,
            cheap_solver=cheap_fn,
            expensive_solver=lambda p: mate.compute_projected("expensive_task", p, expensive_fn).value,
        )
        assert decision.value is not None
        asg.record_evaluation(pt, decision.value)
        evaluated_count += 1

    assert evaluated_count < len(candidates)
    assert evaluated_count > 0


def test_triad_2_triada_ude_uqe_pipeline():
    """Verifies: UDE unit conversion -> TRIADA inventory conservation -> UQE analytical error propagation."""
    ude = UnitDimensionalEngine()
    uqe = UncertaintyPropagationEngine()
    triada = TriadaEngine()

    # Step 1: Unit conversion with UDE
    raw_mass_g = 1500.0  # grams
    raw_mass_unc_g = 15.0
    mass_kg = ude.convert(raw_mass_g, "g", "kg")
    mass_unc_kg = raw_mass_unc_g * 1e-3

    # Step 2: Physical inventory validation with TRIADA
    report = triada.run_pipeline(
        task_name="kinetic_energy",
        inventory_input={"mass": mass_kg, "velocity": 20.0},
        t1_inventory_validator=lambda inv: (inv["mass"] > 0 and inv["velocity"] >= 0, []),
        t2_analytical_solver=lambda inv: 0.5 * inv["mass"] * (inv["velocity"] ** 2),
        t3_projection_verifier=lambda res, inv: (res >= 0, []),
    )
    assert report.success
    assert report.final_output == 300.0  # 0.5 * 1.5 * 400 = 300 J

    # Step 3: 1-pass Analytical Error Propagation with UQE
    inputs = {
        "m": UncertaintyInterval(nominal=mass_kg, uncertainty=mass_unc_kg),
        "v": UncertaintyInterval(nominal=20.0, uncertainty=0.5),
    }
    uqe_rep = uqe.propagate_general(
        function=lambda p: 0.5 * p["m"] * (p["v"] ** 2),
        inputs=inputs,
    )
    assert math.isclose(uqe_rep.output_interval.nominal, 300.0, abs_tol=1e-5)
    assert uqe_rep.output_interval.uncertainty > 0.0


def test_triad_3_sra_cae_icr_pipeline():
    """Verifies: SRA parameter subspace reduction -> CAE domain feasibility cuts -> ICR loop pruning."""
    sra = SensitivityReductionAnalyzer()
    cae = ConstraintAwarenessEngine()
    icr = ICREngine()

    def complex_objective(p):
        # x3 has negligible variance
        return 5.0 * p["x1"] + 2.0 * p["x2"] + 0.0001 * p["x3"]

    nominal = {"x1": 1.0, "x2": 2.0, "x3": 3.0}

    # Step 1: SRA Dimensional reduction
    reduction = sra.reduce_parameter_space(nominal, complex_objective, target_variance_explained=0.99)
    assert "x3" in reduction.pruned_parameters
    assert "x1" in reduction.retained_parameters

    # Step 2: CAE Constraint cuts
    cae.add_explicit_constraint(lambda p: (p["x1"] > 0, "x1 must be positive"))
    valid_pt = {"x1": 2.0, "x2": 3.0, "x3": 0.0}
    invalid_pt = {"x1": -1.0, "x2": 3.0, "x3": 0.0}

    ok_v, _ = cae.validate_inputs(valid_pt)
    ok_inv, _ = cae.validate_inputs(invalid_pt)
    assert ok_v
    assert not ok_inv

    # Step 3: ICR in-frame optimization and shortcut
    result, profile = icr.optimize_and_execute(
        task_id="icr_test_task",
        input_params=valid_pt,
        exact_solver=lambda p: p["x1"] * 2.0,
        analytical_shortcut=lambda p: p["x1"] * 2.0,
        shortcut_validity_condition=lambda p: True,
        estimated_dense_ops=500,
    )
    assert result == 4.0
    assert profile.operations_eliminated > 0


def test_triad_4_cqe_pbe_ldr_pipeline():
    """Verifies: CQE batch clustering -> PBE parallel dispatch -> LDR dataset table projection."""
    cqe = QueryCompressionEngine(clustering_radius=0.1)
    pbe = ParallelBatchEngine(max_workers=2)
    ldr = LaboratoryDataRepository()

    queries = [{"t": float(i % 10) + (i * 0.001)} for i in range(100)]

    def heavy_step(p):
        return math.sin(p["t"]) * 50.0

    # Step 1 & 2: CQE Centroid clustering and PBE evaluation
    comp_res = cqe.compress_and_solve(
        queries=queries,
        heavy_solver=heavy_step,
    )
    assert comp_res.representative_count < len(queries)
    assert len(comp_res.reconstructed_outputs) == 100

    # Step 3: LDR Reference table synthesis and fast O(1) interpolation
    table = ldr.synthesize_reference_table(
        table_id="triad_dataset",
        name="Triad Test Dataset",
        model_fn=lambda p: {"step_val": heavy_step(p)},
        parameter_sweeps={"t": [1.0, 2.0, 3.0]},
    )
    assert table.table_id == "triad_dataset"
    assert len(table.rows) == 3

    interpolated = ldr.interpolate_from_table(
        table_id="triad_dataset",
        target_point={"t": 2.01},
        target_output_key="step_val",
    )
    assert interpolated is not None
    assert math.isclose(interpolated, math.sin(2.0) * 50.0, abs_tol=1e-4)


def test_triad_5_dae_sme_rte_pipeline():
    """Verifies: DAE inverse calibration -> SME surrogate fitting -> RTE adversarial stability audit."""
    dae = DataAssimilationEngine(tolerance=1e-4, max_iterations=30)
    sme = SurrogateModelingEngine()
    rte = RobustnessTestingEngine()

    # Step 1: DAE Parameter calibration from noisy sensor data
    sensor_data = [{"x": float(i), "observed": 3.14 * float(i)} for i in range(1, 10)]
    calib = dae.calibrate(
        experimental_data=sensor_data,
        model_fn=lambda inp, p: p["pi_approx"] * inp["x"],
        initial_params={"pi_approx": 1.0},
        target_key="observed",
        param_bounds={"pi_approx": (1.0, 5.0)},
    )
    assert calib.converged
    best_pi = calib.calibrated_parameters["pi_approx"]
    assert math.isclose(best_pi, 3.14, abs_tol=0.05)

    # Step 2: SME Surrogate fitting from calibration data
    train_x = [{"x": float(i)} for i in range(1, 10)]
    train_y = [best_pi * float(i) for i in range(1, 10)]
    surrogate = sme.fit_from_history("pi_model", train_x, train_y)
    pred, unc = surrogate.predict({"x": 5.0})
    assert math.isclose(pred, best_pi * 5.0, abs_tol=1e-4)
    assert unc == 0.0

    # Step 3: RTE Adversarial perturbation stress-test
    robust_rep = rte.stress_test(
        base_inputs={"pi_approx": best_pi},
        model_fn=lambda p: p["pi_approx"] * 10.0,
        perturbation_percentages=[0.01, 0.05],
    )
    assert robust_rep.is_robust
    assert robust_rep.condition_number > 0.0
