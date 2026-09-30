"""
sfsa — Empirical Benchmark for MATE Ampliado across 3 Operational Regimes
========================================================================
Comprehensive multi-regime empirical stress test:
1. Régimen Estructurado (Clustered sweeps, exact repeats, tight perturbations)
2. Régimen Semi-Aleatorio (Sparse jumps, wide parameter leaps, partial locality)
3. Régimen Solver Pesado (High-cost dense workload, e.g., ~12-15 ms/query)

Reports across all 3 regimes:
- % Hits Distribution L0–L5
- Speculative Battery ROI (Speculation Cost vs. Future Net Savings)
- Net Campaign Speedup & Wall-Clock Reduction %
- MechanismCards Promoted vs. Negative Knowledge Captured

Part of SFSA (Standard Framework for Scientific Advancement)
Author & Protocol Creator: Alejo Malia
License: CC BY 4.0
"""

import math
import random
import time
from sfsa.mate import MATEEngine, ReuseLevel, MechanismStatus


# --------------------------------------------------------------------------
# Solvers & Speculative Surrogate Models
# --------------------------------------------------------------------------

T_INTEGRAL = 10.0


def standard_scientific_solver(inputs):
    """Standard non-linear reactive transport solver (~0.3-0.4 ms/eval, 1200 steps)."""
    temp = inputs.get("temperature", 300.0)
    pres = inputs.get("pressure", 1.0)
    n_steps = 1200
    dt = T_INTEGRAL / n_steps
    res = sum(
        math.sin(temp * 0.005 + (s * dt) * 0.5) * math.cos(pres * 0.02 + (s * dt) * 0.25) * dt
        for s in range(n_steps)
    )
    return (temp / 100.0) ** 1.5 * math.log(pres + 1.0) + res


def heavy_dense_scientific_solver(inputs):
    """Heavy scientific solver simulating dense 3D / stiff ODE (~12-16 ms/eval, 45,000 steps)."""
    temp = inputs.get("temperature", 300.0)
    pres = inputs.get("pressure", 1.0)
    n_steps = 45000
    dt = T_INTEGRAL / n_steps
    res = sum(
        math.sin(temp * 0.005 + (s * dt) * 0.5) * math.cos(pres * 0.02 + (s * dt) * 0.25) * dt
        for s in range(n_steps)
    )
    return (temp / 100.0) ** 1.5 * math.log(pres + 1.0) + res


def coarse_discretization_model(inputs):
    """Coarse discretization surrogate (200 steps, ~0.06 ms, error < 0.5%)."""
    temp = inputs.get("temperature", 300.0)
    pres = inputs.get("pressure", 1.0)
    n_steps = 200
    dt = T_INTEGRAL / n_steps
    res = sum(
        math.sin(temp * 0.005 + (s * dt) * 0.5) * math.cos(pres * 0.02 + (s * dt) * 0.25) * dt
        for s in range(n_steps)
    )
    return (temp / 100.0) ** 1.5 * math.log(pres + 1.0) + res


def cheap_surrogate_model(inputs):
    """Fast analytical surrogate approximation (< 0.003 ms)."""
    temp = inputs.get("temperature", 300.0)
    pres = inputs.get("pressure", 1.0)
    return (temp / 100.0) ** 1.5 * math.log(pres + 1.0)


def divergent_bad_model(inputs):
    """Infeasible candidate model that fails tolerance check (divergence)."""
    return 0.0


# --------------------------------------------------------------------------
# Multi-Regime Benchmark Runner
# --------------------------------------------------------------------------

