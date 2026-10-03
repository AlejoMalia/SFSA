---
description: Use SFSA as the scientific-computation engine for the task that follows (units audit, equivalence, caching, multi-fidelity, sampling, sensitivity, discrepancies, reproducible report)
argument-hint: "[scientific task, e.g. audit the units of E = 1/2 m v^2]"
---

Activate SFSA for this session and work as its operator.

1. Load and follow the `sfsa` skill (its rules, workflow, engine table and reporting template). SFSA is bundled with this plugin: do not ask the user to clone anything, install anything or "read the repo".
2. Run `selftest` through the bundled `bin/sfsa-info` once to confirm the library runs, and tell the user in one line that SFSA is active.
3. If the user gave a task below, start on it now: frame it, audit units, pick the engines, write a short script, run it with the bundled `bin/sfsa-python`, and report with method, uncertainty and limits. If no task was given, ask what they want to compute, check, speed up or design, and list the five most useful capabilities in one line each.

Task: $ARGUMENTS
