"""Regression tests for the four audit findings: UDE silent dimensionless, SYE regex rewriting,
ASG.filter_grid ignoring the uncertainty estimator, DIE labelling discretization error as a modeling assumption."""

import math

import pytest

from sfsa.asg import AdaptiveSamplingEngine
from sfsa.die import DiscrepancyCause, DiscrepancyIntelligenceEngine
from sfsa.sye import SymbolicEquivalenceEngine, parse_expression
from sfsa.ude import DimensionVector, UnitDimensionalEngine, UnitSyntaxError, UnknownUnitError

ude = UnitDimensionalEngine()


# ----------------------------------------------------------------------------------------- 1. UDE
class TestUDE:
    @pytest.mark.parametrize("expr,dim,scale", [
        ("1/year", DimensionVector(time=-1), 1 / 31557600.0),
        ("m/s", DimensionVector(length=1, time=-1), 1.0),
        ("month", DimensionVector(time=1), 31557600.0 / 12),
        ("km/h", DimensionVector(length=1, time=-1), 1000 / 3600),
        ("kg*m/s^2", DimensionVector(mass=1, length=1, time=-2), 1.0),
        ("kg m s^-2", DimensionVector(mass=1, length=1, time=-2), 1.0),
        ("J/(kg*K)", DimensionVector(length=2, time=-2, temp=-1), 1.0),
        ("W*h", DimensionVector(mass=1, length=2, time=-2), 3600.0),
        ("kWh", DimensionVector(mass=1, length=2, time=-2), 3.6e6),
        ("mol/L", DimensionVector(amount=1, length=-3), 1000.0),
        ("mW", DimensionVector(mass=1, length=2, time=-3), 1e-3),
        ("MW", DimensionVector(mass=1, length=2, time=-3), 1e6),
        ("GPa", DimensionVector(mass=1, length=-1, time=-2), 1e9),
        ("Pa^(1/2)", DimensionVector(mass=0.5, length=-0.5, time=-1), 1.0),
        ("m**2", DimensionVector(length=2), 1.0),
    ])
    def test_compound_units_resolve_with_correct_dimension_and_scale(self, expr, dim, scale):
        d, s = ude.parse_unit(expr)
        assert d == dim and math.isclose(s, scale, rel_tol=1e-12)

    @pytest.mark.parametrize("name", ["furlongz", "parsecs", "kg*bananas", "m/fortnightly", "xyz"])
    def test_unknown_unit_is_an_error_not_dimensionless(self, name):
        with pytest.raises(UnknownUnitError):
            ude.parse_unit(name)
        ok, why = ude.verify_compatibility(name, "m")
        assert ok is False and "Unknown unit" in why

    def test_unknown_unit_never_matches_dimensionless(self):
        assert ude.verify_compatibility("bananas", "dimensionless")[0] is False
        with pytest.raises(UnknownUnitError):
            ude.convert(1.0, "bananas", "fraction")

    @pytest.mark.parametrize("bad", ["m2", "s-1", "m/", "(m", "", "m^", "m^x"])
    def test_malformed_expressions_are_rejected(self, bad):
        with pytest.raises(UnitSyntaxError):
            ude.parse_unit(bad)

    def test_m2_is_not_silently_two_meters(self):
        with pytest.raises(UnitSyntaxError, match="m\\^2"):
            ude.parse_unit("m2")

    def test_conversions_of_compound_units(self):
        assert math.isclose(ude.convert(36, "km/h", "m/s"), 10.0)
        assert math.isclose(ude.convert(1, "year", "month"), 12.0)
        assert math.isclose(ude.convert(2.0, "1/year", "1/month"), 2.0 / 12.0)
        assert math.isclose(ude.convert(1, "N", "kg*m/s^2"), 1.0)
        assert math.isclose(ude.convert(3, "kWh", "MJ"), 10.8)
        assert math.isclose(ude.convert(1, "bar", "kPa"), 100.0)
        with pytest.raises(ValueError, match="mismatch"):
            ude.convert(1, "m/s", "m")

    def test_absolute_temperature_offsets(self):
        assert math.isclose(ude.convert(25, "degC", "K"), 298.15)
        assert math.isclose(ude.convert(100, "degC", "degF"), 212.0)
        assert math.isclose(ude.convert(0, "K", "degC"), -273.15)
        assert ude.verify_compatibility("degC", "K")[0]
        assert math.isclose(ude.convert(10, "degC/m", "K/m"), 10.0)           # gradients are intervals

    def test_legacy_lowercase_aliases_still_work(self):
        assert ude.parse_unit("km") == (DimensionVector(length=1), 1000.0)
        assert math.isclose(ude.convert(200000.0, "pa", "bar"), 2.0)
        assert ude.parse_unit("mpa")[1] == 1e6 and ude.parse_unit("kw")[1] == 1e3

    def test_case_sensitive_si_prefixes(self):
        assert ude.parse_unit("mW")[1] == 1e-3 and ude.parse_unit("MW")[1] == 1e6
        assert ude.parse_unit("min")[0] == DimensionVector(time=1)             # minute, not milli-inch
        assert ude.parse_unit("mol")[0] == DimensionVector(amount=1)           # mole, not milli-ol

    def test_check_sum_and_describe(self):
        assert ude.check_sum(["J", "N*m", "kg*m^2/s^2"])[0]
        ok, why = ude.check_sum(["J", "W"])
        assert not ok and "Incompatible" in why
        assert "kg^1 m^1 s^-2" in ude.describe("N")

    def test_dimension_vector_algebra(self):
        v = DimensionVector(length=1)
        t = DimensionVector(time=1)
        assert (v / t) == DimensionVector(length=1, time=-1) and (v * t) == DimensionVector(length=1, time=1)
        assert (v ** 2) == DimensionVector(length=2) and (v ** 0.5).length == 0.5
        assert DimensionVector().is_dimensionless() and DimensionVector().label() == "1"

    def test_unit_resolution_is_cached_and_stable(self):
        assert ude.parse_unit("1/year") is ude.parse_unit("1/year") or ude.parse_unit("1/year") == ude.parse_unit("1/year")