def run_regime_benchmark(regime_name, campaign_queries, solver_fn):
    total_queries = len(campaign_queries)
    
    # 1. Baseline Execution (Brute-Force without MATE)
    t0_base = time.perf_counter()
    for q in campaign_queries:
        solver_fn(q)
    t_baseline_total = time.perf_counter() - t0_base
    avg_solver_cost = t_baseline_total / total_queries

    # 2. MATE Ampliado Execution (Multilevel + Speculative Battery)
    mate = MATEEngine(
        cache_precision_decimals=4,
        spec_mode="bounded",
        speculative_budget_ratio=0.20,
        max_spec_chains=3,
    )
    
    candidate_chains = [
        {
            "chain": ["COARSE_DISCRETIZATION", "UAS"],
            "eval_fn": coarse_discretization_model,
            "cost_factor": 0.05,
            "tolerance": 0.02,
            "shortcuts": {"fidelity": "COARSE_MESH", "stopping_step": 200},
        },
        {
            "chain": ["AMF_SURROGATE", "UAS"],
            "eval_fn": cheap_surrogate_model,
            "cost_factor": 0.01,
            "tolerance": 0.01,
            "shortcuts": {"fidelity": "SURROGATE", "tolerance": 0.01},
        },
        {
            "chain": ["DIVERGENT_MODEL"],
            "eval_fn": divergent_bad_model,
            "cost_factor": 0.005,
            "tolerance": 0.01,
        },
    ]

    level_counts = {
        ReuseLevel.L0: 0,
        ReuseLevel.L1: 0,
        ReuseLevel.L2: 0,
        ReuseLevel.L3: 0,
        ReuseLevel.L5: 0,
    }

    t0_mate = time.perf_counter()
    speculative_time_total = 0.0

    for q in campaign_queries:
        reuse_lvl, cached_val, favorable_card = mate.lookup_multilevel("reacting_flow", q, tolerance=0.015)

        if reuse_lvl in (ReuseLevel.L0, ReuseLevel.L1):
            level_counts[reuse_lvl] += 1
            continue

        elif reuse_lvl in (ReuseLevel.L2, ReuseLevel.L3) and favorable_card:
            level_counts[reuse_lvl] += 1
            if "fidelity" in favorable_card.shortcuts and favorable_card.shortcuts["fidelity"] == "SURROGATE":
                val = cheap_surrogate_model(q)
            else:
                val = coarse_discretization_model(q)
            continue

        # L5: Full compute required + background speculative exploration
        level_counts[ReuseLevel.L5] += 1
        res = mate.compute_projected(
            task_id="reacting_flow",
            inputs=q,
            solver=solver_fn,
            candidate_chains=candidate_chains,
            estimated_heavy_cost_s=avg_solver_cost,
        )
        if candidate_chains:
            speculative_time_total += (avg_solver_cost * mate.speculative_budget_ratio)

    t_mate_total = time.perf_counter() - t0_mate

    # Metrics calculation
    pct_l0 = (level_counts[ReuseLevel.L0] / total_queries) * 100.0
    pct_l1 = (level_counts[ReuseLevel.L1] / total_queries) * 100.0
    pct_l2 = (level_counts[ReuseLevel.L2] / total_queries) * 100.0
    pct_l3 = (level_counts[ReuseLevel.L3] / total_queries) * 100.0
    pct_l5 = (level_counts[ReuseLevel.L5] / total_queries) * 100.0
    pct_reused_total = 100.0 - pct_l5

    queries_saved_by_mechanisms = level_counts[ReuseLevel.L2] + level_counts[ReuseLevel.L3]
    gross_time_saved = queries_saved_by_mechanisms * (avg_solver_cost * 0.95)
    speculative_roi = gross_time_saved / max(speculative_time_total, 1e-6)

    speedup_factor = t_baseline_total / max(t_mate_total, 1e-6)
    net_wall_clock_saved_pct = ((t_baseline_total - t_mate_total) / t_baseline_total) * 100.0

    cards_promoted = sum(1 for c in mate.cards.values() if c.status in (MechanismStatus.TRUSTED, MechanismStatus.DEFAULT))
    cards_candidate = sum(1 for c in mate.cards.values() if c.status == MechanismStatus.CANDIDATE)
    negative_captured = len(mate.negative_knowledge)

    return {
        "regime": regime_name,
        "total_queries": total_queries,
        "t_baseline_ms": t_baseline_total * 1000.0,
        "t_mate_ms": t_mate_total * 1000.0,
        "speedup_factor": speedup_factor,
        "saved_pct": net_wall_clock_saved_pct,
        "pct_l0": pct_l0,
        "pct_l1": pct_l1,
        "pct_l2": pct_l2,
        "pct_l3": pct_l3,
        "pct_l5": pct_l5,
        "pct_reused": pct_reused_total,
        "spec_cost_ms": speculative_time_total * 1000.0,
        "time_saved_ms": gross_time_saved * 1000.0,
        "spec_roi": speculative_roi,
        "cards_promoted": cards_promoted,
        "cards_candidate": cards_candidate,
        "negative_captured": negative_captured,
    }


