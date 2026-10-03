#!/usr/bin/env bash
# One-line installer for plain "/sfsa" in Claude Code (no manual clone):
#   curl -fsSL https://raw.githubusercontent.com/AlejoMalia/SFSA/main/scripts/install.sh | bash
# Installs SFSA as a standalone skill in ~/.claude/skills/sfsa (bundled library, no pip). Needs git and python3 (3.9+).
# Optional: SFSA_REPO=<git url> to use another source, SFSA_LOCAL=<dir> to use a local checkout, or pass a target dir.
set -euo pipefail
TARGET="${1:-$HOME/.claude/skills/sfsa}"
for tool in git python3; do
  command -v "$tool" >/dev/null || { echo "SFSA install needs '$tool' on PATH" >&2; exit 1; }
done
if [ -n "${SFSA_LOCAL:-}" ]; then
  SRC="$SFSA_LOCAL"
else
  TMP="$(mktemp -d)"
  trap 'rm -rf "$TMP"' EXIT
  git clone --quiet --depth 1 "${SFSA_REPO:-https://github.com/AlejoMalia/SFSA.git}" "$TMP/sfsa"
  SRC="$TMP/sfsa"
fi
bash "$SRC/scripts/install_claude_skill.sh" "$TARGET"
