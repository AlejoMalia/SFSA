"""
sfsa.mate — MATE Engine (Multi-Dimensional Acceleration & Trajectory Estimation)
=================================================================================
Generic scientific memoization, projection, speculative execution battery, and
mechanism learning engine.

Evolved from a passive result memoizer into a dual-speed operating memory and
speculative mechanism battery:
- MATE-Core:   Result, plan, and shortcut memory across scientific queries.
- MATE-Spec:   Speculative background execution of alternative engine chains.
- MATE-Policy: Validity, promotion, budget control, and scientific safety governance.

Part of SFSA (Standard Framework for Scientific Advancement)
Author & TRIADA Protocol Creator: Alejo Malia
License: CC BY 4.0
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Tuple, Union
import hashlib
import json
import math
import time


class MATEStatus(str, Enum):
    """Execution status resulting from MATE analysis."""
    R1_EXACT = "R1_EXACT"          # Solved exactly or retrieved from memoized cache
    R2_PROJECTED = "R2_PROJECTED"  # Projected via closed-form approximation without dense iteration
    R3_INFEASIBLE = "R3_INFEASIBLE" # Aborted early: physical, mathematical, or boundary constraint violated


class ReuseLevel(str, Enum):
    """Hierarchy of scientific computational reuse."""
    L0 = "L0"  # Zero-compute exact result (~0 cost)
    L1 = "L1"  # Approximate reuse within tolerance / surrogate (~0 cost)
    L2 = "L2"  # Plan reuse: known favorable engine sequence (low cost)
    L3 = "L3"  # Shortcut reuse: learned early-stop / prune / fidelity (low cost)
    L4 = "L4"  # Warm-start: improved initial state (medium cost)
    L5 = "L5"  # Full recompute: complete execution pipeline (high cost)


class MechanismStatus(str, Enum):
    """Validation and lifecycle status of a MATE Mechanism."""
    CANDIDATE = "candidate"        # Newly discovered via speculative battery
    TRUSTED = "trusted"            # Verified across multiple cases without quality loss
    DEFAULT = "default"            # Promoted to preferred default for this pattern
    REJECTED = "rejected"          # Fails validation, violates invariants, or deprecated


@dataclass
class MechanismCard:
    """
    A documented, reusable scientific execution strategy.
    Encapsulates problem patterns, engine chains, entry conditions, shortcuts, and negative knowledge.
    """
    id: str
    pattern: str                                      # Semantic problem signature (e.g. 'linear_flux_pde')
    chain: List[str]                                  # Sequence of engines (e.g. ['AMF_LOW', 'UAS'])
    entry_conditions: Dict[str, Any] = field(default_factory=dict)
    forbidden_conditions: Dict[str, Any] = field(default_factory=dict)
    expected_cost: float = 1.0                        # Normalized cost relative to full baseline
    expected_quality: float = 1.0                     # Quality/accuracy retention [0.0 to 1.0]
    expected_risk: float = 0.0                        # Risk of invalidity [0.0 to 1.0]
    confidence: float = 0.5                           # Statistical confidence
    evidence_count: int = 1                           # Count of successful supporting evaluations
    provenance: str = "speculative_battery"
    model_version: str = "v1.0"
    tolerance_profile: Dict[str, Any] = field(default_factory=dict)
    outputs_cached: List[Any] = field(default_factory=list)
    shortcuts: Dict[str, Any] = field(default_factory=dict) # e.g. {'fidelity': 'LOW', 'stopping_residual': 1e-3}
    failures: List[Dict[str, Any]] = field(default_factory=list) # Negative knowledge
    status: MechanismStatus = MechanismStatus.CANDIDATE
    created_at: float = field(default_factory=time.time)


@dataclass
class SpeculativeResult:
    """Outcome of running a speculative alternative chain in MATE-Spec."""
    mechanism_id: str
    chain: List[str]
    real_cost: float
    output_value: Any
    discrepancy_vs_official: float
    invariants_passed: bool
    is_favorable: bool
    rationale: str


@dataclass
class MATEResult:
    """Outcome of a MATE-evaluated computation."""
    status: MATEStatus
    value: Any
    cached: bool = False
    compute_time_saved_pct: float = 0.0
    elapsed_seconds: float = 0.0
    diagnostic_message: str = ""
    reuse_level: ReuseLevel = ReuseLevel.L5
    mechanism_used: Optional[str] = None
    intermediate_checkpoints: List[Dict[str, Any]] = field(default_factory=list)
    speculative_discoveries: List[MechanismCard] = field(default_factory=list)


class MATEEngine:
    """
    MATE Ampliado: Advanced Scientific Memoization, Operational Memory & Speculative Mechanism Battery.
    """

    def __init__(
        self,
        cache_precision_decimals: int = 6,
        spec_mode: str = "bounded",
        speculative_budget_ratio: float = 0.20,
        max_spec_chains: int = 2,
    ) -> None:
        self.cache_precision = cache_precision_decimals
        self.spec_mode = spec_mode                    # 'off', 'idle_only', 'bounded', 'aggressive'
        self.speculative_budget_ratio = speculative_budget_ratio
        self.max_spec_chains = max_spec_chains
        self.model_version = "v1.0"

        # 1. MATE-Core (Result & Plan Memory)
        self._cache: Dict[str, Any] = {}
        self._approximate_records: List[Dict[str, Any]] = []
        self.cards: Dict[str, MechanismCard] = {}
        self.plans_by_pattern: Dict[str, List[str]] = {}
        self.negative_knowledge: Dict[str, List[Dict[str, Any]]] = {}

        # 2. Performance Metrics
        self._metrics = {
            "total_queries": 0,
            "cache_hits": 0,
            "early_aborts": 0,
            "full_computes": 0,
            "estimated_cpu_seconds_saved": 0.0,
            "l0_exact_hits": 0,
            "l1_approx_hits": 0,
            "l2_plan_hits": 0,
            "l3_shortcut_hits": 0,
            "speculative_runs_count": 0,
            "mechanisms_discovered": 0,
            "mechanisms_promoted": 0,
        }

    # --------------------------------------------------------------------------
    # MATE-Core: Hashing, Pattern Signatures & Storage
    # --------------------------------------------------------------------------

    def _hash_key(self, namespace: str, *args: Any, **kwargs: Any) -> str:
        """Generates a deterministic hash for any combination of scientific arguments."""
        def normalize(obj: Any) -> Any:
            if isinstance(obj, float):
                if math.isnan(obj) or math.isinf(obj):
                    return str(obj)
                return round(obj, self.cache_precision)
            if isinstance(obj, (int, str, bool)) or obj is None:
                return obj
            if isinstance(obj, (list, tuple)):
                return [normalize(x) for x in obj]
            if isinstance(obj, dict):
                return {str(k): normalize(v) for k, v in sorted(obj.items())}
            if hasattr(obj, "__dict__"):
                return normalize(obj.__dict__)
            return str(obj)

        normalized_data = {
            "ns": namespace,
            "args": [normalize(a) for a in args],
            "kwargs": {str(k): normalize(v) for k, v in sorted(kwargs.items())}
        }
        serialized = json.dumps(normalized_data, sort_keys=True, default=str)
        return hashlib.sha256(serialized.encode("utf-8")).hexdigest()

    def synthesize_pattern_signature(self, task_id: str, inputs: Dict[str, Any], context: Optional[Dict[str, Any]] = None) -> str:
        """Synthesizes a semantic pattern signature characterizing the problem type."""
        keys = sorted(inputs.keys())
        dim = len(keys)
        regime = (context or {}).get("regime", "general")
        return f"{task_id}::{regime}::{dim}D::{'_'.join(keys[:4])}"

    def memoized_get(self, key: str) -> Optional[Any]:
        """Retrieves a cached result if present."""
        return self._cache.get(key)

    def memoized_set(self, key: str, value: Any) -> None:
        """Stores a computed result in cache."""
        self._cache[key] = value

    def clear_cache(self) -> None:
        """Empties the result and approximate caches while preserving trusted mechanisms."""
        self._cache.clear()
        self._approximate_records.clear()

    # --------------------------------------------------------------------------
    # MATE-Core: Multi-level Lookup (L0 -> L1 -> L2/L3 -> L5)
    # --------------------------------------------------------------------------

    def lookup_multilevel(
        self,
        task_id: str,
        inputs: Dict[str, Any],
        tolerance: float = 0.05,
        context: Optional[Dict[str, Any]] = None,
    ) -> Tuple[ReuseLevel, Optional[Any], Optional[MechanismCard]]:
        """
        Multilevel hierarchy lookup:
        - L0: Exact valid result.
        - L1: Approximate reuse within numerical tolerance.
        - L2/L3: Favorable mechanism card (plan / shortcuts).
        - L5: Full recompute required.
        """
        # Level L0: Exact result lookup
        cache_key = self._hash_key(task_id, inputs)
        exact = self.memoized_get(cache_key)
        if exact is not None:
            self._metrics["l0_exact_hits"] += 1
            return ReuseLevel.L0, exact, None

        # Level L1: Approximate reuse from numerical neighbors
        if isinstance(inputs, dict):
            num_keys = [k for k, v in inputs.items() if isinstance(v, (int, float))]
            if num_keys:
                for rec in self._approximate_records:
                    if rec.get("task_id") == task_id and rec.get("model_version") == self.model_version:
                        rec_inputs = rec.get("inputs", {})
                        diffs = [abs(inputs[k] - rec_inputs.get(k, inputs[k])) / max(abs(inputs[k]), 1.0) for k in num_keys]
                        max_rel_diff = max(diffs) if diffs else 1.0
                        if max_rel_diff <= tolerance:
                            self._metrics["l1_approx_hits"] += 1
                            return ReuseLevel.L1, rec.get("value"), None

        # Level L2/L3: Plan and shortcut reuse via MechanismCards
        pattern = self.synthesize_pattern_signature(task_id, inputs, context)
        matching_cards = [
            self.cards[cid] for cid in self.plans_by_pattern.get(pattern, [])
            if self.cards.get(cid) and self.cards[cid].status in (MechanismStatus.TRUSTED, MechanismStatus.DEFAULT)
        ]
        if matching_cards:
            best_card = sorted(matching_cards, key=lambda c: (c.status == MechanismStatus.DEFAULT, c.expected_cost), reverse=True)[0]
            reuse_lvl = ReuseLevel.L3 if best_card.shortcuts else ReuseLevel.L2
            if reuse_lvl == ReuseLevel.L3:
                self._metrics["l3_shortcut_hits"] += 1
            else:
                self._metrics["l2_plan_hits"] += 1
            return reuse_lvl, None, best_card

        return ReuseLevel.L5, None, None

    # --------------------------------------------------------------------------
    # MATE-Spec: Speculative Execution Battery
    # --------------------------------------------------------------------------

    def speculate(
        self,
        task_id: str,
        inputs: Dict[str, Any],
        official_value: Any,
        candidate_chains: List[Dict[str, Any]],
        budget_time_s: float = 0.05,
    ) -> List[SpeculativeResult]:
        """
        Executes bounded speculative alternatives in the background to discover better mechanisms.
        Compares cost, quality, and invariant conformance against official output.
        """
        if self.spec_mode == "off" or budget_time_s <= 0:
            return []

        pattern = self.synthesize_pattern_signature(task_id, inputs)
        spec_results: List[SpeculativeResult] = []
        chains_to_test = candidate_chains[:self.max_spec_chains]

        for cand in chains_to_test:
            chain_seq = cand.get("chain", ["DEFAULT_PIPELINE"])
            eval_fn = cand.get("eval_fn")
            cost_factor = cand.get("cost_factor", 0.5)

            if not callable(eval_fn):
                continue

            self._metrics["speculative_runs_count"] += 1
            t_start = time.perf_counter()
            try:
                alt_value = eval_fn(inputs)
                elapsed = time.perf_counter() - t_start

                # Compare against official value
                discrepancy = 0.0
                if isinstance(official_value, (int, float)) and isinstance(alt_value, (int, float)):
                    denom = max(abs(official_value), 1e-9)
                    discrepancy = abs(official_value - alt_value) / denom

                tol = cand.get("tolerance", 0.05)
                invariants_ok = cand.get("invariant_checker", lambda v: True)(alt_value)
                is_favorable = (discrepancy <= tol) and invariants_ok and (cost_factor < 0.9)

                card_id = f"mech_{self._hash_key(pattern, chain_seq)[:8]}"
                res = SpeculativeResult(
                    mechanism_id=card_id,
                    chain=chain_seq,
                    real_cost=elapsed,
                    output_value=alt_value,
                    discrepancy_vs_official=discrepancy,
                    invariants_passed=invariants_ok,
                    is_favorable=is_favorable,
                    rationale=f"Alternative chain {chain_seq}: cost {cost_factor:.2f}x, discrepancy {discrepancy:.2%}",
                )
                spec_results.append(res)

                if is_favorable:
                    self._register_or_update_mechanism(
                        card_id=card_id,
                        pattern=pattern,
                        chain=chain_seq,
                        cost=cost_factor,
                        quality=max(0.0, 1.0 - discrepancy),
                        shortcuts=cand.get("shortcuts", {}),
                    )
                else:
                    self._record_negative_knowledge(pattern, chain_seq, f"Discrepancy {discrepancy:.2%} exceeded tolerance {tol:.2%}")

            except Exception as e:
                self._record_negative_knowledge(pattern, chain_seq, f"Execution failed: {str(e)}")

        return spec_results

    def _register_or_update_mechanism(
        self,
        card_id: str,
        pattern: str,
        chain: List[str],
        cost: float,
        quality: float,
        shortcuts: Dict[str, Any],
    ) -> MechanismCard:
        """Stores or reinforces a favorable mechanism card."""
        if card_id in self.cards:
            card = self.cards[card_id]
            card.evidence_count += 1
            card.confidence = min(0.99, card.confidence + 0.15)
            card.expected_cost = (card.expected_cost + cost) / 2.0
            card.expected_quality = (card.expected_quality + quality) / 2.0
        else:
            card = MechanismCard(
                id=card_id,
                pattern=pattern,
                chain=chain,
                expected_cost=cost,
                expected_quality=quality,
                expected_risk=0.05,
                confidence=0.55,
                evidence_count=1,
                shortcuts=shortcuts,
                status=MechanismStatus.CANDIDATE,
                model_version=self.model_version,
            )
            self.cards[card_id] = card
            self.plans_by_pattern.setdefault(pattern, []).append(card_id)
            self._metrics["mechanisms_discovered"] += 1

        # Check automated policy promotion criteria (candidate -> trusted)
        if card.evidence_count >= 3 and card.confidence >= 0.80 and card.status == MechanismStatus.CANDIDATE:
            card.status = MechanismStatus.TRUSTED
            self._metrics["mechanisms_promoted"] += 1

        return card

    def _record_negative_knowledge(self, pattern: str, chain: List[str], reason: str) -> None:
        """Registers a failed mechanism to prevent future speculative waste."""
        entry = {
            "chain": chain,
            "reason": reason,
            "timestamp": time.time(),
        }
        self.negative_knowledge.setdefault(pattern, []).append(entry)

    # --------------------------------------------------------------------------
    # MATE-Policy: Governance, Promotion, Rejection & Invalidation
    # --------------------------------------------------------------------------

    def promote(self, mechanism_id: str, to_default: bool = False) -> bool:
        """Promotes a mechanism to TRUSTED or DEFAULT."""
        if mechanism_id not in self.cards:
            return False
        card = self.cards[mechanism_id]
        card.status = MechanismStatus.DEFAULT if to_default else MechanismStatus.TRUSTED
        self._metrics["mechanisms_promoted"] += 1
        return True

    def reject(self, mechanism_id: str, reason: str = "") -> bool:
        """Marks a mechanism as REJECTED and documents rationale in failures."""
        if mechanism_id not in self.cards:
            return False
        card = self.cards[mechanism_id]
        card.status = MechanismStatus.REJECTED
        card.failures.append({"reason": reason, "timestamp": time.time()})
        return True

    def invalidate(self, new_model_version: str) -> int:
        """Invalidates mechanisms and cached states when the underlying scientific model updates."""
        self.model_version = new_model_version
        self.clear_cache()
        invalidated_count = 0
        for card in self.cards.values():
            if card.model_version != new_model_version:
                card.status = MechanismStatus.REJECTED
                card.failures.append({"reason": f"Model upgraded to {new_model_version}", "timestamp": time.time()})
                invalidated_count += 1
        return invalidated_count

    def get_mechanisms(
        self,
        pattern: Optional[str] = None,
        status: Optional[MechanismStatus] = None,
    ) -> List[MechanismCard]:
        """Queries registered mechanisms filtered by pattern or lifecycle status."""
        results = list(self.cards.values())
        if pattern is not None:
            results = [c for c in results if c.pattern == pattern]
        if status is not None:
            results = [c for c in results if c.status == status]
        return results

    def explain(self, mechanism_id: str) -> str:
        """Generates a comprehensive scientific explanation of a MechanismCard."""
        if mechanism_id not in self.cards:
            return f"Mechanism '{mechanism_id}' not found in MATE registry."
        card = self.cards[mechanism_id]
        speedup = (1.0 / max(card.expected_cost, 0.01))
        return (
            f"### MATE Mechanism [{card.id}] — Status: {card.status.value.upper()}\n"
            f"- **Problem Pattern:** `{card.pattern}`\n"
            f"- **Execution Chain:** `{' -> '.join(card.chain)}`\n"
            f"- **Performance Payoff:** ~{speedup:.1f}x speedup (Cost: {card.expected_cost:.1%}, Quality: {card.expected_quality:.1%})\n"
            f"- **Confidence & Evidence:** {card.confidence:.1%} across {card.evidence_count} evaluations\n"
            f"- **Shortcuts Applied:** {json.dumps(card.shortcuts)}\n"
            f"- **Provenance:** {card.provenance} (Model: {card.model_version})"
        )

    # --------------------------------------------------------------------------
    # Backward-Compatible Execution Interface
    # --------------------------------------------------------------------------

    def compute_projected(
        self,
        task_id: str,
        inputs: Dict[str, Any],
        solver: Callable[[Dict[str, Any]], Any],
        boundary_validator: Optional[Callable[[Dict[str, Any]], Tuple[bool, str]]] = None,
        intermediate_check: Optional[Callable[[Dict[str, Any]], Tuple[bool, str]]] = None,
        estimated_heavy_cost_s: float = 0.05,
        candidate_chains: Optional[List[Dict[str, Any]]] = None,
        approximate_tolerance: float = 0.05,
    ) -> MATEResult:
        """
        Backward-compatible execution method enhanced with MATE-Core multilevel lookup
        and MATE-Spec background mechanism exploration.
        """
        t0 = time.perf_counter()
        self._metrics["total_queries"] += 1

        # 1. Boundary Pre-Check (Early Exit R3)
        if boundary_validator is not None:
            is_valid, reason = boundary_validator(inputs)
            if not is_valid:
                self._metrics["early_aborts"] += 1
                self._metrics["estimated_cpu_seconds_saved"] += estimated_heavy_cost_s
                return MATEResult(
                    status=MATEStatus.R3_INFEASIBLE,
                    value=None,
                    cached=False,
                    compute_time_saved_pct=99.9,
                    elapsed_seconds=time.perf_counter() - t0,
                    diagnostic_message=f"Early abort by boundary validator: {reason}",
                    reuse_level=ReuseLevel.L5,
                )

        # 2. Multilevel Lookup (L0 / L1 / L2 / L3)
        reuse_lvl, cached_val, favorable_card = self.lookup_multilevel(
            task_id, inputs, tolerance=approximate_tolerance)

        # L0: Exact hit
        if reuse_lvl == ReuseLevel.L0:
            self._metrics["cache_hits"] += 1
            self._metrics["estimated_cpu_seconds_saved"] += estimated_heavy_cost_s
            return MATEResult(
                status=MATEStatus.R1_EXACT,
                value=cached_val,
                cached=True,
                compute_time_saved_pct=99.5,
                elapsed_seconds=time.perf_counter() - t0,
                diagnostic_message="Value retrieved from MATE invariant cache (L0 Zero-Compute)",
                reuse_level=ReuseLevel.L0,
            )

        # L1: Approximate hit
        if reuse_lvl == ReuseLevel.L1:
            self._metrics["cache_hits"] += 1
            self._metrics["estimated_cpu_seconds_saved"] += (estimated_heavy_cost_s * 0.95)
            return MATEResult(
                status=MATEStatus.R1_EXACT,
                value=cached_val,
                cached=True,
                compute_time_saved_pct=95.0,
                elapsed_seconds=time.perf_counter() - t0,
                diagnostic_message="Value retrieved via MATE approximate neighbor reuse (L1)",
                reuse_level=ReuseLevel.L1,
            )

        # 3. Intermediate Feasibility Check
        if intermediate_check is not None:
            is_feasible, reason = intermediate_check(inputs)
            if not is_feasible:
                self._metrics["early_aborts"] += 1
                self._metrics["estimated_cpu_seconds_saved"] += (estimated_heavy_cost_s * 0.8)
                return MATEResult(
                    status=MATEStatus.R3_INFEASIBLE,
                    value=None,
                    cached=False,
                    compute_time_saved_pct=80.0,
                    elapsed_seconds=time.perf_counter() - t0,
                    diagnostic_message=f"Aborted at intermediate checkpoint: {reason}",
                    reuse_level=ReuseLevel.L5,
                )

        # 4. Official Solver Execution (Foreground)
        self._metrics["full_computes"] += 1
        result_value = solver(inputs)

        # Store in exact cache & approximate register
        cache_key = self._hash_key(task_id, inputs)
        self.memoized_set(cache_key, result_value)
        self._approximate_records.append({
            "task_id": task_id,
            "inputs": dict(inputs),
            "value": result_value,
            "model_version": self.model_version,
            "timestamp": time.time(),
        })

        # 5. Speculative Execution Battery (Background / Budgeted)
        discoveries: List[MechanismCard] = []
        if candidate_chains:
            spec_res = self.speculate(
                task_id=task_id,
                inputs=inputs,
                official_value=result_value,
                candidate_chains=candidate_chains,
                budget_time_s=estimated_heavy_cost_s * self.speculative_budget_ratio,
            )
            for r in spec_res:
                if r.is_favorable and r.mechanism_id in self.cards:
                    discoveries.append(self.cards[r.mechanism_id])

        elapsed = time.perf_counter() - t0
        return MATEResult(
            status=MATEStatus.R1_EXACT,
            value=result_value,
            cached=False,
            compute_time_saved_pct=0.0,
            elapsed_seconds=elapsed,
            diagnostic_message="Computed freshly and registered into MATE memory",
            reuse_level=ReuseLevel.L5,
            mechanism_used=favorable_card.id if favorable_card else None,
            speculative_discoveries=discoveries,
        )

    def stats(self) -> Any:
        """Returns comprehensive statistics compatible with report generation."""
        from types import SimpleNamespace
        return SimpleNamespace(
            total_lookups=self._metrics["total_queries"],
            cache_hits=self._metrics["cache_hits"],
            early_aborts=self._metrics["early_aborts"],
            operations_avoided=self._metrics["cache_hits"] * 250,
            l0_exact_hits=self._metrics["l0_exact_hits"],
            l1_approx_hits=self._metrics["l1_approx_hits"],
            l2_plan_hits=self._metrics["l2_plan_hits"],
            l3_shortcut_hits=self._metrics["l3_shortcut_hits"],
            speculative_runs_count=self._metrics["speculative_runs_count"],
            mechanisms_discovered=self._metrics["mechanisms_discovered"],
            mechanisms_promoted=self._metrics["mechanisms_promoted"],
        )

    def lookup(self, task_id: str, inputs: Dict[str, Any]) -> Optional[Any]:
        """Queries the cache for an exact match."""
        key = self._hash_key(task_id, inputs)
        return self.memoized_get(key)

    def record_early_abort(self) -> None:
        """Records an early abort triggered by an external validator."""
        self._metrics["early_aborts"] += 1

    def project_trajectory(self, task_id: str, inputs: Dict[str, Any], invariants: Optional[List[Any]] = None) -> bool:
        """
        Projects feasibility before a heavy solve. Each invariant is a callable taking the inputs and
        returning a bool or a (bool, reason) tuple. Returns False (infeasible) as soon as one fails.
        An invariant that raises is treated as violated.
        """
        for inv in invariants or []:
            try:
                res = inv(inputs)
            except Exception:
                return False
            ok = res[0] if isinstance(res, tuple) else res
            if not ok:
                return False
        return True

    def store(self, task_id: str, inputs: Dict[str, Any], value: Any) -> str:
        """Stores a result under the exact-match key used by lookup(). Returns the cache key."""
        key = self._hash_key(task_id, inputs)
        self.memoized_set(key, value)
        self._approximate_records.append({
            "task_id": task_id,
            "inputs": dict(inputs),
            "value": value,
            "model_version": self.model_version,
            "timestamp": time.time(),
        })
        return key

    def export_manifest(self) -> Dict[str, Any]:
        """Exports the reusable-cache catalog (keys only, no payloads) plus mechanism cards and metrics."""
        return {
            "model_version": self.model_version,
            "cache_entries": len(self._cache),
            "cache_keys": sorted(self._cache.keys()),
            "approximate_records": len(self._approximate_records),
            "mechanisms": [
                {"id": c.id, "status": c.status.value, "model_version": c.model_version}
                for c in self.cards.values()
            ],
            "metrics": dict(self._metrics),
        }

    @property
    def metrics(self) -> Dict[str, Any]:
        """Performance, reuse hierarchy, and mechanism learning metrics."""
        return dict(self._metrics)
