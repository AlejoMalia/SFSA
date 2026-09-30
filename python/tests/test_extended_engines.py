"""
Tests for the 9 extended SFSA engines:
UQE, UDE, SME, DAE, SYE, PBE, RTE, RME, and LDR (Laboratory Data Repository).
"""

import pytest
import math
from sfsa import (
    SFSASession,
    UncertaintyPropagationEngine,
    UncertaintyInterval,
    UnitDimensionalEngine,
    DimensionVector,
    SurrogateModelingEngine,
    DataAssimilationEngine,
    SymbolicEquivalenceEngine,
    ParallelBatchEngine,
    RobustnessTestingEngine,
    ReproducibilityManifestEngine,
    LaboratoryDataRepository,
    DatasetTable,
)


def test_uqe_uncertainty_propagation():
    uqe = UncertaintyPropagationEngine()

    a = UncertaintyInterval(nominal=10.0, uncertainty=1.0)
    b = UncertaintyInterval(nominal=5.0, uncertainty=0.5)

    sum_res = uqe.combine_binary(a, b, "+")
    assert sum_res.nominal == 15.0
    assert math.isclose(sum_res.uncertainty, math.sqrt(1.0**2 + 0.5**2), rel_tol=1e-4)

    prod_res = uqe.combine_binary(a, b, "*")
    assert prod_res.nominal == 50.0

    # General nonlinear propagation via numerical Jacobian
    inputs = {
        "x": UncertaintyInterval(nominal=2.0, uncertainty=0.1),
        "y": UncertaintyInterval(nominal=3.0, uncertainty=0.2),
    }
    report = uqe.propagate_general(
        function=lambda p: p["x"] ** 2 + p["y"],
        inputs=inputs,
    )
    # nominal = 2^2 + 3 = 7.0
    assert report.output_interval.nominal == 7.0
    assert report.output_interval.uncertainty > 0.0
    assert len(report.dominant_contributors) == 2


def test_ude_unit_dimensional_engine():
    ude = UnitDimensionalEngine()

    dim_length, scale_l = ude.parse_unit("km")
    assert dim_length.length == 1
    assert scale_l == 1000.0

    # Conversions
    val_bars = ude.convert(200000.0, "pa", "bar")
    assert math.isclose(val_bars, 2.0, rel_tol=1e-5)

    val_kj = ude.convert(5000.0, "j", "kj")
    assert math.isclose(val_kj, 5.0, rel_tol=1e-5)

    # Dimensional compatibility checks
    compatible, _ = ude.verify_compatibility("pa", "bar")
    assert compatible

    incompatible, err = ude.verify_compatibility("pa", "meter")
    assert not incompatible
    assert "Incompatible" in err


def test_sme_surrogate_modeling():
    sme = SurrogateModelingEngine()

    # Quadratic function: f(x) = x^2
    points = [{"x": float(i)} for i in range(10)]
    values = [float(i**2) for i in range(10)]

    surrogate = sme.fit_from_history("quad_surrogate", points, values)
    pred_val, unc = surrogate.predict({"x": 4.0})
    # Point is exactly in training data
    assert math.isclose(pred_val, 16.0, abs_tol=1e-5)
    assert unc == 0.0

    # Intermediate point
    pred_mid, unc_mid = surrogate.predict({"x": 4.5})
    assert 16.0 < pred_mid < 25.0
    assert unc_mid > 0.0

    # AMF-compatible solver closure
    amf_solver = sme.create_amf_solver("quad_surrogate")
    val, u = amf_solver({"x": 4.0})
    assert math.isclose(val, 16.0, abs_tol=1e-5)


def test_dae_data_assimilation():
    dae = DataAssimilationEngine(tolerance=1e-4, max_iterations=50)

    # True parameter: k = 2.5
    # y = k * x
    experimental_data = [
        {"x": 1.0, "observed": 2.5},
        {"x": 2.0, "observed": 5.0},
        {"x": 3.0, "observed": 7.5},
        {"x": 4.0, "observed": 10.0},
    ]

    def model_fn(inputs, params):
        return params["k"] * inputs["x"]

    result = dae.calibrate(
        experimental_data=experimental_data,
        model_fn=model_fn,
        initial_params={"k": 1.0},
        target_key="observed",
        param_bounds={"k": (0.5, 5.0)},
    )

    assert result.converged
    assert math.isclose(result.calibrated_parameters["k"], 2.5, abs_tol=0.1)
    assert result.final_rmse < 0.1
    assert result.r_squared > 0.95