# ----------------------------------------------------------------------------------------- 2. SYE
sye = SymbolicEquivalenceEngine()


class TestSYE:
    def test_log_identity_is_recognised(self):
        r = sye.check_equivalence("log(v1/v0) + log(v2/v1)", "log(v2/v0)")
        assert r.equivalent and r.method in ("symbolic", "numeric") and r.valid_points >= 0
        assert sye.are_equivalent("log(v1/v0)+log(v2/v1)", "log(v2/v0)")

    @pytest.mark.parametrize("a,b", [
        ("(a + b)^2", "a^2 + 2*a*b + b^2"),
        ("exp(a + b)", "exp(a)*exp(b)"),
        ("sqrt(x*x)", "x"),
        ("sin(t)^2 + cos(t)^2", "1"),
        ("(x^2 - 1)/(x - 1)", "x + 1"),
        ("log(x^3)", "3*log(x)"),
        ("a/b + c/b", "(a + c)/b"),
    ])
    def test_true_identities_on_positive_reals(self, a, b):
        assert sye.are_equivalent(a, b)

    @pytest.mark.parametrize("a,b", [
        ("x + 1", "x + 2"), ("log(a*b)", "log(a) * log(b)"), ("(a + b)^2", "a^2 + b^2"),
        ("exp(a + b)", "exp(a) + exp(b)"), ("x/y", "y/x"), ("sin(x)", "x"),
    ])
    def test_false_identities_are_rejected_with_counterexample(self, a, b):
        r = sye.check_equivalence(a, b)
        assert not r.equivalent and r.counterexample is not None

    def test_real_domain_catches_log_x_squared(self):
        assert sye.are_equivalent("log(x*x)", "2*log(x)")                      # fine for x > 0
        r = sye.check_equivalence("log(x*x)", "2*log(x)", domain="real")
        assert not r.equivalent and "domain" in r.note

    def test_decimal_literals_are_not_corrupted(self):
        # the old regex rewrote "x * 0.5" to "0.5" ("x*0" matched inside the literal)
        s = sye.simplify("x * 0.5")
        assert s.simplified_expression.replace(" ", "") == "x*0.5"
        assert not sye.are_equivalent("x * 0.5", "0.5")
        assert sye.are_equivalent("x * 0.5", "x / 2")
        s2 = sye.simplify("10 * x + 1.05 * y")
        assert s2.simplified_expression.replace(" ", "") == "10*x+1.05*y"

    def test_identity_folding_and_ops_count(self):
        s = sye.simplify("0 * x + 1 * y + 0")
        assert s.simplified_expression == "y" and s.operations_eliminated_count >= 2
        assert sye.simplify("x - x").is_constant and sye.simplify("x - x").constant_value == 0.0
        assert sye.simplify("2*3 + 4").constant_value == 10.0
        assert sye.simplify("log(exp(a))").simplified_expression == "a"

    def test_division_by_x_over_x_records_its_domain_condition(self):
        s = sye.simplify("x / x")
        assert s.simplified_expression == "1" and "x != 0" in s.domain_restrictions
        e = sye.simplify("exp(log(b))")
        assert "b > 0" in e.domain_restrictions

    def test_poles_use_the_whole_denominator(self):
        s = sye.simplify("a / (b - c) + 1 / x")
        assert "Pole at b - c == 0" in s.detected_singularities and "Pole at x == 0" in s.detected_singularities
        assert sye.simplify("1 / 0").detected_singularities == ["Division by the constant 0"]

    def test_log_domain_is_reported(self):
        assert "v > 0" in sye.simplify("log(v) + 1").domain_restrictions

    @pytest.mark.parametrize("bad", ["__import__('os').system('echo hi')", "x.real", "[1, 2]", "lambda: 1", "a if b else c",
                                     "f(x)", "log(x, 2)", "x and y", "'s'", "", "1 +"])
    def test_expressions_outside_the_whitelist_are_rejected(self, bad):
        with pytest.raises(ValueError):
            parse_expression(bad)
        with pytest.raises(ValueError):
            sye.simplify(bad)

    def test_equivalence_is_deterministic(self):
        a = sye.check_equivalence("x + y", "y + x")
        b = SymbolicEquivalenceEngine().check_equivalence("x + y", "y + x")
        assert a == b

    def test_inconclusive_when_the_domain_is_empty(self):
        r = sye.check_equivalence("sqrt(0 - 1 - x*x)", "sqrt(0 - 2 - x*x)")
        assert not r.equivalent and r.method == "inconclusive"


