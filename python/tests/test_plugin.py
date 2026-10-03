"""The Claude plugin: bundled library in sync, valid manifests, a skill with correct frontmatter, runnable recipes."""

import hashlib
import json
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PLUGIN = ROOT / "claude-plugin"


def _digest(folder: Path) -> dict:
    return {str(p.relative_to(folder)): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in sorted(folder.rglob("*.py")) if "__pycache__" not in p.parts}


def test_bundled_library_matches_source():
    assert _digest(PLUGIN / "lib" / "sfsa") == _digest(ROOT / "python" / "sfsa"), "run: python scripts/sync_plugin.py"


def test_generated_reference_files_are_in_sync():
    catalog = json.loads((ROOT / "skills" / "catalog.json").read_text(encoding="utf-8"))
    md = (PLUGIN / "skills" / "sfsa" / "reference" / "skills-catalog.md").read_text(encoding="utf-8")
    assert all(f"`{s['name']}`" in md for s in catalog) and len(catalog) == 85


def test_manifests():
    plugin = json.loads((PLUGIN / ".claude-plugin" / "plugin.json").read_text())
    market = json.loads((ROOT / ".claude-plugin" / "marketplace.json").read_text())
    assert plugin["name"] == "sfsa" and plugin["license"] == "CC-BY-4.0"
    entry = market["plugins"][0]
    assert entry["name"] == plugin["name"] and (ROOT / entry["source"]).resolve() == PLUGIN.resolve()
    assert entry["version"] == plugin["version"]


def test_skill_frontmatter_and_references():
    text = (PLUGIN / "skills" / "sfsa" / "SKILL.md").read_text(encoding="utf-8")
    head = text.split("---")[1]
    assert re.search(r"^name: sfsa$", head, re.M) and "description:" in head
    for ref in re.findall(r"`(reference/[\w.-]+)`", text):
        assert (PLUGIN / "skills" / "sfsa" / ref).exists(), ref
    assert "Numbers come from executed code" in text


def test_runner_and_info_scripts_work_without_installation(tmp_path):
    out = subprocess.run([str(PLUGIN / "bin" / "sfsa-info"), "selftest"], capture_output=True, text=True, check=False)
    assert out.returncode == 0 and "OK" in out.stdout
    code = subprocess.run([str(PLUGIN / "bin" / "sfsa-python"), "-c", "import sfsa; print(sfsa.__file__)"],
                          capture_output=True, text=True, check=False, cwd=tmp_path)
    assert code.returncode == 0 and "claude-plugin" in code.stdout
    d = subprocess.run([str(PLUGIN / "bin" / "sfsa-info"), "describe", "compute"], capture_output=True, text=True, check=False)
    assert json.loads(d.stdout)["required_args"] == ["task_id", "inventory", "solver"]
    assert subprocess.run([str(PLUGIN / "bin" / "sfsa-info"), "describe", "nope"], capture_output=True, check=False).returncode == 1


def test_every_recipe_runs(tmp_path):
    text = (PLUGIN / "skills" / "sfsa" / "reference" / "recipes.md").read_text(encoding="utf-8")
    blocks = re.findall(r"```python\n(.*?)```", text, flags=re.S)
    assert len(blocks) >= 8
    for i, code in enumerate(blocks, 1):
        f = tmp_path / f"recipe{i}.py"
        f.write_text(code)
        r = subprocess.run([str(PLUGIN / "bin" / "sfsa-python"), str(f)], capture_output=True, text=True, check=False)
        assert r.returncode == 0, f"recipe {i} failed:\n{r.stderr}"


def test_standalone_install_gives_a_self_contained_skill(tmp_path):
    target = tmp_path / "skills" / "sfsa"
    r = subprocess.run([str(ROOT / "scripts" / "install_claude_skill.sh"), str(target)], capture_output=True, text=True, check=False)
    assert r.returncode == 0, r.stderr
    assert (target / "SKILL.md").is_file() and (target / "reference" / "recipes.md").is_file()
    assert (target / "lib" / "sfsa" / "__init__.py").is_file()
    out = subprocess.run([str(target / "bin" / "sfsa-info"), "selftest"], capture_output=True, text=True, check=False, cwd=tmp_path)
    assert out.returncode == 0 and "OK" in out.stdout


def test_slash_command_exists_so_plain_sfsa_works_after_plugin_install():
    cmd = (PLUGIN / "commands" / "sfsa.md").read_text(encoding="utf-8")
    head = cmd.split("---")[1]
    assert "description:" in head and "$ARGUMENTS" in cmd and "`sfsa` skill" in cmd
