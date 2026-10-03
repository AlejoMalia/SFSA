# SFSA for Claude (plugin)

Installs SFSA as Claude's scientific-computation engine. Nothing to clone, nothing to `pip install`: the library is bundled and run through `bin/sfsa-python`.

```
/plugin marketplace add AlejoMalia/SFSA
/plugin install sfsa@sfsa-marketplace
```
Then type `/sfsa:sfsa` followed by your task, e.g. `/sfsa:sfsa audit the units of E = 1/2 m v^2`, or describe the scientific task and the skill triggers on its own. Requires Python 3.9+; no packages.

For the short `/sfsa`, install it as a standalone skill with one command: `curl -fsSL https://raw.githubusercontent.com/AlejoMalia/SFSA/main/scripts/install.sh | bash`.

Contents: `skills/sfsa/SKILL.md` (operating instructions), `skills/sfsa/reference/` (tested recipes, engine and skill lists), `bin/sfsa-python` and `bin/sfsa-info`, `lib/sfsa` (bundled copy of `python/sfsa`, regenerated with `python scripts/sync_plugin.py`).