# ----------------------------------------------------------------------------------------- 3. ASG
class TestASG:
    def test_uncertainty_estimator_changes_the_filter(self):
        """Two nearby points: skipped when uncertainty is low, kept when the estimator says it is high."""
        grid = [{"x": 0.50, "y": 0.50}, {"x": 0.52, "y": 0.50}]
        low = AdaptiveSamplingEngine(min_euclidean_distance=0.1)
        assert len(low.filter_grid(grid, uncertainty_estimator=lambda p: 0.01)) == 1
        high = AdaptiveSamplingEngine(min_euclidean_distance=0.1)
        assert len(high.filter_grid(grid, uncertainty_estimator=lambda p: 0.9)) == 2

    def test_estimator_can_be_set_at_construction(self):
        grid = [{"x": 0.5}, {"x": 0.52}]
        eng = AdaptiveSamplingEngine(min_euclidean_distance=0.1, uncertainty_estimator=lambda p: 0.9)
        assert len(eng.filter_grid(grid)) == 2
        override = AdaptiveSamplingEngine(min_euclidean_distance=0.1, uncertainty_estimator=lambda p: 0.9)
        assert len(override.filter_grid(grid, uncertainty_estimator=lambda p: 0.0)) == 1

    def test_estimator_is_called_for_each_candidate_after_the_first(self):
        calls = []
        eng = AdaptiveSamplingEngine(min_euclidean_distance=0.1)
        eng.filter_grid([{"x": 0.0}, {"x": 0.5}, {"x": 1.0}], uncertainty_estimator=lambda p: calls.append(p["x"]) or 0.5)
        assert calls == [0.5, 1.0]                                          # the first point has no neighbours to compare

    def test_gradient_estimator_is_forwarded_too(self):
        seen = []
        eng = AdaptiveSamplingEngine()
        eng.filter_grid([{"x": 0.0}, {"x": 1.0}], gradient_estimator=lambda p: seen.append(p["x"]) or 0.5)
        assert seen == [1.0]

    def test_budget_picks_the_most_informative_not_the_first(self):
        grid = [{"x": 0.0}, {"x": 0.01}, {"x": 0.5}, {"x": 1.0}]
        eng = AdaptiveSamplingEngine(min_euclidean_distance=0.001)
        eng.record_evaluation({"x": 0.0}, 1.0)
        chosen = eng.filter_grid(grid, max_budget=2)
        assert [p["x"] for p in chosen][0] == 1.0                           # farthest from the known point first
        assert len(chosen) == 2 and {"x": 0.01} not in chosen

    def test_zero_budget_selects_nothing_and_negative_is_an_error(self):
        eng = AdaptiveSamplingEngine()
        assert eng.filter_grid([{"x": 0.0}, {"x": 1.0}], max_budget=0) == [] and eng.evaluated_points == []
        with pytest.raises(ValueError):
            eng.filter_grid([{"x": 0.0}], max_budget=-1)

    def test_selected_points_have_a_pending_response_not_a_fake_zero(self):
        eng = AdaptiveSamplingEngine()
        eng.filter_grid([{"x": 0.0}, {"x": 1.0}])
        assert all(math.isnan(v) for v in eng.point_values) and len(eng.point_values) == 2

    def test_no_budget_keeps_the_original_scan_semantics(self):
        eng = AdaptiveSamplingEngine(min_euclidean_distance=0.15)
        grid = [{"x": i / 100} for i in range(101)]
        kept = eng.filter_grid(grid)
        # default estimator: unc = 2 * distance, skip needs unc < 0.1, i.e. distance < 0.05
        assert kept[0] == {"x": 0.0} and 1 < len(kept) < 101
        assert all(b["x"] - a["x"] >= 0.05 - 1e-9 for a, b in zip(kept, kept[1:]))


