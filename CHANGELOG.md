# Changelog

## Unreleased

### Fixed (external audit; Python and JavaScript)
- **UDE** returned any unknown or compound unit (`1/year`, `m/s`, `month`) as dimensionless without warning, so a mismatch could pass an audit. It now parses unit expressions (`*`, `/`, `^`, parentheses, SI prefixes, rational exponents), raises `UnknownUnitError` / `UnitSyntaxError` for anything it cannot resolve (`m2` is an error, not 2 m), reports unknown units as incompatible in `verify_compatibility`, and converts absolute temperatures (degC, degF). Legacy lowercase aliases (`kpa`, `mw`) still resolve.
- **SYE** rewrote text with regular expressions: `x * 0.5` became `0.5`, and identities such as `log(v1/v0) + log(v2/v1) = log(v2/v0)` were not recognised. It now works on a restricted syntax tree (no evaluation of arbitrary code), reports poles using the whole denominator and the domain condition of each rewrite, and decides equivalence with `check_equivalence()`: a sympy proof when sympy is installed (Python, optional) and a seeded numerical check otherwise, stating the method and that a numerical agreement is evidence, not proof.
- **ASG** `filter_grid` ignored the uncertainty estimator. Estimators (per call or at construction) now drive the skip decision; under a budget the points are chosen greedily by utility instead of first-come; a budget of 0 selects nothing; pending responses are NaN, not a fake 0.
- **DIE** classified a numerical discrepancy (Euler vs a finer solution) as a modeling assumption. New cause `NUMERICAL_DISCRETIZATION`, `same_model` / `discretization_error` hints, `richardson()` and `analyze_refinement()`. Default behavior without hints is unchanged.

### Tests
- `python/tests/test_audit_fixes.py` and `javascript/test/test_audit_fixes.js`.

## 0.2.0

### Fixed
- All 85 catalog skills are implemented (44 were no-op stubs reporting `SUCCESS`); missing arguments raise a clear error and failures are logged as `ERROR`.
- `compute(..., analytical_shortcut=...)` crashed with `AttributeError` (ICR counter had no setter).
- ICR returned `0.0` for all-zero inputs without calling the solver; pruning now requires a declared `zero_input_result`, and failing or non-finite shortcuts fall back to the exact solver.
- CAE inferred one-sided cuts from failures alone; cuts now require every known feasible point to lie on the safe side and are revoked when a feasible point appears in the blocked region (`record_feasibility`).
- `compute` silently reused nearby results; approximate reuse is now opt-in (`approximate_reuse_tolerance`) and bound to the current model version. MATE L1 reuse inside `compute` is disabled unless opted in.
- `compute` ignored `bounds` and `invariants`; results violating invariants are no longer cached.
- `session.project_layers`, `session.find_pareto_pathways` and `mate.project_trajectory` were broken or stubs.
- FLN rejects cycles at connect time and applies updates atomically.
- CAE and AIE fail closed on rules that raise; RTE reports singularities as fragility; TBE validates requests.
- Pareto search can repeat steps (dominance pruning + expansion cap).
- RME seal covered only top-level fields in JavaScript; manifests can now be verified (`verify_manifest` / `verifyManifest`).
- TXE transferred constraints use the new cut semantics and ignore absent parameters.
- Skills catalog is bundled with both packages; a missing catalog is an error instead of an empty registry.

### Added
- `test_skills_catalog` and `test_robustness` suites in Python and JavaScript.
- LKE `source_types` filter, FLN `disconnect_layers` / `get_downstream` / `export_graph`, MATE `store` / `export_manifest`, RFE eviction candidates in JavaScript, STE suggestions and bias warnings in JavaScript.
