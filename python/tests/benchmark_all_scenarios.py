"""
benchmark_all_scenarios.py — Calibrated Empirical Benchmark for SFSA Scenarios
=============================================================================
Runs real, empirical wall-clock measurements across each specific engine archetype:
1. MATE Cache & Reuse
2. AMF Multi-Fidelity Routing
3. ASG Adaptive Sampling vs Dense Grid (Realistic simulation workload)
4. UAS Uncertainty-Aware Early Stopping (Iterative solver workload)
5. Single Isolated Run (Measuring framework overhead on 1-shot execution)
6. CQE Query Compression Batch
"""

import time
import math
from sfsa import (
    SFSASession,
    AdaptiveMultiFidelityEngine,
    AdaptiveSamplingEngine,
    SensitivityReductionAnalyzer,
    UncertaintyAwareStoppingEngine,
    QueryCompressionEngine,
)


def run_all_benchmarks():
    print("=" * 70)
    print("RUNNING EMPIRICAL SFSA HARDWARE BENCHMARKS (Darwin ARM64)")
    print("=" * 70)

    results = {}

    # 1. MATE Cache & Reuse (N = 1000)
    def heavy_integral(x, y):
        s = 0.0
        for i in range(250):
            s += math.sin(x + i * 0.01) * math.cos(y + i * 0.01)
        return s

    inputs_1000 = [{"x": float(i % 25), "y": float((i * 2) % 20)} for i in range(1000)]

    t0 = time.perf_counter()
    for inp in inputs_1000:
        heavy_integral(inp["x"], inp["y"])
    t_base_1 = time.perf_counter() - t0

    session = SFSASession()
    t0 = time.perf_counter()
    for inp in inputs_1000:
        session.mate.compute_projected(
            task_id="heavy_int",
            inputs=inp,
            solver=lambda p: heavy_integral(p["x"], p["y"]),
        )
    t_sfsa_1 = time.perf_counter() - t0
    saved_1 = (1.0 - (t_sfsa_1 / t_base_1)) * 100.0
    results["1. MATE Cache & Reuse (N=1000)"] = {
        "baseline_ms": t_base_1 * 1000,
        "sfsa_ms": t_sfsa_1 * 1000,
        "saved_pct": saved_1,
        "speedup": t_base_1 / max(t_sfsa_1, 1e-9),
    }

    # 2. AMF Multi-Fidelity Routing (N = 500)
    def expensive_sim(p):
        v = 0.0
        for i in range(300):
            v += math.sin(p["temp"] * 0.01 + i)
        return v

    def cheap_sim(p):
        v = 0.0
        for i in range(15):
            v += math.sin(p["temp"] * 0.01 + i)
        unc = 0.02 if p["temp"] < 400 else 0.20
        return v * 20.0, unc

    amf_inputs = [{"temp": 280.0 + (i % 50) * 3.0} for i in range(500)]

    t0 = time.perf_counter()
    for inp in amf_inputs:
        expensive_sim(inp)
    t_base_2 = time.perf_counter() - t0

    amf = AdaptiveMultiFidelityEngine(default_tolerance=0.05)
    t0 = time.perf_counter()
    for inp in amf_inputs:
        amf.evaluate(
            task_id="amf_task",
            inputs=inp,
            cheap_solver=cheap_sim,
            expensive_solver=expensive_sim,
            benchmark_cost_factor=20.0,
        )
    t_sfsa_2 = time.perf_counter() - t0
    saved_2 = (1.0 - (t_sfsa_2 / t_base_2)) * 100.0
    results["2. AMF Multi-Fidelity Routing (N=500)"] = {
        "baseline_ms": t_base_2 * 1000,
        "sfsa_ms": t_sfsa_2 * 1000,
        "saved_pct": saved_2,
        "speedup": t_base_2 / max(t_sfsa_2, 1e-9),
    }

    # 3. ASG Adaptive Sampling vs Dense Grid (Workload: dense response calculation)
    # A candidate grid of 400 points (20x20).
    # Each physical evaluation solves a non-linear ODE integration step (1000 iterations).
    def scientific_ode_response(p):
        v = 1.0
        for step in range(1200):
            v += math.sin(p["x"] * 0.2 + step * 0.01) * math.cos(p["y"] * 0.2 + step * 0.01)
        return v

    grid_400 = [{"x": float(x), "y": float(y)} for x in range(20) for y in range(20)]

    # Baseline: sweep all 400 grid points
    t0 = time.perf_counter()
    for pt in grid_400:
        scientific_ode_response(pt)
    t_base_3 = time.perf_counter() - t0

    # ASG: adaptive acquisition
    asg = AdaptiveSamplingEngine(min_euclidean_distance=0.15)
    t0 = time.perf_counter()
    sampled_count = 0
    for pt in grid_400:
        cand = asg.evaluate_candidate(pt)
        if not cand.skip_recommended:
            scientific_ode_response(pt)
            asg.record_evaluation(pt, 0.0)
            sampled_count += 1
    t_sfsa_3 = time.perf_counter() - t0
    saved_3 = (1.0 - (t_sfsa_3 / t_base_3)) * 100.0
    results["3. ASG Adaptive Sampling vs Grid (400 pts, ODE workload)"] = {
        "baseline_ms": t_base_3 * 1000,
        "sfsa_ms": t_sfsa_3 * 1000,
        "saved_pct": saved_3,
        "speedup": t_base_3 / max(t_sfsa_3, 1e-9),
        "points_evaluated": sampled_count,
        "points_skipped": 400 - sampled_count,
    }

    # 4. UAS Uncertainty Early Stopping (Iterative PDE / relaxation loop)
    # Baseline: fixed 200 relaxation steps (each step: 200 math ops)
    # UAS: stops when convergence residual < 1e-4
    def pde_relaxation_step(val):
        for _ in range(250):
            val = val * 0.85 + 0.15 * 3.14159
        return val

    uas = UncertaintyAwareStoppingEngine(target_tolerance=1e-4)

    t0 = time.perf_counter()
    for prob in range(20):
        val = 100.0
        for it in range(200):
            val = pde_relaxation_step(val)
    t_base_4 = time.perf_counter() - t0

    t0 = time.perf_counter()
    for prob in range(20):
        val_uas = 100.0
        for it in range(200):
            prev = val_uas
            val_uas = pde_relaxation_step(val_uas)
            stop_eval = uas.evaluate_step(it, val_uas, prev, 200)
            if stop_eval.should_stop:
                break
    t_sfsa_4 = time.perf_counter() - t0
    saved_4 = (1.0 - (t_sfsa_4 / t_base_4)) * 100.0
    results["4. UAS Uncertainty Early Stopping (20 PDE loops)"] = {
        "baseline_ms": t_base_4 * 1000,
        "sfsa_ms": t_sfsa_4 * 1000,
        "saved_pct": saved_4,
        "speedup": t_base_4 / max(t_sfsa_4, 1e-9),
    }

    # 5. Single Isolated Run (N=1, no reuse)
    single_inp = {"x": 12.5, "y": 4.2}
    t0 = time.perf_counter()
    heavy_integral(single_inp["x"], single_inp["y"])
    t_base_5 = time.perf_counter() - t0

    session_iso = SFSASession()
    t0 = time.perf_counter()
    session_iso.mate.compute_projected(
        task_id="single_iso",
        inputs=single_inp,
        solver=lambda p: heavy_integral(p["x"], p["y"]),
    )
    t_sfsa_5 = time.perf_counter() - t0
    saved_5 = (1.0 - (t_sfsa_5 / t_base_5)) * 100.0
    results["5. Single Isolated Run (N=1, zero reuse)"] = {
        "baseline_ms": t_base_5 * 1000,
        "sfsa_ms": t_sfsa_5 * 1000,
        "saved_pct": saved_5,
        "speedup": t_base_5 / max(t_sfsa_5, 1e-9),
    }

    # 6. CQE Query Compression Batch (N=1000)
    cqe = QueryCompressionEngine(clustering_radius=0.15)
    batch_1000 = [{"x": float(i % 15) * 0.1 + (i % 3) * 0.02} for i in range(1000)]

    def batch_fn(q):
        s = 0.0
        for i in range(100):
            s += math.sin(q["x"] + i * 0.05)
        return s

    t0 = time.perf_counter()
    for q in batch_1000:
        batch_fn(q)
    t_base_6 = time.perf_counter() - t0

    t0 = time.perf_counter()
    comp_res = cqe.compress_and_solve(batch_1000, batch_fn)
    t_sfsa_6 = time.perf_counter() - t0
    saved_6 = (1.0 - (t_sfsa_6 / t_base_6)) * 100.0
    results["6. CQE Query Compression (N=1000)"] = {
        "baseline_ms": t_base_6 * 1000,
        "sfsa_ms": t_sfsa_6 * 1000,
        "saved_pct": saved_6,
        "speedup": t_base_6 / max(t_sfsa_6, 1e-9),
        "centroids": comp_res.representative_count,
    }

    for name, data in results.items():
        print(f"\n{name}:")
        print(f"  Baseline: {data['baseline_ms']:.2f} ms | SFSA: {data['sfsa_ms']:.2f} ms")
        print(f"  Wall-Clock Reduction: {data['saved_pct']:.2f}% | Speedup: {data['speedup']:.2f}x")
        if "points_evaluated" in data:
            print(f"  Points: {data['points_evaluated']} evaluated, {data['points_skipped']} skipped")
        if "centroids" in data:
            print(f"  Centroids: {data['centroids']} solved vs 1000 full queries")

    print("\n" + "=" * 70)
    return results


if __name__ == "__main__":
    run_all_benchmarks()
