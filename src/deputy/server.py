"""MCP server that exposes Deputy to Claude Code (or any MCP client)."""
from __future__ import annotations

import asyncio
import threading
from typing import Any, Literal

from mcp.server.fastmcp import FastMCP
from mcp.server.fastmcp.exceptions import ToolError
from mcp.types import ToolAnnotations

from . import __version__
from .agent import DeputyError, Usage, consult as run_consult, run_agent
from .config import ConfigError, Settings, load_settings
from .workspace import WorkspaceError, check_root

INSTRUCTIONS = """Deputy runs a cheaper model (by default DeepSeek V4.1 Flash with thinking on) as a
sub-agent in this workspace. You stay the lead: you plan, decide and verify. Deputy does the
token-heavy work so your context stays small and focused on judgment.

When to use which tool:
- `delegate`: well-specified coding work. Multi-file edits, refactors, tests, boilerplate,
  migrations, scripts, fixing lint or type errors. Give the goal, the files or area, constraints
  and how to verify. Prefer one complete unit of work over many tiny calls.
- `investigate`: questions that need a lot of reading. "Where is X handled?", "How does the auth
  flow work?", log or data scans. Returns a compact answer with file:line evidence.
- `consult`: a cheap second opinion before you commit to an approach, when you are stuck, or
  before you call a task done. Ask for 2-3 `lenses` (for example "simplest approach",
  "edge cases and failure modes", "performance") to get diverse ideas in parallel.
  Treat the answers as unverified hints from a weaker model: weigh them below your own
  analysis and adopt only what you can confirm.

Decide to delegate BEFORE you read lots of source yourself, or you pay for the reading twice.
Keep for yourself: architecture, ambiguous root-cause analysis, security-sensitive changes,
and anything the user asked you to do personally.

Always verify Deputy's work before relying on it: read the changed files listed in the result,
check the diff, and run the tests. Deputy's "done" is a claim, not proof. Never put secrets in
`task` or `context`: they are sent to the configured model provider."""

mcp = FastMCP("deputy", instructions=INSTRUCTIONS, log_level="WARNING")

_code_lock = threading.Lock()
_session_lock = threading.Lock()
_session = {"runs": 0, "usage": Usage(), "cost": 0.0}


def make_client(settings: Settings) -> Any:
    from openai import OpenAI

    return OpenAI(base_url=settings.base_url, api_key=settings.api_key, timeout=300.0, max_retries=0)


def _ready_settings() -> Settings:
    try:
        settings = load_settings()
        check_root(settings.workspace)
    except (ConfigError, WorkspaceError) as exc:
        raise ToolError(f"Deputy is not configured correctly: {exc}") from None
    if not settings.api_key:
        raise ToolError(
            "Deputy has no API key. Set DEEPINFRA_API_KEY (or DEPUTY_API_KEY) in your "
            "environment, then restart Claude Code. See the README for the DeepInfra setup."
        )
    return settings


def _record(usage: Usage, cost: float | None) -> None:
    with _session_lock:
        _session["runs"] += 1
        _session["usage"].merge(usage)
        _session["cost"] += cost or 0.0


def _thinking(value: str | None, settings: Settings) -> str:
    return value or settings.effort


@mcp.tool(annotations=ToolAnnotations(
    title="Delegate coding work to Deputy", readOnlyHint=False, destructiveHint=True,
    idempotentHint=False, openWorldHint=True))
