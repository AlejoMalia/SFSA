# SFSA — Standard Framework for Scientific Advancement
### **A Universal, Domain-Agnostic Computational Engine for Accelerated Scientific Research** 

<p align="center">
  <img src="docs/banner.png" alt="SFSA — Standard Framework for Scientific Advancement" width="100%">
</p>

[![License: CC BY 4.0](https://img.shields.io/badge/License-CC_BY_4.0-lightgrey.svg)](https://creativecommons.org/licenses/by/4.0/)
[![Version](https://img.shields.io/badge/version-0.2.0-blue.svg)]()
[![Tests](https://img.shields.io/badge/tests-137%20passed%20(100%25)-brightgreen.svg)]()
[![Python Tests](https://img.shields.io/badge/pytest-95%2F95%20passed-brightgreen.svg)]()
[![JavaScript Tests](https://img.shields.io/badge/node%20test-42%2F42%20passed-brightgreen.svg)]()
[![Engines](https://img.shields.io/badge/engines-39%20scientific%20engines-blue.svg)]()
[![Skills](https://img.shields.io/badge/skills-85%20executable%20skills-purple.svg)]()
[![Compute Reduction](https://img.shields.io/badge/compute%20reduction-45%25%20--%2098%25%20(by%20scenario)-orange.svg)]()
[![Languages](https://img.shields.io/badge/languages-Python%20%7C%20JavaScript-blue.svg)]()

> **Typical savings when reuse/bounds apply:** ~45–98 % wall-clock (scenario models). **Isolated one-shot runs:** ~0 %.

SFSA does not unilaterally complete 100% of a scientific investigation on its own; rather, it empowers the researcher to reach the solution, decisive data point, or methodological trajectory required to close it much faster—substantially reducing time lost in search, trial-and-error, and redundant recalculation.

---

## Executive Summary & The Next-Generation Vision

Scientific software repeatedly wastes massive compute budgets on work that never needed to be executed:
- Evaluating brute-force parameter grids where gradients are flat.
- Running high-fidelity 3D numerical simulations when a 1D surrogate or closed-form is within tolerance.
- Re-computing deterministic states that were already resolved.
- Iterating hundreds of convergence loops when the uncertainty already guarantees the scientific conclusion.
- Sweeping unviable regions that violate implicit constraints.

**SFSA (Standard Framework for Scientific Advancement)** is an open-source, domain-neutral computational management layer designed for scientists, computational labs, and autonomous AI agents. Rather than merely accelerating an isolated solver, SFSA governs the **entire economy of scientific computation**:

```
                                      SFSA
                                       │
            ┌──────────────────────────┴──────────────────────────┐
            ▼                                                     ▼
 [ORE] Orchestration & Routing Engine              [TXE] Cross-Session Experience
 (Dynamic Minimal Pipeline Composer)               (Surrogates & Constraints Memory)
            │                                                     │
            └──────────────────────────┬──────────────────────────┘
                                       ▼
         ┌─────────────────────────────┼─────────────────────────────┐
         ▼                             ▼                             ▼
   WHAT TO COMPUTE?             HOW TO COMPUTE?                 IS IT NEEDED?
   [VOI] Value of Information   [AMF] Multi-Fidelity           [UAS] Uncertainty Stopping
   [ASG] Adaptive Sampling      [CAE] Constraint Awareness     [VOI] Epistemic Payoff Cut
   [SRA] Sensitivity Reduction  [DIE] Discrepancy Intel        [PKE] Partial Knowledge
   [CQE] Query Compression      [ICR] In-Frame Reduction       [TBE] Temporal Budget
   [PBE] Parallel Batch Dispatch[SYE] Symbolic Simplification  [LSE] Landscape Topology
   [SRE] Schedule & Makespan    [MRE] Model Epistemic Validity [RTE] Robustness Stress-Testing
         │                             │                             │
         └─────────────────────────────┼─────────────────────────────┘
                                       ▼
                       [FLN] Reactive Multi-Layer DAG
                                       │
                      [CPE / MATE / RFE] Provenance & Reuse
                                       │
                    [UQE / UDE] Uncertainty & Dimensional Check
                                       │
                        [TRIADA] Protocol (T1 → T2 → T3)
                                       │
                   [LDR] Laboratory Data Repository & Tables
                                       │
                       [DAE / SME] Assimilation & Surrogates
                                       │
                       [ELE] Closed-Loop Lab-in-the-Loop DoE
                                       │
                       [PROJECTOR & PARETO] Multi-Objective
                                       │
                      [STE / TIL / LKE] Semantic Taxonomy
                                       │
                      [XXE] Explanation & Audit Narrative
                                       │
                      [RME] Cryptographic Reproducibility
```

---

## The 39 Core Engines of SFSA

SFSA is modularized into **39 specialized scientific engines** implemented with complete architectural parity in **Python (`python/`)** and **JavaScript (`javascript/`)**:

### Foundational Engines

| Engine | Name | Role & Core Function |
|---|---|---|
| `MATE` | Multi-Dimensional Acceleration & Trajectory Estimation | Dual-speed operational memory, 6-level reuse (L0–L3), speculative execution battery (`MATE-Spec`), `MechanismCard` learning. |
| `TRIADA` | Scientific Method Protocol (Alejo Malia) | Strict 3-stage solver: T1 (Inventory verification) $\to$ T2 (Analytical closed-form) $\to$ T3 (Invariant check). |
| `Autocomplete` | Model Self-Gap Synthesizer | Epistemic void detector that proposes rule-based layer connections without inventing physics. |
| `FLN` | Framework Layer Network | Reactive dependency DAG propagating parameter deltas across coupled scientific layers. |
| `ICR` | In-Frame Computer Reduction | Constant folding, dead-branch elimination, and analytical loop substitution within calibrated bounds. |
| `ParetoPath` | Transition Optimizer | Multi-objective branch-and-bound optimizer discovering non-dominated transition pathways. |
| `LayerConsistencyProjector` | Layer Consistency Projector | Cross-layer vector distance ($1 - \cos\theta$), parameter coupling ratios, and concrete boundary inconsistency checks. |

### Computational Decision & Efficiency Engines

| Engine | Name | Role & Core Function |
|---|---|---|
| `AMF` | Adaptive Multi-Fidelity Engine | Dynamic evaluation routing between cheap surrogates, intermediate simulations, and dense solvers. |
| `ASG` | Adaptive Sampling & Experimentation | Slashes exploratory grids ($100^3$) by sampling only where information density, sensitivity, or uncertainty vary. |
| `SRA` | Sensitivity & Reduction Analyzer | Identifies active subspaces via Sobol/OAT sensitivity indices, reducing dimensionality and pruning FLN branches. |
| `UAS` | Uncertainty-Aware Stopping | Terminates iterative solvers early when residual uncertainty cannot alter the qualitative scientific conclusion. |
| `CPE` | Computational Provenance & Reuse Engine | Lineage tracking, mathematical premise auditing, and certified approximate reuse. |

### Advanced Mathematical & Execution Engines

| Engine | Name | Role & Core Function |
|---|---|---|
| `CAE` | Constraint Awareness Engine | Propagates hard/soft constraints and infers implicit infeasibility cutting planes from failure clusters. |
| `DIE` | Discrepancy Intelligence Engine | Diagnoses why multi-model pathways diverge (noise vs. modeling assumption vs. regime breakdown) & arbitrates. |
| `TBE` | Temporal Budget Engine | Dynamic wall-clock time-slice allocation between early exploratory sweeps and precision refinement. |
| `PKE` | Partial Knowledge Engine | Harvests and caches intermediate residuals, states, and bounds from interrupted or aborted solver runs. |
| `LSE` | Landscape Structure Engine | Fast response surface topography mapping (plateaus, steep valleys, discontinuities) via sparse stencils. |
| `RFE` | Result Forgetting Engine | Cost-weighted cache eviction and hygiene removing low-utility, high-drift, or trivial entries. |
| `AIE` | Assumption Integrity Engine | Continuous auditing of physical premises (e.g. laminar flow, dilute limit), flagging regime transitions. |
| `CQE` | Query Compression Engine | Clusters high-throughput query streams into representative centroids, evaluating and interpolating. |

### Thematic, Knowledge & Living Taxonomy Engines

| Engine | Name | Role & Core Function |
|---|---|---|
| `STE` | Scientific Thematic Engine | Disciplinary coverage mapping (%), blind spot detection, and methodological gap identification. |
| `LKE` | Literature & Knowledge Engine | Connects model themes with typed repositories (arXiv, ChemRxiv, NIST, Materials Project, Zenodo) to emit proposals. |
| `TIL` | Tag Index & Linking Engine | Constructs and updates an operational living taxonomy of typed scientific tags (`domain`, `method`, `variable`, `regime`). |

### Extended Verification, Acceleration & Data Projection Engines

| Engine | Name | Role & Core Function |
|---|---|---|
| `UQE` | Uncertainty Propagation Engine | Analytical first-order error propagation and interval arithmetic across DAG layers without Monte Carlo overhead. |
| `UDE` | Unit & Dimensional Analysis Engine | Formal dimensional homogeneity verifier tracking SI base exponents $[M, L, T, \Theta, N, I, J]$ in $O(1)$. |
| `SME` | Surrogate Modeling Engine | Automated response surface fitting (RBF / IDW) generating lightweight proxy models for AMF routing. |
| `DAE` | Data Assimilation Engine | Calibrates unknown parameters against laboratory observations via bounded coordinate optimization. |
| `SYE` | Symbolic Equivalence Engine | Algebraic identity simplification ($0 \times x \to 0, \log(\exp(x)) \to x$) and singularity pole detection. |
| `PBE` | Parallel Batch Dispatch Engine | Concurrent workload dispatcher scaling query batches and sampling campaigns across multi-core CPUs. |
| `RTE` | Robustness Testing Engine | Adversarial perturbation tester evaluating numerical condition numbers and detecting bifurcation instabilities. |
| `RME` | Reproducibility Manifest Engine | Cryptographic SHA-256 certificate recording platform, IEEE-754 precision, and module signatures. |
| `LDR` | Laboratory Data Repository | Synthesizes multidimensional reference datasets from runs, enabling table interpolation. |

### Meta-Orchestration, Progress & Experimental Engines

| Engine | Name | Role & Core Function |
|---|---|---|
| `ORE` | Orchestration & Routing Engine | Central meta-brain dynamically composing minimal sufficient engine pipelines based on query archetypes. |
| `VOI` | Value-of-Information Decision Engine | Quantifies marginal expected epistemic gain vs. compute cost, cutting low-return evaluations. |
| `TXE` | Transfer Experience Engine | Cross-session memory transferring constraints (CAE), surrogates (SME), and active subspaces (SRA) to warm-start runs. |
| `ELE` | Experiment Loop Engine | Lab-in-the-Loop closing the cycle: Theory $\to$ DoE $\to$ Measurement $\to$ Assimilation (DAE) $\to$ LDR Repository. |
| `MRE` | Model Risk & Validity Engine | Epistemic validity envelope and physical limit auditor issuing binding safety recommendations. |
| `XXE` | Explanation & Audit Engine | Generates publication-grade audit narratives explaining computational decisions and bound cuts. |
| `SRE` | Schedule & Resource Engine | Hardware-aware queue scheduler prioritizing tasks by VOI/cost ratio and applying backpressure throttling. |

---

## The 85-Skills Catalog

SFSA exposes an executable API of **85 standardized scientific skills**, categorized into 13 functional modules for humans and AI agents:

| Module | Skills (#) | Representative Skills | Function |
|---|---|---|---|
| **Orchestration** | 1–7 | `create_session`, `load_session`, `save_session`, `reset_session`, `get_session_status`, `set_budget`, `set_policy` | Session lifecycle & resource bounds |
| **Reactive Graph (FLN)** | 8–15 | `register_layer`, `update_layer`, `connect_layers`, `disconnect_layers`, `inspect_graph`, `get_layer_state`, `propagate_delta`, `find_affected_layers` | DAG synchronization & state management |
| **Scientific Method (TRIADA)** | 16–21 | `inventory_check`, `try_closed_form`, `bounded_verify`, `run_triada`, `declare_invariants`, `check_invariants` | 3-stage validation & physical laws |
| **Memoization & Pruning (MATE/ICR)** | 22–29 | `compute`, `query_cache`, `store_result`, `invalidate_cache`, `project_trajectory`, `early_abort_check`, `reduce_expression`, `estimate_compute_cost` | Caching, early abort, constant folding |
| **Consistency & Pareto** | 30–35 | `check_consistency`, `project_layers`, `register_transition_step`, `find_pareto_paths`, `rank_pathways`, `compare_states` | Multi-objective paths & cross-layer checks |
| **Fidelity & Sampling (AMF/ASG/UAS)** | 36–43 | `choose_fidelity`, `compute_multi_fidelity`, `suggest_samples`, `run_adaptive_sampling`, `should_stop`, `value_of_information`, `warm_start`, `build_surrogate` | Adaptive compute & intelligent early-exit |
| **Sensitivity & Cuts (SRA/CAE/PKE/LSE)** | 44–50 | `analyze_sensitivity`, `reduce_dimensions`, `infer_constraints`, `apply_constraints`, `extract_partial_knowledge`, `reuse_approximate`, `map_landscape` | Active subspace & implicit cutting planes |
| **Provenance & Hygiene (CPE/RFE)** | 51–55 | `get_provenance`, `assess_reuse`, `forget_results`, `version_model`, `diff_model_versions` | Result lineage & cache lifecycle |
| **Thematic Awareness (STE)** | 56–60 | `analyze_themes`, `get_theme_coverage`, `detect_theme_gaps`, `suggest_related_themes`, `explain_model_focus` | Model self-knowledge & domain % map |
| **External Literature (LKE)** | 61–66 | `search_literature`, `search_datasets`, `search_reference_code`, `rank_external_sources`, `propose_external_evidence`, `link_evidence_to_gap` | Typed repository search & proposals |
| **Assumptions & Auditing (AIE)** | 67–73 | `detect_gaps`, `suggest_gap_closure`, `list_assumptions`, `check_assumption_integrity`, `explain_decision`, `explain_result`, `audit_run` | Premise auditing & verifiable explanations |
| **Reporting & Export** | 74–79 | `compare_runs`, `generate_report`, `export_graph`, `export_cache_manifest`, `export_thematic_map`, `export_skill_trace` | Scientific reports & manifests |
| **Agent Planning** | 80–85 | `plan_computation`, `select_next_action`, `dry_run`, `validate_skill_call`, `batch_queries`, `prioritize_queries` | Automated agent action scheduling |

---

## Computational Savings: Characterized Scenarios

| Archetype | Scenario Condition | Wall-Clock Time Reduction | Compute Reduction (Ops / CPU) |
|---|---|---|---|
| **Astrophysics / 1D column integration** | 70% queries repeat state; 20% abort on domain | **75% – 90%** | **80% – 95%** |
| **Kinetics / Arrhenius exploratory grid** | 50% of grid violates inventory or bounds prior to heavy solver | **45% – 70%** | **50% – 75%** |
| **Materials / multi-parameter mesh** | 40% cells pruned by bounds; 30% cache hits | **50% – 75%** | **55% – 80%** |
| **Multi-layer DAG (10 layers, localized delta)** | Only 1–2 of 10 layers affected by parameter change | **70% – 90%** | **70% – 90%** |
| **Single isolated calculation** | Single non-repeating execution | **0%** (≤ **−5%** overhead) | **0%** |
| **Adaptive Sampling vs. Full Grid Sweep** | Evaluates only high-information subregions | **60% – 85%** | **65% – 90%** |
| **Multi-Fidelity Surrogate Routing** | 80% of queries resolved by low-cost approximation | **70% – 92%** | **75% – 95%** |
| **MATE Ampliado (Multilevel + Speculative Battery)** | 6-level reuse (L0–L3 hits), learned shortcuts & background `MechanismCards` | **85% – 95%** | **90% – 98%** |

> [!IMPORTANT]
> **Mandatory Specification Note:**  
> The percentage figures in the table above represent engineering scenario models under the specified conditions (Column 2). They are not static blanket guarantees across all possible tasks. Below are real empirical benchmarks measured directly on hardware.

---

## Empirical Hardware Benchmarks (Darwin ARM64)

### MATE Ampliado & Speculative Battery Benchmarks (`benchmark_mate_ampliado.py`)

Empirical verification of MATE Ampliado across a 120-query scientific campaign with background speculative mechanism discovery:

| Empirical Experiment | Workload Specification | Baseline Time | MATE Ampliado Time | Wall-Clock Time Reduction | Speedup Factor | Mechanism Highlight |
|---|---|---|---|---|---|---|
| **MATE Ampliado Campaign** | 120 reacting flow queries, L0–L3 reuse + MATE-Spec battery | 37.41 ms | 3.76 ms | **90.00%** | **9.96×** | 96.7% low-latency reuse (L0/L1/L3); 72.4× speculative ROI |

- **Reuse Hierarchy Distribution:** L0 (Exact Zero-Compute): **20.8%** \| L1 (Approximate Neighbor): **25.0%** \| L3 (Shortcut / `MechanismCard`): **50.8%** \| L5 (Full Recompute Baseline): **3.3%**. Total low-latency reuse: **96.7%**.
- **Speculative Battery ROI:** 0.25 ms background speculation yielded 18.06 ms future computational savings (**72.4× compute return on investment**).
- **Methodological Automation:** 12 alternative method evaluations automated, 1 divergent model archived to negative knowledge, 2 production `MechanismCards` promoted.

### Individual Engine Benchmarks (`benchmark_all_scenarios.py`)

| Empirical Experiment | Workload Specification | Baseline Time | SFSA Time | Wall-Clock Time Reduction | Speedup Factor | Mechanism Highlight |
|---|---|---|---|---|---|---|
| **MATE Cache & Invariants** | $N = 1000$ integral queries, 25 cluster keys | 52.65 ms | 10.01 ms | **80.99%** | **5.26×** | Semantic invariant lookup ($O(1)$) |
| **AMF Multi-Fidelity Routing** | $N = 500$, 80% cheap solvable ($tol \le 0.05$) | 19.78 ms | 5.45 ms | **72.44%** | **3.63×** | Cheap surrogate uncertainty gating |
| **UAS Uncertainty Early Stopping** | 20 non-linear PDE loops (200 max iters) | 36.29 ms | 0.78 ms | **97.84%** | **46.32×** | Early termination on residual invariant |
| **CQE Query Compression** | $N = 1000$ stream clustered into centroids | 13.40 ms | 3.79 ms | **71.68%** | **3.53×** | 8 centroids evaluated vs 1000 full solves |
| **ASG Adaptive Grid Pruning** | 2500 dense parameter candidate points | 2500 evals | 59 evals | **97.64%** *(ops)* | **42.3×** | High-utility acquisition filtering |
| **Single Isolated Calculation** | $N = 1$, non-repeating state | 0.05 ms | 0.11 ms | **0.0%** *(−92% overhead)*| **0.52×** | Demonstrates ~0% savings on 1-shot runs |

### Multi-Engine & Triad Pipeline Benchmarks (`benchmark_engine_triads.py`)

Empirical results measuring real multi-engine pipelines working in concert:

| Triad Pipeline | Chained Engines | Workload Specification | Baseline Time | Triad Time | Time Reduction | Speedup | Value Added & Highlights |
|---|---|---|---|---|---|---|---|
| **Triad 1** | `ASG` + `AMF` + `MATE` | 400-point 2D exploratory simulation sweep | 55.47 ms | 13.25 ms | **76.1%** | **4.19×** | 351/400 points pruned by ASG; 49 heavy solves |
| **Triad 2** | `TRIADA` + `UDE` + `UQE` | Physical kinetic energy with uncertainty vs. 10k Monte Carlo | 14.02 ms | 0.15 ms | **98.9%** | **92.36×** | UDE unit homogeneity + 1-pass analytical uncertainty |
| **Triad 3** | `SRA` + `CAE` + `ICR` | 500-candidate 5D parameter optimization under constraints | 4.89 ms | 0.37 ms | **92.4%** | **13.08×** | 2 insensitive dims pruned; 49 unviable points cut prior to solve |
| **Triad 4** | `CQE` + `PBE` + `LDR` | 800 PDE queries compressed, parallelized & projected | 10.53 ms | 6.47 ms | **38.5%** | **1.63×** | Centroid compression + multi-core batch + full LDR table |
| **Triad 5** | `DAE` + `SME` + `RTE` | Empirical parameter assimilation -> surrogate -> stability audit | 15.00 ms | 0.34 ms | **97.7%** | **44.10×** | Fast calibration ($R^2=1.0$) + surrogate + condition audit |

---

## Use SFSA with Claude (plugin)

SFSA ships as a Claude Code plugin: the library, the operating instructions and tested recipes are bundled, so nobody has to clone the repository, run `pip install` or tell Claude to "read SFSA".

```
/plugin marketplace add AlejoMalia/SFSA
/plugin install sfsa@sfsa-marketplace
```

Two ways to use it:

- **Plugin** (above): the skill is invoked as `/sfsa:sfsa` followed by the task (plugin skills carry the plugin name; the short `/sfsa` is not available from a plugin), or just describe the scientific task and Claude loads it on its own.
- **Plain `/sfsa`**, one command, no manual clone (needs `git` and `python3`):
  ```
  curl -fsSL https://raw.githubusercontent.com/AlejoMalia/SFSA/main/scripts/install.sh | bash
  ```
  It installs the same skill, with the library bundled, into `~/.claude/skills/sfsa`; open a new Claude Code session and type `/sfsa audit the units of E = 1/2 m v^2`.

Claude loads the SFSA instructions, writes a short script, runs it through the bundled `bin/sfsa-python` (Python 3.9+, no packages) and reports the result with its method, uncertainty and limits.

What this is: operating instructions plus tools, loaded when needed. It is not training, and Claude does not "remember" SFSA between sessions; the skill loads again each time. The model of the system (the physics) always comes from the user: SFSA accelerates, audits and documents the computation around it. Details: [`claude-plugin/README.md`](claude-plugin/README.md). The bundled copy of `python/sfsa` is regenerated with `python scripts/sync_plugin.py`, and a test fails if it drifts.

---

## Quickstart Guide

### Python Integration

```python
from sfsa import SFSASession, FidelityLevel

session = SFSASession(name="Atmospheric_Chemistry_Framework")

# 1. Multi-Fidelity Computation (AMF)
decision = session.amf.evaluate(
    task_id="rate_constant",
    inputs={"temp_k": 300.0, "pressure_bar": 1.0},
    cheap_solver=lambda inp: (inp["temp_k"] * 1.8e-3, 0.02), # 2% uncertainty
    expensive_solver=lambda inp: inp["temp_k"] * 1.82e-3,
    tolerance=0.05
)
print(f"AMF Level: {decision.selected_level} | Savings: {decision.compute_saved_ratio:.1%}")

# 2. Sensitivity Reduction (SRA)
dim_red = session.sra.reduce_parameter_space(
    base_inputs={"T": 300.0, "P": 1.0, "inert_gas": 0.001},
    objective_fn=lambda p: p["T"] * 2.5 + p["P"] * 0.8 + p["inert_gas"] * 0.0001
)
print(f"Dimensionality: {dim_red.original_dimension}D -> {dim_red.reduced_dimension}D (Retained: {dim_red.retained_parameters})")

# 3. Model Thematic Self-Awareness (STE) & Literature (LKE)
session.register_layer("thermodynamics", {"temp_k": 300.0, "pressure_pa": 101325})
thematic_report = session.analyze_themes()
print(f"Primary Domain Focus: {thematic_report.primary_themes}")

literature = session.search_literature(limit=3)
print(f"External Sources Recommended: {len(literature)}")

# 4. Executing Skills Uniformly (85 Skills)
report = session.execute_skill("generate_report")
print(f"Active SFSA Engines: {report.active_engines_count}")
```

> **Approximate reuse is opt-in.** `session.compute(...)` returns exact cache hits only. To accept a nearby previous result, pass `approximate_reuse_tolerance=0.01` (JS: `approximateReuseTolerance`); it is only applied to results of the current model version.

### JavaScript / Node.js Integration

```javascript
import { SFSASession, FidelityLevel } from './src/index.js';

const session = new SFSASession({ name: "Molecular_Dynamics_Framework" });

// 1. Adaptive Multi-Fidelity Evaluation (AMF)
const decision = session.amf.evaluate({
  taskId: "solvation_energy",
  inputs: { tempK: 298.15 },
  cheapSolver: (inp) => ({ value: inp.tempK * 0.042, uncertainty: 0.015 }),
  expensiveSolver: (inp) => inp.tempK * 0.0423,
  tolerance: 0.05
});
console.log(`AMF Level: ${decision.selectedLevel} | Compute Saved: ${(decision.computeSavedRatio * 100).toFixed(1)}%`);

// 2. Execute via Skills Catalog (Skill 44: Sensitivity Analysis)
const sens = session.executeSkill("analyze_sensitivity", {
  baseInputs: { temp: 300, traceGas: 0.005 },
  objectiveFn: (p) => p.temp * 4.0 + p.traceGas * 0.01
});
console.log(`Most Impactful Parameter: ${sens[0].parameterName}`);
```

---

## Empirical Verification & Multi-Regime Stress Benchmark

To rigorously stress-test and empirically validate the dual-speed operational memory and speculative mechanism battery (`MATE Ampliado`), an exhaustive multi-regime empirical benchmark (`python/tests/benchmark_mate_ampliado.py`) was executed across 3 distinct operational regimes (120 scientific evaluations each on Darwin ARM64 hardware):

| Operational Regime | Workload Characteristics | Baseline Wall-Clock | MATE Ampliado | Net Speedup | Wall-Clock Saved | Low-Lat. Reuse (L0–L3) | Speculative Battery ROI |
|---|---|---|---|---|---|---|---|
| **1. Structured Sweep** | Clustered parameter sweeps, exact repeats, tight perturbations ($\pm 0.4\%$) | $38.5\text{ ms}$ | $7.4\text{ ms}$ | **$5.19\times$** | **$80.7\%$** | $97.5\%$ | **$114.0\times$** |
| **2. Semi-Random Space** | Wide parameter leaps ($\pm 6\%$), dispersed exploration, novel domains | $41.0\text{ ms}$ | $9.4\text{ ms}$ | **$4.39\times$** | **$77.2\%$** | $97.5\%$ | **$178.9\times$** |
| **3. Heavy Dense Solver** | High-cost non-linear integration / stiff 3D grid ($45,000$ steps, $\sim 16.5\text{ ms/eval}$) | $1,984.6\text{ ms}$ | $60.4\text{ ms}$ | **$32.84\times$** | **$97.0\%$** | $97.5\%$ | **$114.0\times$** |

### Four Dimensions of Empirical Verification:
1. **Reuse Distribution (L0–L5):**
   - *Structured:* L0 (Exact): $17.5\%$, L1 (Approximate): $20.0\%$, L3 (Shortcuts): $60.0\%$, L5 (Full compute): $2.5\%$.
   - *Semi-Random:* L0: $3.3\%$, L1: $0.0\%$, L3: $94.2\%$, L5: $2.5\%$ (shortcuts adaptively generalize to wide parameter steps).
   - *Heavy Solver:* L0: $17.5\%$, L1: $20.0\%$, L3: $60.0\%$, L5: $2.5\%$.
2. **Speculative Battery ROI:**
   - Background mechanism exploration consumes only a tiny budgeted slice ($< 0.25\text{ ms}$ in light models, $9.9\text{ ms}$ in heavy models).
   - Compute saved by discovered `MechanismCards` yields **$114\times$ to $178.9\times$ ROI** ($\text{ROI} \gg 1$).
3. **Net Campaign Speedup:**
   - In heavy computational regimes, campaign wall-clock time drops from **$1,984.6\text{ ms}$ to $60.4\text{ ms}$** (**$32.84\times$ net speedup, $97.0\%$ reduction**).
4. **Autonomous Policy Governance:**
   - High-fidelity shortcuts are automatically promoted to `TRUSTED` status once verified ($3+$ confirmations with zero tolerance breaches).
   - Divergent candidate models are quarantined into `negative_knowledge` to eliminate recurring exploratory waste.

---

## Verification & Test Suite

Both implementations ship automated suites covering all **39 engines** and **85 skills**. Every skill is executed with realistic arguments and its *behaviour* is asserted (a skill that degrades to a no-op stub fails the suite), plus regression tests for the core-engine defects fixed in the v0.2 diagnosis (ICR zero-pruning, cyclic FLN graphs, atomic layer updates, fail-closed constraint/assumption rules, RTE singularities, RME seal coverage).

### Running Python Tests
```bash
cd python && python3 -m pytest -q
# 95 passed
```

### Running JavaScript Tests (Node.js)
```bash
cd javascript && npm test          # runs every suite file
node --test javascript/test/*.js   # or via the Node test runner (42 passed)
```

### Notes on cross-language parity
Python and JavaScript share the skills catalog (`skills/catalog.json`, bundled copy in `python/sfsa/catalog.json` and `javascript/src/catalog.json`; a test fails if they drift) and the same skill semantics. Some lower-level engines are simpler in JavaScript than in Python (for example TBE strategy selection); the skill-level behaviour is what is held identical.

---

## License & Legal Attribution

This framework and all accompanying specifications are licensed under the **Creative Commons Attribution 4.0 International Public License (CC BY 4.0)**.

**Copyright (c) 2026 Alejo Malia. All rights reserved.**

You are free to share, copy, modify, and build upon this framework for any research, commercial, or academic project, provided that appropriate attribution is given to **Alejo Malia** and the **SFSA Project**.
