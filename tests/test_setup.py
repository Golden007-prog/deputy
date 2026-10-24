import json
from pathlib import Path

import pytest

from deputy import setup


@pytest.fixture
def home(tmp_path: Path, monkeypatch) -> Path:
    root = tmp_path / "home"
    root.mkdir()
    monkeypatch.setenv("HOME", str(root))
    monkeypatch.setenv("USERPROFILE", str(root))
    monkeypatch.setenv("CODEX_HOME", str(root / ".codex"))
    monkeypatch.setattr(Path, "home", classmethod(lambda cls: root))
    return root


def test_cursor_global_merges_and_keeps_other_servers(home: Path):
    config = home / ".cursor" / "mcp.json"
    config.parent.mkdir()
    config.write_text(json.dumps({"mcpServers": {"other": {"command": "x"}}}), encoding="utf-8")
    notes = setup.setup_cursor()
    data = json.loads(config.read_text(encoding="utf-8"))
    assert set(data["mcpServers"]) == {"other", "deputy"}
    entry = data["mcpServers"]["deputy"]
    assert entry["command"] == "uvx" and entry["args"][-2:] == ["deputy", "serve"]
    assert entry["env"]["DEEPINFRA_API_KEY"] == "${env:DEEPINFRA_API_KEY}"
    assert "DEPUTY_WORKSPACE" not in entry["env"]  # global config: rely on MCP roots
    assert (config.parent / "mcp.json.deputy-backup").exists()
    assert any("no global rules file" in n for n in notes)
    # Running again keeps the existing entry instead of overwriting it.
    assert any("kept the existing deputy entry" in n for n in setup.setup_cursor())


def test_cursor_project_writes_config_and_rule(home: Path, tmp_path: Path):
    project = tmp_path / "app"
    project.mkdir()
    setup.setup_cursor(project, mode="balanced", pypi=True)
    entry = json.loads((project / ".cursor" / "mcp.json").read_text(encoding="utf-8"))["mcpServers"]["deputy"]
    assert entry["args"] == ["deputy-cc", "serve"]
    assert entry["env"]["DEPUTY_WORKSPACE"] == "${workspaceFolder}"
    assert entry["env"]["DEPUTY_MODE"] == "balanced"
    rule = (project / ".cursor" / "rules" / "deputy.mdc").read_text(encoding="utf-8")
    assert rule.startswith("---\ndescription:") and "low-risk mechanical work" in rule


def test_cursor_refuses_to_overwrite_broken_json(home: Path):
    config = home / ".cursor" / "mcp.json"
    config.parent.mkdir()
    config.write_text("{ not json", encoding="utf-8")
    with pytest.raises(setup.SetupError, match="not valid JSON"):
        setup.setup_cursor()
    assert config.read_text(encoding="utf-8") == "{ not json"


def test_codex_appends_block_and_installs_skill(home: Path):
    config = home / ".codex" / "config.toml"
    config.parent.mkdir()
    config.write_text('model = "gpt-5"\n', encoding="utf-8")
    setup.setup_codex()
    text = config.read_text(encoding="utf-8")
    assert text.startswith('model = "gpt-5"\n')
    assert "[mcp_servers.deputy]" in text and "tool_timeout_sec = 1800" in text
    assert '"DEEPINFRA_API_KEY"' in text and 'DEPUTY_MODE = "accuracy"' in text
    skill = home / ".agents" / "skills" / "deputy" / "SKILL.md"
    assert skill.read_text(encoding="utf-8").startswith("---\nname: deputy\n")
    setup.setup_codex()  # idempotent
    assert config.read_text(encoding="utf-8").count("[mcp_servers.deputy]") == 1


def test_dry_run_writes_nothing(home: Path):
    notes = setup.setup_codex(dry_run=True) + setup.setup_cursor(dry_run=True)
    assert not (home / ".codex").exists() and not (home / ".cursor").exists()
    assert any("would append" in n for n in notes) and any("would write" in n for n in notes)


def test_rules_reflect_the_mode():
    assert "only when the user explicitly asks" in setup.agent_rules("accuracy")
    assert "well-specified coding work" in setup.agent_rules("savings")
    with pytest.raises(setup.SetupError):
        setup.agent_rules("yolo")
