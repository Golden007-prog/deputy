from pathlib import Path

import pytest

from deputy.agent import CONSULT_HEADER, DeputyError, build_request, consult, run_agent
from deputy.config import load_settings

from conftest import FakeClient, reply, tool_call


def test_code_run_edits_files_and_reports(project: Path, settings):
    client = FakeClient([
        reply(calls=[tool_call("read_file", {"path": "app.py"})], reasoning="look first"),
        reply(calls=[tool_call("edit_file", {"path": "app.py", "old_text": "a - b",
                                             "new_text": "a + b"}, "call_2")], reasoning="fix it"),
        reply("RESULT: done\nSUMMARY: fixed add."),
    ])
    result = run_agent("Fix add()", settings, client, mode="code")
    assert result.status == "completed"
    assert "a + b" in (project / "app.py").read_text(encoding="utf-8")
    assert result.files_changed == [{"path": "app.py", "status": "modified", "added": 1, "removed": 1}]
    assert result.usage.requests == 3 and result.usage.prompt == 300 and result.usage.cached == 120
    assert result.cost is not None and result.cost > 0
    text = result.to_text()
    assert "M app.py (+1 -1)" in text and "RESULT: done" in text


def test_thinking_is_requested_and_reasoning_is_passed_back(settings):
    client = FakeClient([
        reply(calls=[tool_call("list_files", {})], reasoning="plan: list files"),
        reply("done"),
    ])
    run_agent("look around", settings, client, mode="readonly")
    first, second = client.requests
    assert first["reasoning_effort"] == "high"
    assert first["model"] == "deepseek-ai/DeepSeek-V4.1-Flash-1017"
    assistant = second["messages"][2]
    assert assistant["role"] == "assistant"
    assert assistant["reasoning_content"] == "plan: list files"
    assert second["messages"][3]["role"] == "tool"


def test_reasoning_passback_can_be_disabled(project: Path):
    settings = load_settings({"DEPUTY_API_KEY": "k", "DEPUTY_WORKSPACE": str(project),
                              "DEPUTY_KEEP_REASONING": "false"})
    client = FakeClient([reply(calls=[tool_call("list_files", {})], reasoning="r"), reply("done")])
    run_agent("look", settings, client, mode="readonly")
    assert "reasoning_content" not in client.requests[1]["messages"][2]


def test_deepseek_api_gets_its_own_thinking_switch(project: Path):
    settings = load_settings({"DEPUTY_API_KEY": "k", "DEPUTY_WORKSPACE": str(project),
                              "DEPUTY_BASE_URL": "https://api.deepseek.com"})
    request = build_request(settings, "max", [], [])
    assert request["extra_body"] == {"thinking": {"type": "enabled"}}
    assert request["reasoning_effort"] == "max"
    off = build_request(settings, "none", [], [])
    assert off["extra_body"] == {"thinking": {"type": "disabled"}} and "reasoning_effort" not in off


def test_readonly_run_cannot_write_even_if_model_tries(project: Path, settings):
    client = FakeClient([
        reply(calls=[tool_call("write_file", {"path": "evil.txt", "content": "x"})]),
        reply("ANSWER: nothing"),
    ])
    result = run_agent("question", settings, client, mode="readonly")
    assert not (project / "evil.txt").exists()
    assert "write_file" not in {t["function"]["name"] for t in client.requests[0]["tools"]}
    assert "read-only" in client.requests[1]["messages"][3]["content"]
    assert result.files_changed == []


def test_max_turns_stops_the_run(settings):
    client = FakeClient([reply(calls=[tool_call("list_files", {})]) for _ in range(3)])
    result = run_agent("loop forever", settings, client, mode="readonly", max_turns=3)
    assert result.status == "max_turns"
    assert "ended early" in result.to_text()


def test_token_budget_stops_the_run(project: Path):
    settings = load_settings({"DEPUTY_API_KEY": "k", "DEPUTY_WORKSPACE": str(project),
                              "DEPUTY_MAX_RUN_TOKENS": "10000"})
    client = FakeClient([reply(calls=[tool_call("list_files", {})], prompt=20_000), reply("never")])
    result = run_agent("big", settings, client, mode="readonly")
    assert result.status == "budget" and len(client.requests) == 1


def test_empty_task_is_rejected(settings):
    with pytest.raises(DeputyError):
        run_agent("  ", settings, FakeClient([]))


def test_workdir_must_stay_inside_workspace(settings):
    from deputy.workspace import WorkspaceError

    with pytest.raises(WorkspaceError):
        run_agent("x", settings, FakeClient([]), workdir="..")


def test_consult_runs_each_lens_and_labels_output_as_unverified(settings):
    clients = []

    def factory():
        client = FakeClient([reply("1. IDEA: try caching\nBIGGEST RISK: stale data")])
        clients.append(client)
        return client

    text, usage, cost = consult("How should we speed this up?", settings, factory,
                                lenses=["performance", "edge cases"])
    assert len(clients) == 2 and usage.requests == 2
    assert text.startswith(CONSULT_HEADER.format(model=settings.model))
    assert "Lens: performance" in text and "Lens: edge cases" in text
    systems = [c.requests[0]["messages"][0]["content"] for c in clients]
    assert any("performance" in s for s in systems) and any("edge cases" in s for s in systems)
    assert all("write_file" not in str(c.requests[0]["tools"]) for c in clients)
    assert cost is not None
