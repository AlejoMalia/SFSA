# SFSA for Claude (plugin)

Installs SFSA as Claude's scientific-computation engine. Nothing to clone, nothing to `pip install`: the library is bundled and run through `bin/sfsa-python`.

```
/plugin marketplace add AlejoMalia/SFSA
/plugin install sfsa@sfsa-marketplace
```
Then type `/sfsa` followed by your task, e.g. `/sfsa audit the units of E = 1/2 m v^2` (if another plugin defines the same command name, use `/sfsa:sfsa`). The skill also triggers on its own for scientific-computation requests. Requires Python 3.9+; no packages.

Alternative for people who have a clone: `scripts/install_claude_skill.sh` installs it as a standalone skill in `~/.claude/skills/sfsa`.

Contents: `skills/sfsa/SKILL.md` (operating instructions), `skills/sfsa/reference/` (tested recipes, engine and skill lists), `bin/sfsa-python` and `bin/sfsa-info`, `lib/sfsa` (bundled copy of `python/sfsa`, regenerated with `python scripts/sync_plugin.py`).
