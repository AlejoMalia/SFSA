# SFSA — Standardized Scientific Skills Catalog (85 Skills)

This directory serves as the **Single Source of Truth (SSOT)** for all 85 standardized scientific skills of the **Standard Framework for Scientific Advancement (SFSA)**.

Both the **Python runtime (`python/sfsa/skills.py`)** and the **JavaScript / ESM runtime (`javascript/src/skills.js`)** dynamically ingest [`catalog.json`](./catalog.json). Autonomous AI coding agents (Antigravity, Claude Code, Cursor, AutoGen) can also inspect this catalog directly to discover, plan, and execute domain-agnostic scientific operations.

---

## Skill Architecture

Every skill is a declarative specification:
```json
{
  "skill_number": 22,
  "name": "compute",
  "category": "MATE_ICR",
  "description": "Executes computation with memoization & early-abort",
  "target_engine": "session",
  "target_method": "compute"
}
```

### Functional Modules (13 Categories)

| # | Category | Skill Range | Core Scope |
|---|---|---|---|
| 1 | **Orchestration** | 1 – 7 | Session initialization, persistence, budgets (`TBE`), global policies |
| 2 | **FLN** | 8 – 15 | Reactive dependency DAG, layer registration, delta propagation |
| 3 | **TRIADA** | 16 – 21 | 3-stage validation (T1 Inventory, T2 Analytical, T3 Verification), physical invariants |
| 4 | **MATE_ICR** | 22 – 29 | Memoization, trajectory bounds, early-abort, loop pruning, cost estimation |
| 5 | **Projector_Pareto** | 30 – 35 | Cross-layer consistency checks, coupling ratios, multi-objective Pareto paths |
| 6 | **Fidelity_Sampling** | 36 – 43 | Multi-fidelity routing (`AMF`), adaptive sampling (`ASG`), uncertainty stopping (`UAS`) |
| 7 | **Sensitivity_Constraints** | 44 – 50 | OAT/Sobol sensitivity (`SRA`), implicit domain cuts (`CAE`), partial knowledge (`PKE`) |
| 8 | **Provenance_Cache** | 51 – 55 | Lineage records (`CPE`), approximate reuse, cost-weighted cache eviction (`RFE`) |
| 9 | **Thematic_STE** | 56 – 60 | Disciplinary composition %, thematic gap detection, model self-awareness (`STE`) |
| 10 | **Literature_LKE** | 61 – 66 | Preprints, datasets, reference code proposals (`LKE`) linked to model gaps |
| 11 | **Gaps_Assumptions** | 67 – 73 | Epistemic void detection (`Autocomplete`), regime premise auditing (`AIE`) |
| 12 | **Reporting** | 74 – 79 | Cross-run comparison, markdown summaries, DAG/trace exports |
| 13 | **Agent_Planning** | 80 – 85 | AI agent step scheduling, query clustering (`CQE`), dry-runs, prioritization |

---

## Universal Execution

### In Python
```python
from sfsa import SFSASession

session = SFSASession()
# Execute by skill name or skill number
session.execute_skill("register_layer", layer_id="atmosphere", initial_state={"pressure_bar": 1.0})
session.execute_skill(22, task_id="flux_calc", inventory={"T": 300}, solver=my_solver)
```

### In JavaScript
```javascript
import { SFSASession } from 'sfsa';

const session = new SFSASession();
session.executeSkill("register_layer", { layerId: "atmosphere", initialState: { pressure_bar: 1.0 } });
session.executeSkill(22, { taskId: "flux_calc", inventory: { T: 300 }, solver: mySolver });
```
