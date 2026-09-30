# Changelog

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
