"""
tests.test_sfsa — Comprehensive Test Suite for SFSA (Python)
============================================================
Validates all 5 core engines and the unified SFSASession orchestrator:
1. MATE Engine
2. TRIADA Engine
3. Autocomplete Engine
4. Framework Layer Network (FLN)
5. In-Frame Computer Reduction (ICR)
"""

import pytest
from sfsa import (
    MATEEngine,
    MATEStatus,
    TriadaEngine,
    TriadaStage,
    AutocompleteEngine,
    ConnectionCandidate,
    GapType,
    FrameworkLayerNetwork,
    ICREngine,
    OptimizationLevel,
    SFSASession,
)


class TestMATEEngine:
    def test_memoization(self):
        engine = MATEEngine()
        calls = {"count": 0}

        def solver(inputs):
            calls["count"] += 1
            return inputs["x"] * 2.5 + inputs["y"]

        # Call 1: Fresh execution
        res1 = engine.compute_projected("task_a", {"x": 2.0, "y": 1.0}, solver)
        assert res1.status == MATEStatus.R1_EXACT
        assert res1.value == 6.0
        assert not res1.cached
        assert calls["count"] == 1

        # Call 2: Exact duplicate inputs -> O(1) cache hit
        res2 = engine.compute_projected("task_a", {"x": 2.0, "y": 1.0}, solver)
        assert res2.status == MATEStatus.R1_EXACT
        assert res2.value == 6.0
        assert res2.cached
        assert calls["count"] == 1  # Solver was not invoked again!

    def test_early_abort_on_boundary_violation(self):
        engine = MATEEngine()

        def boundary_validator(inputs):
            if inputs.get("temperature_k", 0) < 0:
                return False, "Temperature cannot be below absolute zero (0 K)"
            return True, ""

        def expensive_solver(inputs):
            # This should never be reached
            raise RuntimeError("Should have been aborted early!")

        res = engine.compute_projected(
            "thermal_calc",
            {"temperature_k": -15.0},
            expensive_solver,
            boundary_validator=boundary_validator,
        )
        assert res.status == MATEStatus.R3_INFEASIBLE
        assert res.value is None
        assert "Temperature cannot be below absolute zero" in res.diagnostic_message


class TestTriadaEngine:
    def test_successful_three_stage_pipeline(self):
        engine = TriadaEngine()

        # T1: Inventory check
        def t1_check(inv):
            if "mass_kg" not in inv or inv["mass_kg"] <= 0:
                return False, ["Missing valid positive mass_kg"]
            return True, ["All inventory requirements met"]

        # T2: Exact analytical solver
        def t2_solve(inv):
            c = 299792458.0
            return inv["mass_kg"] * (c ** 2)

        # T3: Bounded projection verification
        def t3_verify(result_energy, inv):
            if result_energy <= 0:
                return False, ["Computed energy must be strictly positive"]
            return True, ["Energy satisfies relativistic mass-energy equivalence"]

        report = engine.run_pipeline("mass_energy", {"mass_kg": 1.0}, t1_check, t2_solve, t3_verify)
        assert report.success
        assert report.failed_at_stage is None
        assert report.final_output == pytest.approx(8.987551787368176e16)

    def test_t1_fails_instantly_without_solver(self):
        engine = TriadaEngine()

        def t1_check(inv):
            return False, ["Missing reactant X in inventory"]

        def t2_solve(inv):
            raise AssertionError("Solver should never execute if T1 fails")

        def t3_verify(res, inv):
            return True, []

        report = engine.run_pipeline("reaction", {}, t1_check, t2_solve, t3_verify)
        assert not report.success
        assert report.failed_at_stage == TriadaStage.T1_INVENTORY
        assert "T1_FAIL" in report.diagnostics[0]


class TestAutocompleteEngine:
    def test_detect_and_autofill_gaps(self):
        engine = AutocompleteEngine()

        # Register a physical rule: If volume and density are known, mass = volume * density
        def mass_rule(ctx):
            if ctx.get("_target_gap").target_key == "mass_kg":
                if "volume_m3" in ctx and "density_kg_m3" in ctx:
                    return ConnectionCandidate(
                        rule_name="hydrostatic_mass_rule",
                        target_key="mass_kg",
                        derived_value=ctx["volume_m3"] * ctx["density_kg_m3"],
                        confidence=0.99,
                        source_dependencies=["volume_m3", "density_kg_m3"],
                        derivation_notes="Calculated M = V * rho",
                    )
            return None

        engine.register_rule("mass_rule", mass_rule)

        current_state = {"volume_m3": 10.0, "density_kg_m3": 1000.0}
        required_schema = {"mass_kg": "Total mass of fluid", "temperature_k": "Temperature in Kelvin"}

        filled_state, applied = engine.auto_fill(current_state, required_schema)
        assert "mass_kg" in filled_state
        assert filled_state["mass_kg"] == 10000.0
        assert len(applied) == 1
        assert applied[0].rule_name == "hydrostatic_mass_rule"