# ----------------------------------------------------------------------------------------- 4. DIE
die = DiscrepancyIntelligenceEngine()


def _euler(h, t_end=1.0):
    y = 1.0
    for _ in range(round(t_end / h)):
        y += h * y
    return y


class TestDIE:
    def test_same_model_different_step_is_discretization_not_modeling(self):
        r = die.analyze("euler_h0.1", _euler(0.1), "euler_h0.05", _euler(0.05), same_model=True)
        assert r.probable_cause == DiscrepancyCause.NUMERICAL_DISCRETIZATION
        assert r.probable_cause != DiscrepancyCause.MODELING_ASSUMPTION

    def test_gap_within_discretization_estimate_is_classified_as_such(self):
        r = die.analyze("euler", 2.5937, "rk4", 2.7183, discretization_error=0.2)
        assert r.probable_cause == DiscrepancyCause.NUMERICAL_DISCRETIZATION
        r2 = die.analyze("euler", 2.5937, "rk4", 2.7183, discretization_error=0.01)
        assert r2.probable_cause == DiscrepancyCause.MODELING_ASSUMPTION      # estimate too small to explain the gap

    def test_richardson_recovers_the_exact_value_for_a_first_order_method(self):
        v, err = DiscrepancyIntelligenceEngine.richardson(_euler(0.1), _euler(0.05), order=1)
        assert abs(v - math.e) < abs(_euler(0.05) - math.e) / 5               # far better than the fine solution
        assert math.isclose(err, abs(v - _euler(0.05)))

    def test_analyze_refinement_reconciles_by_extrapolation(self):
        r = die.analyze_refinement("h=0.01", _euler(0.01), "h=0.005", _euler(0.005), order=1)
        assert r.probable_cause == DiscrepancyCause.NUMERICAL_DISCRETIZATION
        assert abs(r.reconciled_value - math.e) < 1e-3 and "Richardson" in r.recommended_action

    def test_default_behaviour_is_unchanged(self):
        assert die.analyze("a", 100.0, "b", 100.5).probable_cause == DiscrepancyCause.NUMERICAL_TOLERANCE
        assert die.analyze("a", 100.0, "b", 110.0).probable_cause == DiscrepancyCause.MODELING_ASSUMPTION
        sev = die.analyze("a", 100.0, "b", 250.0, reference_solver=lambda: 245.0)
        assert sev.probable_cause == DiscrepancyCause.REGIME_BREAKDOWN and sev.reconciled_value == 245.0

    def test_same_model_severe_divergence_is_still_escalated(self):
        r = die.analyze("h=1", 1.0, "h=0.5", 100.0, same_model=True)
        assert r.probable_cause == DiscrepancyCause.REGIME_BREAKDOWN

    def test_invalid_arguments(self):
        with pytest.raises(ValueError):
            die.analyze("a", 1.0, "b", 2.0, discretization_error=-1.0)
        with pytest.raises(ValueError):
            DiscrepancyIntelligenceEngine.richardson(1.0, 1.1, order=0)
        with pytest.raises(ValueError):
            DiscrepancyIntelligenceEngine.richardson(1.0, 1.1, order=1, step_ratio=1.0)