async def delegate(task: str, context: str = "", thinking: Literal["high", "max"] | None = None,
                   workdir: str = ".") -> str:
    """Hand a well-specified coding task to the Deputy sub-agent. It reads, edits files and runs
    commands in the workspace on its own, then returns a short report with the files it changed.

    task: the goal, scope (files or folders), constraints and acceptance criteria.
    context: facts Deputy cannot discover itself (decisions made, conventions, error messages).
    thinking: "high" (default) for normal work, "max" for hard tasks.
    workdir: subfolder of the workspace to treat as the root (default: whole workspace).

    Verify the result yourself before relying on it: review the changed files and run tests."""
    settings = _ready_settings()
    if not _code_lock.acquire(blocking=False):
        raise ToolError("Deputy is already running a coding task; wait for it to finish first.")
    try:
        result = await asyncio.to_thread(
            run_agent, task, settings, make_client(settings), mode="code", context=context,
            effort=_thinking(thinking, settings), workdir=workdir)
    except (DeputyError, WorkspaceError) as exc:
        raise ToolError(f"Deputy failed: {exc}") from None
    finally:
        _code_lock.release()
    _record(result.usage, result.cost)
    return result.to_text()


@mcp.tool(annotations=ToolAnnotations(
    title="Investigate the codebase with Deputy (read-only)", readOnlyHint=True,
    destructiveHint=False, idempotentHint=True, openWorldHint=True))
async def investigate(question: str, context: str = "",
                      thinking: Literal["high", "max"] | None = None, workdir: str = ".") -> str:
    """Ask Deputy to answer a question that needs a lot of reading: where something is handled,
    how a flow works, what a large log says. Deputy can only list, read and search files.
    Returns a compact answer with file:line evidence, so you do not have to read everything."""
    settings = _ready_settings()
    try:
        result = await asyncio.to_thread(
            run_agent, question, settings, make_client(settings), mode="readonly",
            context=context, effort=_thinking(thinking, settings), workdir=workdir)
    except (DeputyError, WorkspaceError) as exc:
        raise ToolError(f"Deputy failed: {exc}") from None
    _record(result.usage, result.cost)
    return result.to_text()


@mcp.tool(annotations=ToolAnnotations(
    title="Get a cheap second opinion from Deputy", readOnlyHint=True, destructiveHint=False,
    idempotentHint=False, openWorldHint=True))
async def consult(question: str, context: str = "", lenses: list[str] | None = None,
                  thinking: Literal["high", "max"] | None = None) -> str:
    """Brainstorm with a cheaper model: ideas, risks and alternatives you may have missed.
    Use it before committing to an approach, when stuck, or before declaring a task done.

    question: what you are deciding, including your current plan if you have one.
    context: relevant facts, constraints and what you already ruled out.
    lenses: optional list of up to 4 angles, each answered in parallel, for example
      ["simplest approach", "edge cases and failure modes", "performance"].

    The answers are UNVERIFIED suggestions from a weaker model. Weigh them below your own
    analysis, check them against the code, and adopt only what holds up."""
    settings = _ready_settings()
    try:
        text, usage, cost = await asyncio.to_thread(
            run_consult, question, settings, lambda: make_client(settings), context=context,
            lenses=lenses, effort=_thinking(thinking, settings))
    except (DeputyError, WorkspaceError) as exc:
        raise ToolError(f"Deputy failed: {exc}") from None
    _record(usage, cost)
    return text


@mcp.tool(annotations=ToolAnnotations(
    title="Deputy status", readOnlyHint=True, destructiveHint=False, idempotentHint=True,
    openWorldHint=False))
def status() -> str:
    """Show Deputy's configuration (model, thinking level, workspace, whether a key is set) and
    what this session has spent so far. Makes no network calls."""
    lines = [f"Deputy {__version__}"]
    try:
        settings = load_settings()
    except ConfigError as exc:
        return f"Deputy {__version__}: configuration error: {exc}"
    for key, value in settings.describe().items():
        lines.append(f"{key}: {value}")
    try:
        check_root(settings.workspace)
    except WorkspaceError as exc:
        lines.append(f"workspace problem: {exc}")
    with _session_lock:
        usage: Usage = _session["usage"]
        lines.append(f"this session: {_session['runs']} runs, {usage.prompt:,} in "
                     f"({usage.cached:,} cached), {usage.completion:,} out, "
                     f"est. ${_session['cost']:.4f}")
    return "\n".join(lines)


def main() -> None:
    mcp.run()
