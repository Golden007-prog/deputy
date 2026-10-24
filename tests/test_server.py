import asyncio
from pathlib import Path

import pytest
from mcp.server.fastmcp.exceptions import ToolError

from deputy import server

from conftest import FakeClient, reply


def test_tools_are_registered():
    tools = asyncio.run(server.mcp.list_tools())
    assert {t.name for t in tools} == {"delegate", "investigate", "consult", "review", "status"}
    assert "UNVERIFIED" in next(t for t in tools if t.name == "consult").description
    assert "UNVERIFIED" in next(t for t in tools if t.name == "review").description


def test_instructions_follow_the_mode():
    accuracy = server.build_instructions("accuracy")
    assert "Do NOT use `delegate` unless the user explicitly asks" in accuracy
    assert "call `review`" in accuracy
    assert "low-risk mechanical work" in server.build_instructions("balanced")
    assert "`delegate` well-specified coding work" in server.build_instructions("savings")
    assert server.build_instructions("nonsense") == accuracy


def test_missing_key_gives_a_helpful_error(project: Path, monkeypatch):
    for name in ("DEPUTY_API_KEY", "DEEPINFRA_API_KEY", "DEEPINFRA_TOKEN"):
        monkeypatch.delenv(name, raising=False)
    monkeypatch.setenv("DEPUTY_WORKSPACE", str(project))
    with pytest.raises(ToolError, match="DEEPINFRA_API_KEY"):
        asyncio.run(server.delegate("do something"))


def test_status_shows_config_without_the_key(project: Path, monkeypatch):
    monkeypatch.setenv("DEPUTY_API_KEY", "very-secret-key")
    monkeypatch.setenv("DEPUTY_WORKSPACE", str(project))
    text = server.status()
    assert "DeepSeek-V4.1-Flash-1017" in text and "thinking: high" in text
    assert "mode: accuracy" in text and "MODE: ACCURACY" in text
    assert "very-secret-key" not in text


def test_delegate_end_to_end_with_fake_provider(project: Path, monkeypatch):
    monkeypatch.setenv("DEPUTY_API_KEY", "k")
    monkeypatch.setenv("DEPUTY_WORKSPACE", str(project))
    fake = FakeClient([reply("RESULT: done")])
    monkeypatch.setattr(server, "make_client", lambda settings: fake)
    text = asyncio.run(server.delegate("say done", thinking="max"))
    assert "RESULT: done" in text and "thinking max" in text
    assert fake.requests[0]["reasoning_effort"] == "max"
