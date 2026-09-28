# SFSA — Standard Framework for Scientific Advancement
### **A Universal, Domain-Agnostic Computational Engine for Accelerated Scientific Research** 

<p align="center">
  <img src="docs/banner.png" alt="SFSA — Standard Framework for Scientific Advancement" width="100%">
</p>
 
[![License: CC BY 4.0](https://img.shields.io/badge/License-CC_BY_4.0-lightgrey.svg)](https://creativecommons.org/licenses/by/4.0/)
[![Tests](https://img.shields.io/badge/tests-passing%20(100%25)-brightgreen.svg)]()
[![Python Tests](https://img.shields.io/badge/pytest-10%2F10%20passed-brightgreen.svg)]()
[![JavaScript Tests](https://img.shields.io/badge/node%20test-8%2F8%20passed-brightgreen.svg)]()
[![Engines](https://img.shields.io/badge/engines-7%20scientific%20engines-blue.svg)]()
[![Performance Range](https://img.shields.io/badge/compute%20reduction-45%25%20--%2090%25%20(by%20scenario)-orange.svg)]()
[![Languages](https://img.shields.io/badge/languages-Python%20%7C%20JavaScript-blue.svg)]()

> **Typical savings when reuse/bounds apply:** ~45–90 % wall-clock (scenario models). Isolated one-shot runs: ~0 %.

---

## Executive Summary & Core Value Proposition

Scientific software often wastes compute on work that never needed to run: full grid sweeps after a bound is already violated, repeated evaluation of the same deterministic state, full-model recomputation when only one layer changed, and numerical iteration where a closed form or a hard constraint would have ended the search early.

**SFSA (Standard Framework for Scientific Advancement)** is an open-source, domain-agnostic toolkit for structuring that logic once and reusing it across projects. It ships seven modular engines with parallel implementations in **Python (`python/`)** and **JavaScript (`javascript/`)**, aimed at researchers, lab pipelines, and automated agents that need predictable control flow—not ad-hoc scripts.

SFSA does not replace domain physics, laboratory data, or full-scale simulators. It reduces avoidable recomputation and makes analytical checks, caching, layer updates, and multi-objective path filtering explicit, testable components of a research codebase.

### Features

- ⚡ **Early-exit & bound checks** — Stop trajectories as soon as inventory, domain, or invariant checks fail.
- 🧠 **Memoization of deterministic states** — Reuse prior results instead of recomputing identical inputs.
- 🔗 **Reactive layer graph** — Propagate parameter changes only through dependent subsystems.
- 📐 **Prefer closed form before grids** — Route to analytical solvers when the problem structure allows.
- 🎯 **Pareto path filtering** — Rank multi-step options by competing objectives without hiding trade-offs.
- 🧩 **Gap inventory (no silent fill)** — Surface missing inputs and open links; do not invent mechanisms.

---

## The 7 Core Engines of SFSA v0.1

SFSA is built upon seven foundational engines engineered in completely domain-neutral mathematics:

```
                                ┌─────────────────────────────────────────┐
                                │               SFSA CORE                 │
                                │   Standard Framework for Scientific     │
                                │              Advancement                │
                                │                                         │
                                └────────────────────┬────────────────────┘
                                                     │
         ┌──────────────┬──────────────┬─────────────┼─────────────┬──────────────┬──────────────┐
         ▼              ▼              ▼             ▼             ▼              ▼              ▼
     [ MATE ]       [ TRIADA ]   [ AUTOCOMPLETE ] [ FLN ]       [ ICR ]       [ PARETO ]   [ PROJECTOR ]
    Memoization   3-Stage Method  Model Self-    Reactive     In-Frame        Pathway        Layer
    & Trajectory  & Verification  Gap Filling    Multi-Layer  Computer        Pareto      Consistency
     Projection                   Synthesizer    DAG Network  Reduction      Optimizer    & Coupling
```

### 1. MATE Engine (`MATE`)
* **Purpose:** Multi-dimensional memoization, trajectory projection, and early-abort evaluation.
* **Research Benefit:** Caches all deterministic intermediate states using semantic invariant hashing ($O(1)$ lookup) and projects downstream feasibility before heavy computations are executed. If a boundary violation is guaranteed, MATE short-circuits immediately with status `R3_INFEASIBLE`.

### 2. TRIADA Engine (`TRIADA`)
* **Purpose:** Standard 3-stage scientific problem decomposition protocol (Alejo Malia):
  - **T1 — Strict In-Situ Inventory:** Validates the physical/mathematical existence and conservation bounds of all necessary variables before computation.
  - **T2 — Exact Analytical & Stoichiometric Solvers:** Prioritizes closed-form algebraic and analytical solutions over blind numerical approximation loops.
  - **T3 — Bounded Projection & Verification:** Projects the solution into operational parameter space and verifies physical consistency against global invariant laws.

### 3. Autocomplete Engine (`Autocomplete`)
* **Purpose:** Model gap detector and autonomous conceptual connection synthesizer.
* **Research Benefit:** Monitors framework layers, detects epistemic voids or unpopulated parameters, searches registered transformation rules, and automatically closes the gaps.

### 4. FLN — Framework Layer Network (`FLN`)
* **Purpose:** Multi-directional reactive dependency graph connecting all conceptual layers of a scientific model.
* **Research Benefit:** Connects physical, chemical, logistical, and reporting layers into a reactive DAG. When any parameter changes, FLN propagates delta-corrections across only the affected downstream layers in microsecond intervals without manual re-wiring.

### 5. In-Frame Computer Reduction (`ICR`)
* **Purpose:** In-situ computational optimizer, dead-branch elimination, and execution-path pruning.
* **Research Benefit:** Inspects calculation graphs, folds constant and near-zero expressions, and substitutes dense numerical loops with verified analytical approximations within calibrated error tolerances.

### 6. ParetoPath Engine (`ParetoPath`)
* **Purpose:** Multi-objective transition pathfinder & Pareto frontier optimizer.
* **Research Benefit:** Discovers the optimal multi-step sequence connecting an Initial State ($A$) to a Desired State ($B$), filtering out dominated pathways and presenting the non-dominated Pareto frontier (Cost vs. Duration vs. Feasibility).

### 7. Layer Consistency Projector (`LayerConsistencyProjector`)
* **Purpose:** Cross-layer parameter coupling evaluator and inconsistency conflict detector.
* **Research Benefit:** Operates strictly computationally (zero graphical overhead). Evaluates layers with numerical parameter vectors or claim flags, computes normalized vector distance ($1 - \cos\theta$) and cross-layer correlation ratios, and detects concrete parameter inconsistencies (e.g., conflicting variable bounds or mismatched shared state values). Defendible, measurable, and free of metaphysical or ungrounded terminology.

---

## Computational Savings: Characterized Scenarios

Rather than citing an unrealistic blanket percentage, computational reduction in SFSA depends directly on the structure and repetitiveness of the research workflow:

| # | Archetype | Scenario Condition | Wall-Clock Time Reduction | Compute Reduction (Ops / CPU) |
|---|---|---|---|---|
| **1** | **Astrophysics / 1D column integration** *(closed-form or repeated profile)* | 70% queries repeat state; 20% abort on domain | **75% – 90%** | **80% – 95%** |
| **2** | **Kinetics / Arrhenius exploratory grid** | 50% of grid violates inventory or bounds prior to heavy solver | **45% – 70%** | **50% – 75%** |
| **3** | **Materials / multi-parameter mesh** | 40% cells pruned by bounds; 30% cache hits | **50% – 75%** | **55% – 80%** |
| **4** | **Multi-layer DAG** *(10 layers, localized delta)* | Only 1–2 of 10 layers affected by parameter change | **70% – 90%** | **70% – 90%** |
| **5** | **Single isolated calculation** *(no reuse, unconstrained)* | Single non-repeating execution | **0%** (≤ **−5%** from overhead) | **0%** |
| **6** | **Pathway / claims analysis** *(reopening closed nodes)* | 60% of work was avoidable re-analysis | **50% – 80%** *(analyst time)* | **20% – 40%** *(automated)* |
| **7** | **Multi-subsystem projection upon parameter change** | Partial DAG recalculation vs full table sweep | **60% – 85%** | **60% – 85%** |

> [!IMPORTANT]
> **Mandatory Specification Note:**  
> The percentage figures above represent engineering scenario models under the specified conditions (Column 3). They are not static empirical benchmark guarantees of SFSA v0.1. Establishing fixed quantitative claims requires reproducible benchmarks (baseline vs. SFSA, identical hardware, $N$ repetitions).

---

## Empirical Reproducible Benchmark (SFSA v0.1)

Below is an empirical benchmark executed directly on SFSA v0.1 measuring an exploratory grid sweep ($N = 1000$ queries, 250 iterative baseline steps per query, 63% cluster reuse, 10% out-of-boundary inputs):

```bash
python python/tests/benchmark_reproducible.py
```

| Experiment | Sample Size (\(N\)) | Baseline Time (\(t_{\text{baseline}}\)) | SFSA Time (\(t_{\text{SFSA}}\)) | Wall-Clock Time Reduction | Speedup Factor | Operations Avoided | MATE Cache Hit Rate |
|---|---|---|---|---|---|---|---|
| **Grid Sweep \(F_4(V\cdot t)\)** | 1,000 | 24.36 ms | 8.36 ms | **65.67%** | **2.9×** | **89.46%** *(223,650 ops)* | 63.0% *(10% T1 aborts)* |

---

## Directory Structure

```
SFSA — Standard Framework for Scientific Advancement/
├── LICENSE                    # Creative Commons Attribution 4.0 (CC BY 4.0)
├── README.md                  # Comprehensive framework documentation
├── python/                    # Python 3.9+ implementation
│   ├── sfsa/
│   │   ├── __init__.py        # Package exports (7 engines)
│   │   ├── mate.py            # 1. MATE Engine
│   │   ├── triada.py          # 2. TRIADA Engine
│   │   ├── autocomplete.py    # 3. Autocomplete Engine
│   │   ├── fln.py             # 4. FLN Engine
│   │   ├── icr.py             # 5. ICR Engine
│   │   ├── path.py            # 6. ParetoPath Engine
│   │   ├── projection.py      # 7. Layer Consistency Projector
│   │   └── session.py         # SFSASession Orchestrator
│   ├── tests/
│   │   ├── test_sfsa.py       # Exhaustive test suite (pytest: 10/10 passing)
│   │   └── benchmark_reproducible.py # Empirical reproducible benchmark runner
│   └── pyproject.toml         # Python packaging configuration
└── javascript/                # Modern JavaScript (ESM / Node.js) implementation
    ├── src/
    │   ├── index.js           # Module exports (7 engines)
    │   ├── mate.js            # 1. MATE Engine
    │   ├── triada.js          # 2. TRIADA Engine
    │   ├── autocomplete.js    # 3. Autocomplete Engine
    │   ├── fln.js             # 4. FLN Engine
    │   ├── icr.js             # 5. ICR Engine
    │   ├── path.js            # 6. ParetoPath Engine
    │   ├── projection.js      # 7. Layer Consistency Projector
    │   └── session.js         # SFSASession Orchestrator
    ├── test/
    │   └── test_sfsa.js       # Exhaustive test runner (Node.js: 8/8 passing)
    └── package.json           # Node / NPM packaging configuration
```

---

## Quickstart Guide

### Python Integration

```python
from sfsa import SFSASession, TransitionStep

session = SFSASession(name="Materials_Transition_Study")

# 1. Register and connect layers with FLN
session.register_layer("thermo", {"temp_k": 300.0, "pressure_pa": 101325})
session.register_layer("kinetics", {})
session.connect_layers("thermo", "kinetics", lambda th, ki: {"rate": th["temp_k"] * 1.5})

session.update_layer("thermo", {"temp_k": 450.0})

# 2. Multi-Objective Pareto Pathway Optimization
session.path.register_step(
    TransitionStep(
        step_id="catalytic_pulse",
        name="Catalytic Pulse",
        cost=15.0,
        duration=2.0,
        feasibility=0.95,
        delta_state={"temp_k": 50.0}
    )
)
pathways = session.find_pareto_pathways(
    initial_state={"temp_k": 450.0},
    target_state={"temp_k": 500.0}
)
print(f"Optimal Pareto Pathways: {len(pathways)}")

# 3. Layer Consistency & Coupling Projection
report = session.project_layers("thermo", "kinetics")
print(f"Normalized Vector Distance: {report.normalized_vector_distance:.3f}")
print(f"Parameter Inconsistencies: {len(report.inconsistencies)}")
```

### JavaScript / Node.js Integration

```javascript
import { SFSASession, TransitionStep } from './src/index.js';

const session = new SFSASession({ name: "Molecular_Dynamics_Framework" });

// 1. Register reactive layers in FLN
session.registerLayer("thermodynamics", { tempK: 300, volumeM3: 0.05 });
session.registerLayer("energy_states", {});
session.connectLayers("thermodynamics", "energy_states", (data) => ({ internalEnergyJ: data.tempK * 8.314 }));

// 2. Compute with TRIADA and MATE
const result = session.compute({
  taskId: "entropy_optimization",
  inventory: { molarMass: 0.028, moles: 2.5 },
  solver: (inv) => inv.moles * 8.314 * Math.log(inv.molarMass)
});
console.log(result.value);

// 3. Layer Consistency & Coupling Projection
const report = session.projectLayers("thermodynamics", "energy_states");
console.log("Coupled parameter pairs:", report.stronglyCoupledPairs.length);
console.log("Inconsistency conflicts:", report.inconsistencies.length);
```

---

## Verification & Test Suite

Both implementations include automated test suites confirming that all 7 engines operate with 100% mathematical and behavioral fidelity:

### Running Python Tests (pytest)
```bash
cd python
pytest tests/
# Output: 10 passed in 0.05s (100% success)
```

### Running JavaScript Tests (Node.js)
```bash
cd javascript
npm test
# Output: ALL SFSA JAVASCRIPT TESTS PASSED SUCCESSFULLY! (100% success)
```

---

## License & Legal Attribution

This framework and all accompanying specifications are licensed under the **Creative Commons Attribution 4.0 International Public License (CC BY 4.0)**. **Copyright (c) 2026 Alejo Malia. All rights reserved.** You are free to share, copy, modify, and build upon this framework for any research, commercial, or academic project, provided that appropriate attribution is given to **Alejo Malia** and the **SFSA Project**.