def test_sye_symbolic_equivalence():
    sye = SymbolicEquivalenceEngine()

    simplified = sye.simplify("0 * x + 1 * y + 0")
    assert simplified.simplified_expression.strip() == "y"
    assert simplified.operations_eliminated_count >= 2

    # Equivalence check
    assert sye.are_equivalent("0 * a + b", "1 * b")
    assert not sye.are_equivalent("x + 1", "x + 2")


def test_pbe_parallel_batch():
    pbe = ParallelBatchEngine(max_workers=2)

    tasks = [{"val": i} for i in range(10)]
    summary = pbe.map_concurrent(
        items=tasks,
        worker_fn=lambda t: t["val"] * 2,
    )

    assert summary.total_items == 10
    assert summary.successful_items == 10
    assert summary.failed_items == 0
    assert summary.results[3] == 6


def test_rte_robustness_testing():
    rte = RobustnessTestingEngine()

    def model_fn(p):
        return p["x"] * 2.0 + p["y"]

    report = rte.stress_test(
        base_inputs={"x": 10.0, "y": 5.0},
        model_fn=model_fn,
        perturbation_percentages=[0.01, 0.05],
    )

    assert report.is_robust
    assert report.fragility_score < 0.5
    assert report.condition_number > 0.0


def test_rme_reproducibility_manifest():
    rme = ReproducibilityManifestEngine()

    manifest = rme.generate_manifest(
        session_name="VerificationSession",
        engine_count=32,
        extra_metadata={"experiment_id": "EXP-900"},
    )

    assert manifest.session_name == "VerificationSession"
    assert manifest.active_engine_count == 32
    assert manifest.cryptographic_seal != ""
    assert manifest.platform_info["system"] != ""
    assert manifest.environment_metadata["experiment_id"] == "EXP-900"


def test_ldr_laboratory_data_repository():
    ldr = LaboratoryDataRepository()

    def solar_flux_model(p):
        distance_au = p["distance_au"]
        albedo = p["albedo"]
        solar_const = 1361.0
        flux = (solar_const / (distance_au ** 2)) * (1.0 - albedo)
        temp_eq = ((flux / (4.0 * 5.67e-8)) ** 0.25)
        return {"absorbed_flux": flux, "temp_equilibrium_k": temp_eq}

    sweeps = {
        "distance_au": [0.72, 1.0, 1.52], # Venus, Earth, Mars
        "albedo": [0.1, 0.3, 0.6],
    }

    table = ldr.synthesize_reference_table(
        table_id="planetary_radiation_baseline",
        name="Planetary Absorbed Flux and Equilibrium Temp Dataset",
        model_fn=solar_flux_model,
        parameter_sweeps=sweeps,
        description="Reference empirical matrix for planetary temperature baselines",
    )

    assert table.table_id == "planetary_radiation_baseline"
    assert len(table.rows) == 9
    assert "distance_au" in table.columns
    assert "absorbed_flux" in table.columns
    assert "temp_equilibrium_k" in table.summary_stats

    # Markdown rendering
    md = table.to_markdown(max_rows=5)
    assert "| distance_au |" in md
    assert "| temp_equilibrium_k |" in md
    assert "... (4 additional rows in repository)" in md

    # Nearest-neighbor interpolation
    interp_temp = ldr.interpolate_from_table(
        table_id="planetary_radiation_baseline",
        target_point={"distance_au": 1.0, "albedo": 0.3},
        target_output_key="temp_equilibrium_k",
    )
    assert interp_temp is not None
    assert 240.0 < interp_temp < 270.0

    # CSV export
    csv_text = ldr.export_csv("planetary_radiation_baseline")
    assert "distance_au,albedo,absorbed_flux,temp_equilibrium_k" in csv_text


def test_session_extended_engines_and_ldr():
    session = SFSASession(name="DeepScienceSession")
    
    # 39 engines active
    report = session.generate_report()
    assert report.active_engines_count == 39

    # LDR integration via session
    def model_fn(p):
        return {"output_metric": p["p1"] * 10.0 + p["p2"]}

    table = session.synthesize_dataset(
        table_id="session_test_table",
        name="Session Test Dataset",
        model_fn=model_fn,
        parameter_sweeps={"p1": [1.0, 2.0], "p2": [0.1, 0.2]},
    )

    assert table.table_id == "session_test_table"
    assert len(table.rows) == 4
    assert session.get_dataset("session_test_table") is not None
