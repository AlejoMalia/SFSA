#!/usr/bin/env bash
# Installs SFSA as a standalone Claude Code skill, so that plain "/sfsa" works (no plugin namespace).
# Usage: scripts/install_claude_skill.sh [target-dir]      default: ~/.claude/skills/sfsa
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TARGET="${1:-$HOME/.claude/skills/sfsa}"
python3 "$ROOT/scripts/sync_plugin.py" >/dev/null
rm -rf "$TARGET"
mkdir -p "$TARGET"
cp -R "$ROOT/claude-plugin/skills/sfsa/." "$TARGET/"
cp -R "$ROOT/claude-plugin/bin" "$ROOT/claude-plugin/lib" "$TARGET/"
find "$TARGET" -name __pycache__ -type d -prune -exec rm -rf {} +
chmod +x "$TARGET/bin/sfsa-python" "$TARGET/bin/sfsa-info"
"$TARGET/bin/sfsa-info" selftest
echo "Installed at $TARGET. Open a new Claude Code session and type /sfsa"
