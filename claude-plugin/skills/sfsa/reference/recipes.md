# SFSA recipes (every block below is executed by the test suite; copy, adapt, run with `sfsa-python`)

The model itself (the physics/chemistry/biology) always comes from the user or their code. These recipes show how to put SFSA around it.

## 1. Audit the units of an equation before trusting it
```python
from sfsa.ude import UnitDimensionalEngine

ude = UnitDimensionalEngine()
# E = 1/2 m v^2   ->  kg * (m/s)^2 must be an energy
ok, why = ude.verify_compatibility("kg*(m/s)^2", "J")
assert ok, why
# an additive expression needs one dimension in every term
ok, why = ude.check_sum(["J", "N*m", "kg*m^2/s^2"])
assert ok, why
print(ude.convert(36, "km/h", "m/s"))          # 10.0
print(ude.convert(25, "degC", "K"))            # 298.15
ok, why = ude.verify_compatibility("m/s", "m")  # a mismatch is reported, never silent
assert not ok
```
An unknown unit raises `UnknownUnitError` (or is reported incompatible by `verify_compatibility`); it is never treated as dimensionless.

## 2. Are two forms of an expression the same?
```python
from sfsa.sye import SymbolicEquivalenceEngine

sye = SymbolicEquivalenceEngine()
r = sye.check_equivalence("log(v1/v0) + log(v2/v1)", "log(v2/v0)")
print(r.equivalent, r.method, r.proven, r.note)   # method: syntactic | symbolic | numeric | inconclusive
assert r.equivalent
bad = sye.check_equivalence("log(a*b)", "log(a)*log(b)")
assert not bad.equivalent and bad.counterexample is not None
print(sye.simplify("a / (b - c)").detected_singularities)   # ['Pole at b - c == 0']
```
Report `method`: only `syntactic` and `symbolic` are proofs; `numeric` is strong evidence on positive reals.

## 3. Run an expensive model with caching, bounds and a closed-form shortcut
```python
from sfsa import SFSASession

session = SFSASession(name="kinetics")
calls = []

def solver(inv):
    calls.append(1)
    return 0.5 * inv["m"] * inv["v"] ** 2

first = session.compute(task_id="ke", inventory={"m": 2.0, "v": 3.0}, solver=solver,
                        bounds={"m": (0, 1e3), "v": (0, 1e4)})
again = session.compute(task_id="ke", inventory={"m": 2.0, "v": 3.0}, solver=solver)
assert first.value == again.value == 9.0 and again.cached and len(calls) == 1
print(again.status, again.compute_time_saved_pct)
```
Approximate reuse is opt-in: pass `approximate_reuse_tolerance=0.01`, and say so in the report.

## 4. Cheap model first, expensive model only if needed (multi-fidelity)
```python
from sfsa import SFSASession

session = SFSASession(name="rates")
decision = session.amf.evaluate(
    task_id="rate_constant", inputs={"T": 300.0},
    cheap_solver=lambda i: (i["T"] * 1.8e-3, 0.02),      # (value, relative uncertainty)
    expensive_solver=lambda i: i["T"] * 1.82e-3,
    tolerance=0.05)
print(decision.selected_level, decision.compute_saved_ratio)
```

## 5. Which parameters matter? (sensitivity and dimension reduction)
```python
from sfsa import SFSASession

session = SFSASession(name="sens")
red = session.sra.reduce_parameter_space(
    base_inputs={"T": 300.0, "P": 1.0, "trace": 0.001},
    objective_fn=lambda p: p["T"] * 2.5 + p["P"] * 0.8 + p["trace"] * 1e-4)
print(red.retained_parameters, red.pruned_parameters, red.variance_retained_ratio)
assert "trace" in red.pruned_parameters
```
Say which parameters were pruned and how much variance was retained; do not drop parameters silently.

## 6. Where to run the next experiment (adaptive sampling)
```python
from sfsa import SFSASession

session = SFSASession(name="design")
session.asg.min_euclidean_distance = 0.1
grid = [{"x": i / 20, "y": j / 20} for i in range(21) for j in range(21)]
chosen = session.asg.filter_grid(grid, max_budget=25,
                                 uncertainty_estimator=lambda p: abs(p["x"] - 0.5))   # your own epistemic estimate
assert 0 < len(chosen) <= 25
print(f"{len(chosen)} of {len(grid)} points selected")
```
Pass the uncertainty estimator you actually believe; the default one is only distance-based.

## 7. Two methods disagree: why?
```python
import math
from sfsa.die import DiscrepancyCause, DiscrepancyIntelligenceEngine

def euler(h):                       # y' = y, y(0)=1, value at t=1 (exact: e)
    y = 1.0
    for _ in range(round(1 / h)):
        y += h * y
    return y

die = DiscrepancyIntelligenceEngine()
r = die.analyze_refinement("h=0.01", euler(0.01), "h=0.005", euler(0.005), order=1)
assert r.probable_cause == DiscrepancyCause.NUMERICAL_DISCRETIZATION and abs(r.reconciled_value - math.e) < 1e-3
# different physics, not different step sizes:
other = die.analyze("model_A", 100.0, "model_B", 110.0)
print(other.probable_cause)
```
Tell DIE when both values come from the same equations (`same_model=True`) or give a `discretization_error`; otherwise it cannot know.

## 8. Reproducible record of the session
```python
from sfsa import SFSASession

session = SFSASession(name="record")
session.compute(task_id="t", inventory={"a": 2.0}, solver=lambda i: i["a"] ** 3)
report = session.execute_skill("generate_report")
print(report.session_name, report.total_queries, report.cache_hits, report.active_engines_count)
```
Save the script you ran next to its output when the user wants a record; SFSA has no hidden state.
