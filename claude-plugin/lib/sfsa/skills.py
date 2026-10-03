"""
sfsa.skills — The 85-Skills Execution Registry (Python)
=======================================================
Reads and executes the centralized 85-Skills Catalog from `/skills/catalog.json`.
Acts as the single source of truth dispatcher for researchers and AI coding agents.

Part of SFSA (Standard Framework for Scientific Advancement)
Author & Protocol Creator: Alejo Malia
License: CC BY 4.0
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, is_dataclass
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional
import copy
import json
import math


@dataclass
class SkillMetadata:
    """Descriptor of an executable scientific skill."""
    skill_number: int
    name: str
    category: str
    description: str
    target_engine: str = "session"
    target_method: str = "execute"


def _load_catalog() -> List[SkillMetadata]:
    """Loads the skills catalog: the copy bundled in the package first, then the repo-level source of truth."""
    possible_paths = [
        Path(__file__).resolve().parent / "catalog.json",
        Path(__file__).resolve().parent.parent.parent / "skills" / "catalog.json",
        Path.cwd() / "skills" / "catalog.json",
    ]
    errors: List[str] = []
    for p in possible_paths:
        if not p.is_file():
            continue
        try:
            with open(p, "r", encoding="utf-8") as f:
                raw = json.load(f)
            return [
                SkillMetadata(
                    skill_number=item["skill_number"],
                    name=item["name"],
                    category=item["category"],
                    description=item["description"],
                    target_engine=item.get("target_engine", "session"),
                    target_method=item.get("target_method", "execute"),
                )
                for item in raw
            ]
        except (OSError, ValueError, KeyError) as exc:
            errors.append(f"{p}: {exc}")
    raise RuntimeError(
        "SFSA skills catalog not found or invalid. Searched: "
        + ", ".join(str(p) for p in possible_paths)
        + ("; errors: " + "; ".join(errors) if errors else "")
    )


# Loaded dynamically from /skills/catalog.json
SKILL_DEFINITIONS: List[SkillMetadata] = _load_catalog()


# Required keyword arguments per skill. Drives both validate_skill_call and the pre-dispatch check,
# so a missing argument raises one clear ValueError instead of a KeyError/TypeError from deep inside an engine.
REQUIRED_ARGS: Dict[str, List[str]] = {
    "load_session": ["path"], "save_session": ["path"],
    "register_layer": ["layer_id"], "update_layer": ["layer_id", "new_state"],
    "connect_layers": ["source_id", "target_id", "transformer"],
    "disconnect_layers": ["source_id", "target_id"],
    "get_layer_state": ["layer_id"], "propagate_delta": ["layer_id"], "find_affected_layers": ["layer_id"],
    "inventory_check": ["inventory"], "try_closed_form": ["inputs", "analytical"],
    "bounded_verify": ["result"], "run_triada": ["inventory", "solver"],
    "declare_invariants": ["invariants"], "check_invariants": ["result"],
    "compute": ["task_id", "inventory", "solver"],
    "query_cache": ["task_id", "inputs"], "store_result": ["task_id", "inputs", "output"],
    "project_trajectory": ["task_id", "inputs"], "early_abort_check": ["task_id", "inputs"],
    "reduce_expression": ["expression"], "estimate_compute_cost": [],
    "check_consistency": ["layer_a", "layer_b"], "project_layers": ["layer_a", "layer_b"],
    "register_transition_step": ["step_id", "cost", "duration", "feasibility", "delta_state"],
    "find_pareto_paths": ["initial_state", "target_state"], "rank_pathways": ["pathways"],
    "compare_states": ["state_a", "state_b"],
    "choose_fidelity": ["inputs", "cheap_solver", "expensive_solver"],
    "compute_multi_fidelity": ["task_id", "inputs", "cheap_solver", "expensive_solver"],
    "suggest_samples": ["candidates"], "run_adaptive_sampling": ["candidates", "objective_fn"],
    "should_stop": ["iteration", "current_value", "previous_value", "max_planned_iterations"],
    "value_of_information": ["candidate_id", "predicted_value", "epistemic_uncertainty", "decision_threshold"],
    "warm_start": ["task_id", "inputs"], "build_surrogate": ["model_id", "points", "values"],
    "analyze_sensitivity": ["base_inputs", "objective_fn"], "reduce_dimensions": ["base_inputs", "objective_fn"],
    "infer_constraints": ["failures"], "apply_constraints": ["inputs"],
    "extract_partial_knowledge": ["task_id"], "reuse_approximate": ["task_id", "inputs"],
    "map_landscape": ["bounds", "surrogate"],
    "assess_reuse": ["task_id", "inputs"],
    "diff_model_versions": ["version_a", "version_b"],
    "link_evidence_to_gap": ["gap", "evidence"],
    "check_assumption_integrity": ["state"],
    "validate_skill_call": ["skill"], "batch_queries": ["queries", "heavy_solver"],
    "prioritize_queries": ["queries"],
}


def _plain(obj: Any) -> Any:
    """Converts dataclasses / enums to plain JSON-friendly data (callables become their name)."""
    if is_dataclass(obj) and not isinstance(obj, type):
        return {k: _plain(v) for k, v in asdict(obj).items()}
    if isinstance(obj, dict):
        return {str(k): _plain(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple, set)):
        return [_plain(v) for v in obj]
    if hasattr(obj, "value") and obj.__class__.__module__ != "builtins" and hasattr(obj.__class__, "__members__"):
        return obj.value
    if callable(obj):
        return getattr(obj, "__name__", "callable")
    return obj


class SkillRegistry:
    """
    Unified execution engine for all 85 SFSA skills, driven by /skills/catalog.json.
    Every catalog entry is dispatched to a `_skill_<name>` method; there are no silent fallbacks.
    """

    def __init__(self, session: Any) -> None:
        self.session = session
        self.skills_by_name: Dict[str, SkillMetadata] = {s.name: s for s in SKILL_DEFINITIONS}
        self.skills_by_num: Dict[int, SkillMetadata] = {s.skill_number: s for s in SKILL_DEFINITIONS}
        self.execution_log: List[Dict[str, Any]] = []
        # Session-scoped state owned by skills
        self.invariants: Dict[str, Callable[[Any], Any]] = {}
        self.versions: Dict[str, Dict[str, Any]] = {}
        self.policy: Dict[str, Any] = {}
        self.evidence_links: List[Dict[str, Any]] = []
        self.run_snapshots: List[Dict[str, Any]] = []

    def list_skills(self, category: Optional[str] = None) -> List[SkillMetadata]:
        """Lists registered skills, optionally filtered by functional category."""
        if category:
            return [s for s in SKILL_DEFINITIONS if s.category.lower() == category.lower()]
        return list(SKILL_DEFINITIONS)

    def missing_implementations(self) -> List[str]:
        """Catalog skills that have no `_skill_<name>` handler (must always be empty)."""
        return [s.name for s in SKILL_DEFINITIONS if not hasattr(self, f"_skill_{s.name}")]

    def validate(self, skill: Any, args: Optional[Dict[str, Any]] = None, **extra: Any) -> Dict[str, Any]:
        """Validates a skill call (existence and required arguments) without executing it."""
        args = dict(args or {}, **extra)
        meta = self.skills_by_num.get(skill) if isinstance(skill, int) else self.skills_by_name.get(str(skill))
        if meta is None:
            return {"valid": False, "skill": skill, "missing": [], "errors": [f"Unknown SFSA skill: {skill}"]}
        missing = [a for a in REQUIRED_ARGS.get(meta.name, []) if a not in args]
        errors = [f"Missing required argument '{m}'" for m in missing]
        return {"valid": not errors, "skill": meta.name, "missing": missing, "errors": errors}

    def execute(self, skill_name_or_number: Any, **kwargs: Any) -> Any:
        """Executes an SFSA skill by name or number."""
        if isinstance(skill_name_or_number, int) and not isinstance(skill_name_or_number, bool):
            meta = self.skills_by_num.get(skill_name_or_number)
        else:
            meta = self.skills_by_name.get(str(skill_name_or_number))
        if not meta:
            raise ValueError(f"Unknown SFSA skill: {skill_name_or_number}")

        entry = {"skill": meta.name, "skill_number": meta.skill_number, "args": list(kwargs.keys())}
        check = self.validate(meta.name, kwargs)
        if not check["valid"]:
            entry["status"] = "INVALID_ARGS"
            self.execution_log.append(entry)
            raise ValueError(f"Skill '{meta.name}': " + "; ".join(check["errors"]))

        handler = getattr(self, f"_skill_{meta.name}", None)
        if handler is None:
            entry["status"] = "NOT_IMPLEMENTED"
            self.execution_log.append(entry)
            raise NotImplementedError(f"Skill '{meta.name}' has no implementation")

        try:
            result = handler(**kwargs)
        except Exception as exc:
            entry["status"] = "ERROR"
            entry["error"] = f"{type(exc).__name__}: {exc}"
            self.execution_log.append(entry)
            raise
        entry["status"] = "SUCCESS"
        self.execution_log.append(entry)
        return result

    # ------------------------------------------------------------------ helpers
    def _layer(self, layer_id: str) -> Any:
        layer = self.session.fln.get_layer(layer_id)
        if layer is None:
            raise KeyError(f"Layer '{layer_id}' not found")
        return layer

    def _layer_state(self, ref: Any) -> Dict[str, Any]:
        """Accepts a layer id or a raw state dict."""
        return dict(ref) if isinstance(ref, dict) else dict(self._layer(ref).state)

    def _check_invariants(self, value: Any, names: Optional[List[str]] = None,
                          extra: Optional[Any] = None) -> Dict[str, Any]:
        checks: Dict[str, Callable[[Any], Any]] = {}
        if names is None:
            checks.update(self.invariants)
        else:
            for n in names:
                if n not in self.invariants:
                    raise KeyError(f"Invariant '{n}' is not declared")
                checks[n] = self.invariants[n]
        if isinstance(extra, dict):
            checks.update(extra)
        elif extra:
            checks.update({getattr(f, "__name__", f"inv_{i}"): f for i, f in enumerate(extra)})
        failures = []
        for name, fn in checks.items():
            try:
                res = fn(value)
                ok, why = (res[0], res[1] if len(res) > 1 else "") if isinstance(res, tuple) else (bool(res), "")
            except Exception as exc:
                ok, why = False, f"raised {type(exc).__name__}: {exc}"
            if not ok:
                failures.append({"invariant": name, "reason": why})
        return {"passed": not failures, "checked": len(checks), "failures": failures}

    def _inventory_report(self, inventory: Dict[str, Any], bounds: Optional[Dict[str, Any]] = None,
                          required: Optional[List[str]] = None,
                          conservation: Optional[Dict[str, Callable[[Dict[str, Any]], Any]]] = None) -> Dict[str, Any]:
        reasons: List[str] = []
        for key in required or []:
            if key not in inventory or inventory[key] is None:
                reasons.append(f"missing variable '{key}'")
        for key, val in inventory.items():
            if isinstance(val, float) and not math.isfinite(val):
                reasons.append(f"non-finite value for '{key}'")
        for key, (lo, hi) in (bounds or {}).items():
            if key not in inventory:
                reasons.append(f"bounded variable '{key}' missing")
            elif isinstance(inventory[key], (int, float)) and not (lo <= inventory[key] <= hi):
                reasons.append(f"'{key}'={inventory[key]} outside [{lo}, {hi}]")
        for name, fn in (conservation or {}).items():
            try:
                if not fn(inventory):
                    reasons.append(f"conservation law '{name}' violated")
            except Exception as exc:
                reasons.append(f"conservation law '{name}' raised {type(exc).__name__}: {exc}")
        return {"passed": not reasons, "reasons": reasons}

    # ============================================================ 1. Orchestration
    def _skill_create_session(self) -> Any:
        return self.session

    def _skill_load_session(self, path: str) -> Dict[str, Any]:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        s = self.session
        for lid, info in data.get("layers", {}).items():
            layer = s.fln.get_layer(lid) or s.register_layer(lid, {}, info.get("name"))
            layer.state.clear()
            layer.state.update(info.get("state", {}))
            layer.version = info.get("version", layer.version)
        self.policy.update(data.get("policy", {}))
        self._apply_policy(self.policy)
        if "budget_seconds" in data:
            self._skill_set_budget(data["budget_seconds"])
        self.versions.update(data.get("versions", {}))
        return {"loaded_layers": len(data.get("layers", {})), "name": data.get("name")}

    def _skill_save_session(self, path: str) -> Dict[str, Any]:
        s = self.session
        data = {
            "format": "sfsa-session/1",
            "name": s.name,
            "layers": {l.layer_id: {"name": l.name, "state": l.state, "version": l.version}
                       for l in s.fln.layers.values()},
            "policy": self.policy,
            "budget_seconds": s.tbe.total_budget,
            "versions": self.versions,
        }
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, default=str)
        return {"saved": path, "layers": len(data["layers"])}

    def _skill_reset_session(self, scope: str = "all") -> Dict[str, Any]:
        if scope not in ("all", "cache", "history", "layers"):
            raise ValueError("scope must be one of: all, cache, history, layers")
        s = self.session
        cleared: List[str] = []
        if scope in ("all", "cache"):
            s.mate.clear_cache()
            s.cpe.records.clear()
            s.rfe.entry_metadata.clear()
            cleared.append("cache")
        if scope in ("all", "history"):
            s.xxe.decision_log.clear()
            self.run_snapshots.clear()
            self.evidence_links.clear()
            cleared.append("history")
        if scope in ("all", "layers"):
            s.fln._layers.clear()
            s.fln._dependencies.clear()
            cleared.append("layers")
        return {"cleared": cleared}

    def _skill_get_session_status(self) -> Any:
        return self.session.generate_report()

    def _skill_set_budget(self, seconds: float = 60.0) -> Dict[str, Any]:
        if not isinstance(seconds, (int, float)) or isinstance(seconds, bool) or not seconds > 0:
            raise ValueError("budget seconds must be a positive number")
        tbe = self.session.tbe
        tbe.total_budget = float(seconds)
        tbe.spent_seconds = 0.0
        tbe.start_timestamp = __import__("time").time()
        return {"budget_seconds": tbe.total_budget}

    def _apply_policy(self, policy: Dict[str, Any]) -> None:
        s = self.session
        if "mate_spec_mode" in policy:
            if policy["mate_spec_mode"] not in ("off", "idle_only", "bounded", "aggressive"):
                raise ValueError("mate_spec_mode must be off|idle_only|bounded|aggressive")
            s.mate.spec_mode = policy["mate_spec_mode"]
        if "reuse_tolerance" in policy:
            s.cpe.approximate_tolerance = float(policy["reuse_tolerance"])
        if "stopping_tolerance" in policy:
            s.uas.target_tolerance = float(policy["stopping_tolerance"])
        if "min_sample_distance" in policy:
            s.asg.min_euclidean_distance = float(policy["min_sample_distance"])

    def _skill_set_policy(self, policy: Optional[Dict[str, Any]] = None, **kw: Any) -> Dict[str, Any]:
        new = dict(policy or {}, **kw)
        self._apply_policy(new)
        self.policy.update(new)
        return dict(self.policy)

    # ============================================================ 2. FLN
    def _skill_register_layer(self, layer_id: str, initial_state: Optional[Dict[str, Any]] = None,
                              name: Optional[str] = None) -> Any:
        return self.session.register_layer(layer_id, initial_state, name)

    def _skill_update_layer(self, layer_id: str, new_state: Dict[str, Any]) -> Any:
        return self.session.update_layer(layer_id, new_state)

    def _skill_connect_layers(self, source_id: str, target_id: str, transformer: Callable[..., Any],
                              desc: str = "") -> Dict[str, Any]:
        self.session.connect_layers(source_id, target_id, transformer, desc)
        return {"connected": True}

    def _skill_disconnect_layers(self, source_id: str, target_id: str) -> Dict[str, Any]:
        removed = self.session.fln.disconnect_layers(source_id, target_id)
        return {"disconnected": removed > 0, "edges_removed": removed}

    def _skill_inspect_graph(self) -> Dict[str, Any]:
        g = self.session.fln.export_graph()
        n = len(g["nodes"])
        degree = {node["id"]: 0 for node in g["nodes"]}
        for e in g["edges"]:
            degree[e["source"]] += 1
            degree[e["target"]] += 1
        centrality = {k: (v / (n - 1) if n > 1 else 0.0) for k, v in degree.items()}
        return {"layers": [x["id"] for x in g["nodes"]], "dependencies": len(g["edges"]),
                "edges": g["edges"], "centrality": centrality}

    def _skill_get_layer_state(self, layer_id: str) -> Dict[str, Any]:
        return copy.deepcopy(self._layer(layer_id).state)

    def _skill_propagate_delta(self, layer_id: str, delta: Optional[Dict[str, Any]] = None) -> Dict[str, int]:
        self._layer(layer_id)
        return self.session.fln.update_layer(layer_id, delta or {}, propagate=True)

    def _skill_find_affected_layers(self, layer_id: str) -> List[str]:
        return self.session.fln.get_downstream(layer_id)

    # ============================================================ 3. TRIADA
    def _skill_inventory_check(self, inventory: Dict[str, Any], bounds: Optional[Dict[str, Any]] = None,
                               required: Optional[List[str]] = None, conservation: Optional[Dict[str, Any]] = None,
                               task_id: str = "inv_check") -> Dict[str, Any]:
        rep = self._inventory_report(inventory, bounds, required, conservation)
        rep["task_id"] = task_id
        rep["stage"] = "T1_INVENTORY"
        return rep

    def _skill_try_closed_form(self, inputs: Dict[str, Any], analytical: Callable[..., Any]) -> Dict[str, Any]:
        try:
            value = analytical(inputs)
        except Exception as exc:
            return {"solved": False, "value": None, "error": f"{type(exc).__name__}: {exc}", "stage": "T2"}
        ok = not (isinstance(value, float) and not math.isfinite(value)) and value is not None
        return {"solved": ok, "value": value if ok else None,
                "error": None if ok else "closed form returned no finite value", "stage": "T2"}

    def _skill_bounded_verify(self, result: Any, invariants: Optional[Any] = None,
                              names: Optional[List[str]] = None) -> Dict[str, Any]:
        rep = self._check_invariants(result, (names or []) if invariants is not None else names, invariants)
        rep["stage"] = "T3"
        return rep

    def _skill_run_triada(self, inventory: Dict[str, Any], solver: Callable[..., Any],
                          task_id: Optional[str] = None, task_name: Optional[str] = None,
                          bounds: Optional[Dict[str, Any]] = None, required: Optional[List[str]] = None,
                          invariants: Optional[Any] = None) -> Any:
        name = task_name or task_id or "triada_task"

        def t1(inv: Dict[str, Any]) -> Any:
            rep = self._inventory_report(inv, bounds, required)
            return rep["passed"], rep["reasons"]

        def t3(out: Any, inv: Dict[str, Any]) -> Any:
            rep = self._check_invariants(out, [] if invariants else None, invariants)
            return rep["passed"], [f"{f['invariant']}: {f['reason']}" for f in rep["failures"]]

        report = self.session.triada.run_pipeline(name, inventory, t1, solver, t3)
        self.session.xxe.record_decision("TRIADA", "RUN_PIPELINE" if report.success else "PIPELINE_FAILED",
                                         f"Task '{name}' success={report.success}", metadata={"task_id": name})
        return report

    def _skill_declare_invariants(self, invariants: Any) -> Dict[str, Any]:
        if isinstance(invariants, dict):
            items = invariants.items()
        else:
            items = [(getattr(f, "__name__", f"invariant_{len(self.invariants) + i}"), f)
                     for i, f in enumerate(invariants)]
        for name, fn in items:
            if not callable(fn):
                raise TypeError(f"Invariant '{name}' must be callable")
            self.invariants[name] = fn
        return {"declared": sorted(self.invariants.keys())}

    def _skill_check_invariants(self, result: Any, names: Optional[List[str]] = None) -> Dict[str, Any]:
        return self._check_invariants(result, names)

    # ============================================================ 4. MATE / ICR
    def _skill_compute(self, **kw: Any) -> Any:
        res = self.session.compute(**kw)
        self.session.xxe.record_decision(
            "MATE", "CACHE_HIT" if res.cached else "COMPUTE",
            res.diagnostic_message or "computed", metadata={"task_id": kw.get("task_id")})
        return res

    def _skill_query_cache(self, task_id: str, inputs: Dict[str, Any]) -> Any:
        return self.session.mate.lookup(task_id, inputs)

    def _skill_store_result(self, task_id: str, inputs: Dict[str, Any], output: Any,
                            model_version: Optional[str] = None, recompute_cost_ms: float = 1.0) -> Any:
        s = self.session
        key = s.mate.store(task_id, inputs, output)
        s.rfe.track_entry(key, recompute_cost_ms)
        return s.cpe.register_result(task_id, inputs, output, model_version=model_version or s.cpe_model_version())

    def _skill_invalidate_cache(self, new_model_version: Optional[str] = None) -> Dict[str, Any]:
        mate = self.session.mate
        version = new_model_version or f"{mate.model_version}+"
        count = mate.invalidate(version)
        self.session.cpe.records.clear()
        return {"model_version": version, "mechanisms_invalidated": count}

    def _skill_project_trajectory(self, task_id: str, inputs: Dict[str, Any],
                                  invariants: Optional[List[Any]] = None) -> bool:
        return self.session.mate.project_trajectory(task_id, inputs, invariants or [])

    def _skill_early_abort_check(self, task_id: str, inputs: Dict[str, Any], invariants: Optional[List[Any]] = None,
                                 bounds: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        ok_cae, reason = self.session.cae.validate_inputs(inputs)
        inv = self._inventory_report(inputs, bounds)
        feasible = self.session.mate.project_trajectory(task_id, inputs, invariants or [])
        reasons = ([reason] if not ok_cae else []) + inv["reasons"] + ([] if feasible else ["trajectory invariant violated"])
        if reasons:
            self.session.mate.record_early_abort()
        return {"should_abort": bool(reasons), "reasons": reasons}

    def _skill_reduce_expression(self, expression: str) -> Any:
        return self.session.sye.simplify(expression)

    def _skill_estimate_compute_cost(self, operations: Optional[int] = None, grid_points: Optional[int] = None,
                                     cost_per_op_ms: float = 0.001, cache_hit_rate: Optional[float] = None) -> Dict[str, Any]:
        if operations is None:
            operations = grid_points if grid_points is not None else 1000
        if operations < 0 or cost_per_op_ms < 0:
            raise ValueError("operations and cost_per_op_ms must be non-negative")
        if cache_hit_rate is None:
            st = self.session.mate.stats()
            cache_hit_rate = st.cache_hits / st.total_lookups if st.total_lookups else 0.0
        cache_hit_rate = min(max(cache_hit_rate, 0.0), 1.0)
        effective = operations * (1.0 - cache_hit_rate)
        return {"operations": operations, "estimated_ms_no_reuse": operations * cost_per_op_ms,
                "cache_hit_rate": cache_hit_rate, "effective_operations": effective,
                "estimated_ms": effective * cost_per_op_ms}

    # ============================================================ 5. Consistency & Pareto
    def _skill_check_consistency(self, layer_a: Any, layer_b: Any,
                                 known_bounds: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        a_id = layer_a if isinstance(layer_a, str) else "layer_a"
        b_id = layer_b if isinstance(layer_b, str) else "layer_b"
        rep = self.session.projector.project_and_intersect(
            a_id, self._layer_state(layer_a), b_id, self._layer_state(layer_b), known_bounds)
        return {"consistent": not rep.inconsistencies, "inconsistencies": rep.inconsistencies,
                "distance": rep.normalized_vector_distance, "report": rep}

    def _skill_project_layers(self, layer_a: str, layer_b: str) -> Any:
        return self.session.project_layers(layer_a, layer_b)

    def _skill_register_transition_step(self, step: Any = None, step_id: Optional[str] = None, name: Optional[str] = None,
                                        cost: float = 0.0, duration: float = 0.0, feasibility: float = 1.0,
                                        delta_state: Optional[Dict[str, float]] = None) -> Any:
        from sfsa.path import TransitionStep
        if step is None:
            if not 0.0 <= feasibility <= 1.0:
                raise ValueError("feasibility must be in [0, 1]")
            step = TransitionStep(step_id=step_id, name=name or step_id, cost=cost, duration=duration,
                                  feasibility=feasibility, delta_state=dict(delta_state or {}))
        self.session.path.register_step(step)
        return step

    def _skill_find_pareto_paths(self, initial_state: Dict[str, float], target_state: Dict[str, float],
                                 max_depth: int = 5) -> Any:
        return self.session.find_pareto_pathways(initial_state, target_state, max_depth)

    def _skill_rank_pathways(self, pathways: List[Any], by: str = "balanced") -> List[Any]:
        keys = {
            "cost": lambda p: p.accumulated_cost,
            "duration": lambda p: p.accumulated_duration,
            "feasibility": lambda p: -p.joint_feasibility,
        }
        if by == "balanced":
            def norm(vals: List[float]) -> List[float]:
                lo, hi = min(vals), max(vals)
                return [0.0 if hi == lo else (v - lo) / (hi - lo) for v in vals]
            if not pathways:
                return []
            c = norm([p.accumulated_cost for p in pathways])
            d = norm([p.accumulated_duration for p in pathways])
            f = norm([-p.joint_feasibility for p in pathways])
            order = sorted(range(len(pathways)), key=lambda i: c[i] + d[i] + f[i])
            return [pathways[i] for i in order]
        if by not in keys:
            raise ValueError("by must be one of: cost, duration, feasibility, balanced")
        return sorted(pathways, key=keys[by])

    def _skill_compare_states(self, state_a: Dict[str, Any], state_b: Dict[str, Any]) -> Dict[str, Any]:
        changed: Dict[str, Any] = {}
        for k in sorted(set(state_a) & set(state_b)):
            a, b = state_a[k], state_b[k]
            if isinstance(a, (int, float)) and isinstance(b, (int, float)) and not isinstance(a, bool):
                if a != b:
                    changed[k] = {"from": a, "to": b, "delta": b - a,
                                  "relative": (b - a) / abs(a) if a else None}
            elif a != b:
                changed[k] = {"from": a, "to": b}
        return {"changed": changed, "added": {k: state_b[k] for k in state_b if k not in state_a},
                "removed": {k: state_a[k] for k in state_a if k not in state_b},
                "identical": not changed and set(state_a) == set(state_b)}

    # ============================================================ 6. Fidelity & Sampling
    def _skill_choose_fidelity(self, inputs: Dict[str, Any], cheap_solver: Callable[..., Any],
                               expensive_solver: Callable[..., Any], task_id: str = "fidelity_eval",
                               intermediate_solver: Optional[Callable[..., Any]] = None,
                               tolerance: Optional[float] = None) -> Any:
        return self.session.amf.evaluate(task_id=task_id, inputs=inputs, cheap_solver=cheap_solver,
                                         expensive_solver=expensive_solver,
                                         intermediate_solver=intermediate_solver, tolerance=tolerance)

    def _skill_compute_multi_fidelity(self, task_id: str, inputs: Dict[str, Any], cheap_solver: Callable[..., Any],
                                      expensive_solver: Callable[..., Any],
                                      intermediate_solver: Optional[Callable[..., Any]] = None,
                                      tolerance: Optional[float] = None) -> Any:
        return self.session.amf.evaluate(task_id=task_id, inputs=inputs, cheap_solver=cheap_solver,
                                         expensive_solver=expensive_solver,
                                         intermediate_solver=intermediate_solver, tolerance=tolerance)

    def _skill_suggest_samples(self, candidates: List[Dict[str, float]], top_k: Optional[int] = None) -> List[Any]:
        ranked = sorted((self.session.asg.evaluate_candidate(pt) for pt in candidates),
                        key=lambda c: c.information_gain, reverse=True)
        return ranked[:top_k] if top_k else ranked

    def _skill_run_adaptive_sampling(self, candidates: List[Dict[str, float]], objective_fn: Callable[..., float],
                                     max_budget: Optional[int] = None) -> Any:
        from sfsa.asg import SamplingCampaign
        asg = self.session.asg
        selected = asg.filter_grid(candidates, max_budget)
        for pt in selected:
            # filter_grid pre-registers a placeholder value; replace it with the real evaluation
            idx = len(asg.evaluated_points) - 1
            for i in range(len(asg.evaluated_points) - 1, -1, -1):
                if asg.evaluated_points[i] == pt:
                    idx = i
                    break
            asg.point_values[idx] = objective_fn(pt)
        total = len(candidates)
        return SamplingCampaign(
            total_grid_points_possible=total, points_evaluated=len(selected),
            points_skipped=total - len(selected),
            points_saved_pct=((total - len(selected)) / total * 100.0) if total else 0.0,
            active_samples=selected)

    def _skill_should_stop(self, **kw: Any) -> Any:
        return self.session.uas.evaluate_step(**kw)

    def _skill_value_of_information(self, candidate_id: str, predicted_value: float, epistemic_uncertainty: float,
                                    decision_threshold: float, estimated_cost: float = 1.0) -> Any:
        return self.session.voi.evaluate_candidate(candidate_id, predicted_value, epistemic_uncertainty,
                                                   decision_threshold, estimated_cost)

    def _skill_warm_start(self, task_id: str, inputs: Dict[str, Any]) -> Dict[str, Any]:
        s = self.session
        exact = s.mate.lookup(task_id, inputs)
        if exact is not None:
            return {"seed": exact, "source": "MATE_EXACT", "confidence": 1.0}
        a = s.cpe.assess_reuse(task_id, inputs)
        if a.value is not None and a.reuse_type.value != "FULL_COMPUTATION":
            return {"seed": a.value, "source": f"CPE_{a.reuse_type.value}", "confidence": a.confidence}
        pk = s.pke.get_latest(task_id)
        if pk is not None:
            return {"seed": pk.latest_estimate, "source": "PKE_PARTIAL", "confidence": 0.5}
        return {"seed": None, "source": "NONE", "confidence": 0.0}

    def _skill_build_surrogate(self, model_id: str, points: List[Dict[str, float]], values: List[float]) -> Any:
        if len(points) != len(values):
            raise ValueError("points and values must have the same length")
        if not points:
            raise ValueError("at least one sample point is required")
        return self.session.sme.fit_from_history(model_id, points, values)

    # ============================================================ 7. Sensitivity & Cuts
    def _skill_analyze_sensitivity(self, base_inputs: Dict[str, float], objective_fn: Callable[..., float],
                                   perturbation_delta: float = 0.01) -> Any:
        return self.session.sra.analyze_one_at_a_time(base_inputs, objective_fn, perturbation_delta)

    def _skill_reduce_dimensions(self, base_inputs: Dict[str, float], objective_fn: Callable[..., float],
                                 target_variance_explained: float = 0.95) -> Any:
        return self.session.sra.reduce_parameter_space(base_inputs, objective_fn, target_variance_explained)

    def _skill_infer_constraints(self, failures: List[Dict[str, Any]], reason: str = "") -> Any:
        for f in failures:
            self.session.cae.record_infeasibility(f, reason)
        return list(self.session.cae.inferred_constraints)

    def _skill_apply_constraints(self, inputs: Dict[str, Any]) -> Any:
        return self.session.cae.validate_inputs(inputs)

    def _skill_extract_partial_knowledge(self, task_id: str) -> Any:
        return self.session.pke.get_latest(task_id)

    def _skill_reuse_approximate(self, task_id: str, inputs: Dict[str, Any], tolerance: Optional[float] = None) -> Any:
        return self.session.cpe.assess_reuse(task_id, inputs, custom_tolerance=tolerance)

    def _skill_map_landscape(self, bounds: Dict[str, Any], surrogate: Callable[..., float]) -> Any:
        return self.session.lse.probe_region(bounds, surrogate)

    # ============================================================ 8. Provenance & Hygiene
    def _skill_get_provenance(self, task_id: Optional[str] = None, record_id: Optional[str] = None) -> List[Any]:
        recs = list(self.session.cpe.records.values())
        if record_id:
            recs = [r for r in recs if r.record_id == record_id]
        if task_id:
            recs = [r for r in recs if r.task_id == task_id]
        return recs

    def _skill_assess_reuse(self, task_id: str, inputs: Dict[str, Any], required_model_version: Optional[str] = None,
                            custom_tolerance: Optional[float] = None) -> Any:
        return self.session.cpe.assess_reuse(task_id, inputs, required_model_version, custom_tolerance)

    def _skill_forget_results(self, count: int = 10) -> Dict[str, Any]:
        s = self.session
        if count < 0:
            raise ValueError("count must be non-negative")
        victims = s.rfe.identify_eviction_candidates(count)
        for key in victims:
            s.rfe.entry_metadata.pop(key, None)
            s.mate._cache.pop(key, None)
        return {"evicted": victims, "count": len(victims)}

    def _skill_version_model(self, label: Optional[str] = None) -> Dict[str, Any]:
        label = label or f"v{len(self.versions) + 1}"
        if label in self.versions:
            raise ValueError(f"Version '{label}' already exists")
        self.versions[label] = {l.layer_id: {"version": l.version, "state": copy.deepcopy(l.state)}
                                for l in self.session.fln.layers.values()}
        return {"version": label, "layers": len(self.versions[label])}

    def _skill_diff_model_versions(self, version_a: str, version_b: str) -> Dict[str, Any]:
        for v in (version_a, version_b):
            if v not in self.versions:
                raise KeyError(f"Unknown model version '{v}'")
        a, b = self.versions[version_a], self.versions[version_b]
        out: Dict[str, Any] = {"layers_added": sorted(set(b) - set(a)),
                               "layers_removed": sorted(set(a) - set(b)), "changed": {}}
        for lid in sorted(set(a) & set(b)):
            d = self._skill_compare_states(a[lid]["state"], b[lid]["state"])
            if not d["identical"]:
                out["changed"][lid] = d
        return out

    # ============================================================ 9. Thematic (STE)
    def _skill_analyze_themes(self) -> Any:
        return self.session.analyze_themes()

    def _skill_get_theme_coverage(self) -> Dict[str, float]:
        return self.session.analyze_themes().coverage_pct

    def _skill_detect_theme_gaps(self) -> List[str]:
        return self.session.analyze_themes().thematic_gaps

    def _skill_suggest_related_themes(self) -> List[str]:
        return self.session.analyze_themes().related_suggestions

    def _skill_explain_model_focus(self) -> str:
        rep = self.session.analyze_themes()
        if not rep.primary_themes and not rep.secondary_themes:
            return "No thematic signal detected yet: register layers with descriptive names and variables."
        lead = ", ".join(f"{k} ({v:.0f}%)" for k, v in (rep.primary_themes or rep.secondary_themes)[:3])
        text = f"The model is mainly about {lead}."
        if rep.thematic_gaps:
            text += " Gaps: " + "; ".join(rep.thematic_gaps) + "."
        if rep.bias_warnings:
            text += " Warnings: " + "; ".join(rep.bias_warnings) + "."
        return text

    # ============================================================ 10. Literature (LKE)
    def _domains(self, domains: Optional[List[str]]) -> List[str]:
        if domains:
            return domains
        return [t[0] for t in self.session.analyze_themes().primary_themes] or ["multidisciplinary"]

    def _skill_search_literature(self, domains: Optional[List[str]] = None, limit: int = 5) -> Any:
        return self.session.search_literature(domains, limit)

    def _by_type(self, type_name: str, domains: Optional[List[str]], limit: int) -> List[Any]:
        from sfsa.lke import SourceType
        return self.session.lke.propose_resources(
            self._domains(domains), limit=limit, source_types=[SourceType[type_name]])

    def _skill_search_datasets(self, domains: Optional[List[str]] = None, limit: int = 5) -> List[Any]:
        return self._by_type("DATASET_PROPERTIES", domains, limit)

    def _skill_search_reference_code(self, domains: Optional[List[str]] = None, limit: int = 5) -> List[Any]:
        return self._by_type("CODE_METHODS", domains, limit)

    def _skill_rank_external_sources(self, domains: Optional[List[str]] = None, limit: int = 10) -> List[Any]:
        found = self.session.lke.propose_resources(self._domains(domains), limit=max(limit, 50))
        return sorted(found, key=lambda p: p.confidence, reverse=True)[:limit]

    def _skill_propose_external_evidence(self, domains: Optional[List[str]] = None, limit: int = 5,
                                         prefer_open_access: bool = True) -> Any:
        return self.session.lke.propose_resources(self._domains(domains), limit=limit,
                                                  prefer_open_access=prefer_open_access)

    def _skill_link_evidence_to_gap(self, gap: Any, evidence: Any) -> Dict[str, Any]:
        link = {
            "gap": getattr(gap, "description", None) or getattr(gap, "parameter_name", None) or str(gap),
            "evidence": getattr(evidence, "title", None) or str(evidence),
            "url": getattr(evidence, "url", None),
        }
        self.evidence_links.append(link)
        return link

    # ============================================================ 11. Gaps & Assumptions
    def _skill_detect_gaps(self, required_schema: Optional[Dict[str, Any]] = None) -> List[Any]:
        merged: Dict[str, Any] = {}
        for layer in self.session.fln.layers.values():
            merged.update(layer.state)
        return self.session.autocomplete.detect_gaps(merged, required_schema)

    def _skill_suggest_gap_closure(self, required_schema: Optional[Dict[str, Any]] = None,
                                   gaps: Optional[List[Any]] = None) -> List[Any]:
        merged: Dict[str, Any] = {}
        for layer in self.session.fln.layers.values():
            merged.update(layer.state)
        gaps = gaps if gaps is not None else self.session.autocomplete.detect_gaps(merged, required_schema)
        return self.session.autocomplete.suggest_connections(gaps, merged)

    def _skill_list_assumptions(self) -> List[Dict[str, Any]]:
        return [{"id": a.assumption_id, "name": a.name, "criticality": a.criticality,
                 "description": a.description} for a in self.session.aie.assumptions.values()]

    def _skill_check_assumption_integrity(self, state: Dict[str, Any]) -> Any:
        return self.session.aie.audit_state(state)

    # ============================================================ 12. Explanation & Audit
    def _skill_explain_decision(self, task_id: Optional[str] = None, engine_name: Optional[str] = None,
                                action: Optional[str] = None, rationale: Optional[str] = None) -> Any:
        xxe = self.session.xxe
        if action and rationale:
            xxe.record_decision(engine_name or "USER", action, rationale,
                                metadata={"task_id": task_id} if task_id else None)
        return xxe.explain_task(task_id or "latest")

    def _skill_explain_result(self, task_id: str = "latest") -> Dict[str, Any]:
        s = self.session
        recs = [r for r in s.cpe.records.values() if task_id in ("latest", r.task_id)]
        last = recs[-1] if recs else None
        exp = s.xxe.explain_task(task_id)
        return {
            "task_id": task_id,
            "found": last is not None,
            "inputs": last.inputs if last else None,
            "output": last.output if last else None,
            "method": last.numerical_method if last else None,
            "narrative": exp.narrative,
            "invariants_declared": sorted(self.invariants),
        }

    def _skill_audit_run(self) -> Dict[str, Any]:
        s = self.session
        manifest = s.rme.generate_manifest(s.name)
        return {
            "session": s.name,
            "report": _plain(s.generate_report()),
            "decisions": len(s.xxe.decision_log),
            "skill_trace": list(self.execution_log),
            "failed_skills": [e for e in self.execution_log if e["status"] != "SUCCESS"],
            "manifest_seal": manifest.cryptographic_seal,
            "markdown": s.xxe.export_audit_markdown(),
        }

    def _skill_compare_runs(self, runs: Optional[List[Any]] = None, label: Optional[str] = None) -> Dict[str, Any]:
        snaps = [_plain(r) for r in runs] if runs else None
        if snaps is None:
            self.run_snapshots.append({"label": label or f"run_{len(self.run_snapshots) + 1}",
                                       **_plain(self.session.generate_report())})
            snaps = self.run_snapshots
        metrics = sorted({k for r in snaps for k, v in r.items()
                          if isinstance(v, (int, float)) and not isinstance(v, bool)})
        out: Dict[str, Any] = {}
        for m in metrics:
            vals = [r[m] for r in snaps if isinstance(r.get(m), (int, float))]
            out[m] = {"min": min(vals), "max": max(vals), "mean": sum(vals) / len(vals),
                      "delta_first_last": vals[-1] - vals[0]}
        return {"runs": len(snaps), "metrics": out}

    # ============================================================ 13. Reporting & Export
    def _skill_generate_report(self, format: str = "object") -> Any:
        rep = self.session.generate_report()
        if format == "object":
            return rep
        if format != "markdown":
            raise ValueError("format must be 'object' or 'markdown'")
        d = _plain(rep)
        lines = [f"# SFSA Report — {d['session_name']}", ""]
        lines += [f"- **{k}**: {v}" for k, v in d.items() if k != "session_name"]
        return "\n".join(lines)

    def _skill_export_graph(self) -> Dict[str, Any]:
        return self.session.fln.export_graph()

    def _skill_export_cache_manifest(self) -> Dict[str, Any]:
        s = self.session
        m = s.mate.export_manifest()
        m["provenance"] = [{"record_id": r.record_id, "task_id": r.task_id, "model_version": r.model_version,
                            "reuse_count": r.reuse_count} for r in s.cpe.records.values()]
        return m

    def _skill_export_thematic_map(self) -> Dict[str, Any]:
        rep = self.session.analyze_themes()
        return {"coverage_pct": rep.coverage_pct, "primary": rep.primary_themes,
                "secondary": rep.secondary_themes, "gaps": rep.thematic_gaps}

    def _skill_export_skill_trace(self) -> List[Dict[str, Any]]:
        return list(self.execution_log)

    # ============================================================ 14. Agent Planning
    def _skill_plan_computation(self, archetype: Any = "HIGH_PRECISION_SOLVE", input_cardinality: int = 1,
                                parameter_dim: int = 2, budget_remaining_seconds: Optional[float] = None,
                                tolerance: float = 0.05) -> Any:
        from sfsa.ore import QueryArchetype
        if not isinstance(archetype, QueryArchetype):
            try:
                archetype = QueryArchetype[str(archetype)]
            except KeyError:
                raise ValueError(f"Unknown archetype '{archetype}'. Valid: {[a.name for a in QueryArchetype]}")
        budget = budget_remaining_seconds if budget_remaining_seconds is not None \
            else self.session.tbe.get_remaining_seconds()
        return self.session.ore.plan_pipeline(archetype, input_cardinality, parameter_dim, budget, tolerance)

    def _skill_select_next_action(self, goal: Optional[str] = None) -> Dict[str, Any]:
        s = self.session
        if not s.fln.layers:
            return {"skill": "register_layer", "reason": "No layers registered: define the model first."}
        if not self.invariants:
            return {"skill": "declare_invariants", "reason": "No physical invariants declared for T3 verification."}
        if not s.aie.assumptions:
            return {"skill": "check_assumption_integrity", "reason": "No assumptions registered to audit."}
        if self._skill_detect_gaps():
            return {"skill": "suggest_gap_closure", "reason": "Model has parameter gaps."}
        if s.mate.stats().total_lookups == 0:
            return {"skill": "compute", "reason": "Nothing computed yet."}
        if not s.analyze_themes().coverage_pct or any("uncertainty" in g.lower() for g in s.analyze_themes().thematic_gaps):
            return {"skill": "analyze_sensitivity", "reason": "Uncertainty/sensitivity coverage is low."}
        return {"skill": "generate_report", "reason": "Model is set up and exercised: summarize results."}

    def _skill_dry_run(self, task_id: str = "dry_run", inputs: Optional[Dict[str, Any]] = None,
                       operations: int = 1000) -> Dict[str, Any]:
        """Predicts what compute() would do, without running any solver or mutating caches."""
        s = self.session
        inputs = inputs or {}
        ok, reason = s.cae.validate_inputs(inputs)
        cached = s.mate.lookup(task_id, inputs) is not None
        reuse = s.cpe.assess_reuse(task_id, inputs)
        if not ok:
            action = "ABORT_CONSTRAINT"
        elif cached:
            action = "CACHE_HIT"
        elif reuse.reuse_type.value == "APPROXIMATE_REUSE":
            action = "APPROXIMATE_REUSE"
        else:
            action = "FULL_COMPUTE"
        cost = 0 if action != "FULL_COMPUTE" else operations
        return {"predicted_action": action, "constraint_reason": reason, "cached": cached,
                "reuse_type": reuse.reuse_type.value, "estimated_operations": cost}

    def _skill_validate_skill_call(self, skill: Any, args: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        return self.validate(skill, args or {})

    def _skill_batch_queries(self, queries: List[Dict[str, float]], heavy_solver: Callable[..., float]) -> Any:
        return self.session.cqe.compress_and_solve(queries, heavy_solver)

    def _skill_prioritize_queries(self, queries: List[Dict[str, float]],
                                  cost_fn: Optional[Callable[[Dict[str, float]], float]] = None) -> List[Dict[str, Any]]:
        scored = []
        for q in queries:
            cost = max(float(cost_fn(q)) if cost_fn else 1.0, 1e-9)
            gain = self.session.asg.evaluate_candidate(q).information_gain
            scored.append({"query": q, "information_gain": gain, "cost": cost, "score": gain / cost})
        scored.sort(key=lambda r: r["score"], reverse=True)
        return scored
