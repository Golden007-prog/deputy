from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from deputy.config import load_settings


def tool_call(name: str, arguments: dict, call_id: str = "call_1") -> SimpleNamespace:
    return SimpleNamespace(id=call_id, type="function",
                           function=SimpleNamespace(name=name, arguments=json.dumps(arguments)))


def reply(content: str = "", calls: list | None = None, reasoning: str | None = None,
          finish: str | None = None, prompt: int = 100, cached: int = 40, completion: int = 20,
          thinking: int = 10) -> SimpleNamespace:
    message = SimpleNamespace(content=content, tool_calls=calls or None, reasoning_content=reasoning)
    usage = SimpleNamespace(
        prompt_tokens=prompt, completion_tokens=completion,
        prompt_tokens_details=SimpleNamespace(cached_tokens=cached),
        completion_tokens_details=SimpleNamespace(reasoning_tokens=thinking),
    )
    return SimpleNamespace(
        choices=[SimpleNamespace(message=message, finish_reason=finish or ("tool_calls" if calls else "stop"))],
        usage=usage,
    )


class FakeClient:
    """Replays scripted responses and records every request it receives."""

    def __init__(self, responses: list):
        self.responses = list(responses)
        self.requests: list[dict] = []
        self.chat = SimpleNamespace(completions=SimpleNamespace(create=self._create))

    def _create(self, **request):
        # Copy the messages: the agent keeps appending to the same list.
        self.requests.append({**request, "messages": [dict(m) for m in request["messages"]]})
        if not self.responses:
            raise AssertionError("FakeClient ran out of scripted responses")
        return self.responses.pop(0)


@pytest.fixture
def project(tmp_path: Path) -> Path:
    root = tmp_path / "project"
    root.mkdir()
    (root / "app.py").write_text("def add(a, b):\n    return a - b\n", encoding="utf-8")
    (root / "README.md").write_text("# demo\n", encoding="utf-8")
    return root


@pytest.fixture
def settings(project: Path):
    return load_settings({"DEPUTY_API_KEY": "test-key", "DEPUTY_WORKSPACE": str(project)})