class TestFrameworkLayerNetwork:
    def test_reactive_layer_propagation(self):
        fln = FrameworkLayerNetwork()

        # Layer 1: Boundary Constants
        fln.register_layer("boundary", {"temp_celsius": 25.0})

        # Layer 2: Thermodynamics (auto-derives Kelvin)
        fln.register_layer("thermo", {"temp_kelvin": 298.15})

        # Layer 3: Pressure State (auto-derives ideal pressure P = n R T / V)
        fln.register_layer("pressure_state", {"pressure_pa": 0.0})

        # Connect boundary -> thermo: T(K) = T(C) + 273.15
        fln.connect_layers(
            "boundary",
            "thermo",
            lambda b_state, t_state: {"temp_kelvin": b_state["temp_celsius"] + 273.15}
        )

        # Connect thermo -> pressure: P = 1.0 * 8.314 * T / 0.024
        fln.connect_layers(
            "thermo",
            "pressure_state",
            lambda t_state, p_state: {"pressure_pa": round((1.0 * 8.314 * t_state["temp_kelvin"]) / 0.024, 2)}
        )

        # Trigger update on boundary: change Celsius from 25 to 100
        versions = fln.update_layer("boundary", {"temp_celsius": 100.0})

        # Verify thermo and pressure reactively updated!
        thermo_layer = fln.get_layer("thermo")
        pressure_layer = fln.get_layer("pressure_state")

        assert thermo_layer.state["temp_kelvin"] == 373.15
        assert pressure_layer.state["pressure_pa"] == pytest.approx(129272.23, 0.1)
        assert versions["thermo"] >= 2
        assert versions["pressure_state"] >= 2


class TestICREngine:
    def test_in_frame_computer_reduction_shortcut(self):
        icr = ICREngine(level=OptimizationLevel.O2_ANALYTICAL)

        def dense_solver(inputs):
            # Simulated 1000 iteration ODE loop
            val = 0.0
            for i in range(1000):
                val += inputs["x"] * 0.001
            return val

        def analytical_shortcut(inputs):
            # Exact closed-form integral
            return inputs["x"] * 1.0

        res, profile = icr.optimize_and_execute(
            task_id="integral_reduction",
            input_params={"x": 5.0},
            exact_solver=dense_solver,
            analytical_shortcut=analytical_shortcut,
            estimated_dense_ops=1000,
        )

        assert res == 5.0
        assert profile.operations_eliminated > 900
        assert profile.reduction_percentage > 90.0
        assert "ClosedFormSubstitution" in profile.optimizations_applied[0]


class TestSFSASession:
    def test_full_session_workflow(self):
        session = SFSASession(name="Quantum_Thermodynamics_Study")

        # 1. Register and connect layers
        session.register_layer("env", {"t_k": 300.0})
        session.register_layer("output", {})
        session.connect_layers("env", "output", lambda env, out: {"heat_flux": env["t_k"] * 5.67})

        session.update_layer("env", {"t_k": 400.0})
        assert session.fln.get_layer("output").state["heat_flux"] == 2268.0

        # 2. Compute with TRIADA and MATE
        res = session.compute(
            task_id="flux_density",
            inventory={"area_m2": 2.0, "flux": 2268.0},
            solver=lambda inv: inv["area_m2"] * inv["flux"]
        )
        assert res.status == MATEStatus.R1_EXACT
        assert res.value == 4536.0

        report = session.session_report()
        assert report.session_name == "Quantum_Thermodynamics_Study"
        assert report.active_layers_count == 2
        assert report.total_queries >= 1


class TestParetoPathEngine:
    def test_find_pareto_frontier(self):
        from sfsa import ParetoPathEngine, TransitionStep

        engine = ParetoPathEngine()
        engine.register_step(
            TransitionStep(
                step_id="step_fast_costly",
                name="High Energy Fast Step",
                cost=100.0,
                duration=5.0,
                feasibility=0.95,
                delta_state={"temp_k": 50.0},
            )
        )
        engine.register_step(
            TransitionStep(
                step_id="step_slow_cheap",
                name="Low Energy Slow Step",
                cost=20.0,
                duration=25.0,
                feasibility=0.90,
                delta_state={"temp_k": 50.0},
            )
        )
        engine.register_step(
            TransitionStep(
                step_id="step_dominated",
                name="Strictly Dominated Step",
                cost=120.0, # worse cost
                duration=30.0, # worse time
                feasibility=0.80, # worse feasibility
                delta_state={"temp_k": 50.0},
            )
        )

        paths = engine.find_pathways(
            initial_state={"temp_k": 250.0},
            target_state={"temp_k": 300.0},
            max_steps=2,
            tolerance=0.01,
        )

        # Should only contain non-dominated Pareto pathways
        assert len(paths) >= 2
        step_ids_in_pareto = {p.steps[0].step_id for p in paths}
        assert "step_fast_costly" in step_ids_in_pareto
        assert "step_slow_cheap" in step_ids_in_pareto
        assert "step_dominated" not in step_ids_in_pareto


class TestDimensionalProjectionEngine:
    def test_project_and_intersect_layers(self):
        from sfsa import LayerConsistencyProjector

        engine = LayerConsistencyProjector()
        layer_thermo = {"temperature_k": 1500.0, "pressure_pa": 1e6}
        layer_material = {"temperature_k": 1200.0, "yield_strength_mpa": 250.0}

        report = engine.project_and_intersect(
            layer_a_id="thermo",
            layer_a_state=layer_thermo,
            layer_b_id="materials",
            layer_b_state=layer_material,
            known_bounds={"yield_strength_mpa": (50.0, 500.0)},
        )

        assert report.total_parameters_compared == 4
        assert len(report.strongly_coupled_pairs) > 0
        assert report.normalized_vector_distance >= 0.0
        # Discovered mismatch in shared parameter 'temperature_k' (1500 K in thermo vs 1200 K in materials)
        assert len(report.inconsistencies) == 1
        assert report.inconsistencies[0].conflict_type == "VALUE_MISMATCH"
        assert report.inconsistencies[0].parameter_name == "temperature_k"