def run_all_three_regimes():
    random.seed(42)
    
    # -------------------------------------------------------------------------
    # Regime 1: Estructurado (Structured sweep)
    # -------------------------------------------------------------------------
    base_points = [
        {"temperature": 350.0, "pressure": 2.5},
        {"temperature": 400.0, "pressure": 5.0},
        {"temperature": 450.0, "pressure": 8.0},
        {"temperature": 500.0, "pressure": 12.0},
    ]
    queries_structured = []
    for pt in base_points: queries_structured.append(dict(pt))
    for _ in range(25): queries_structured.append(dict(random.choice(base_points)))
    for _ in range(30):
        bp = random.choice(base_points)
        queries_structured.append({
            "temperature": bp["temperature"] * (1.0 + random.uniform(-0.004, 0.004)),
            "pressure": bp["pressure"] * (1.0 + random.uniform(-0.004, 0.004)),
        })
    for _ in range(45):
        queries_structured.append({
            "temperature": random.uniform(320.0, 520.0),
            "pressure": random.uniform(2.0, 14.0),
        })
    for _ in range(16):
        queries_structured.append({
            "temperature": random.uniform(600.0, 900.0),
            "pressure": random.uniform(20.0, 45.0),
        })

    # -------------------------------------------------------------------------
    # Regime 2: Semi-Aleatorio (Jumps & dispersed space)
    # -------------------------------------------------------------------------
    queries_semi_random = []
    # Fewer exact repeats (10)
    for _ in range(10): queries_semi_random.append(dict(random.choice(base_points)))
    # Larger perturbations (15 points with +-6% jumps)
    for _ in range(15):
        bp = random.choice(base_points)
        queries_semi_random.append({
            "temperature": bp["temperature"] * (1.0 + random.uniform(-0.06, 0.06)),
            "pressure": bp["pressure"] * (1.0 + random.uniform(-0.06, 0.06)),
        })
    # Wide dispersed space across 4 regimes (65 queries)
    for _ in range(65):
        queries_semi_random.append({
            "temperature": random.uniform(200.0, 1200.0),
            "pressure": random.uniform(0.5, 60.0),
        })
    # Random novel points (30 queries)
    for _ in range(30):
        queries_semi_random.append({
            "temperature": random.uniform(100.0, 2000.0),
            "pressure": random.uniform(0.1, 100.0),
        })

    # -------------------------------------------------------------------------
    # Regime 3: Solver Pesado (Heavy dense workload on structured queries)
    # -------------------------------------------------------------------------
    queries_heavy = list(queries_structured)

    # Execute all 3 benchmarks
    res_structured = run_regime_benchmark("1. Estructurado", queries_structured, standard_scientific_solver)
    res_semi_random = run_regime_benchmark("2. Semi-Aleatorio", queries_semi_random, standard_scientific_solver)
    res_heavy = run_regime_benchmark("3. Solver Pesado", queries_heavy, heavy_dense_scientific_solver)

    return [res_structured, res_semi_random, res_heavy]


if __name__ == "__main__":
    results = run_all_three_regimes()

    print("=" * 88)
    print("SFSA — MATE AMPLIADO 3-REGIME EMPIRICAL VERIFICATION BENCHMARK")
    print("=" * 88)
    print(f"{'Regime':<18} | {'Baseline':<9} | {'MATE Time':<10} | {'Speedup':<9} | {'Saved %':<8} | {'Low-Lat %':<9} | {'ROI':<7}")
    print("-" * 88)
    for r in results:
        base_s = f"{r['t_baseline_ms']:.1f} ms"
        mate_s = f"{r['t_mate_ms']:.1f} ms"
        sp_s = f"{r['speedup_factor']:.2f}x"
        sav_s = f"{r['saved_pct']:.1f}%"
        ll_s = f"{r['pct_reused']:.1f}%"
        roi_s = f"{r['spec_roi']:.1f}x"
        print(f"{r['regime']:<18} | {base_s:<9} | {mate_s:<10} | {sp_s:<9} | {sav_s:<8} | {ll_s:<9} | {roi_s:<7}")
    print("=" * 88)

    for r in results:
        print(f"\n>>> REGIME DETAILED BREAKDOWN: {r['regime'].upper()}")
        print(f"    - Baseline Time:       {r['t_baseline_ms']:.2f} ms")
        print(f"    - MATE Ampliado Time:  {r['t_mate_ms']:.2f} ms")
        print(f"    - Net Speedup:         {r['speedup_factor']:.2f}x ({r['saved_pct']:.1f}% time saved)")
        print(f"    - Level Distribution:  L0: {r['pct_l0']:.1f}% | L1: {r['pct_l1']:.1f}% | L2: {r['pct_l2']:.1f}% | L3: {r['pct_l3']:.1f}% | L5: {r['pct_l5']:.1f}%")
        print(f"    - Speculative Battery: Cost: {r['spec_cost_ms']:.2f} ms | Saved: {r['time_saved_ms']:.2f} ms | ROI: {r['spec_roi']:.1f}x")
        print(f"    - Mechanism Cards:     Promoted: {r['cards_promoted']} | Candidates: {r['cards_candidate']} | Negatives Captured: {r['negative_captured']}")
