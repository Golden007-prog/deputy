"""MCP server that exposes Deputy to Claude Code (or any MCP client)."""
from __future__ import annotations

import asyncio
import threading
from typing import Any, Literal

from mcp.server.fastmcp import FastMCP
from mcp.server.fastmcp.exceptions import ToolError
from mcp.types import ToolAnnotations

from . import __version__
from .agent import DeputyError, Usage, consult as run_consult, review as run_review, run_agent
from .config import DEFAULT_MODE, ConfigError, Settings, load_settings, read_mode
from .diff import DiffError, collect_diff
from .workspace import Workspace, WorkspaceError, check_root

COMMON = """Deputy runs a cheaper model (by default DeepSeek V4.1 Flash with thinking on) as a
helper in this workspace. You are the lead: you plan, decide, write the important code and
verify. Deputy's output is never proof; check it against the code before relying on it.

Tools:
- `consult`: diverse second opinions (ideas, risks, alternatives) through 2-3 parallel `lenses`.
- `review`: independent reviewers hunt for defects in your uncommitted change (git diff).
- `investigate`: read-only search across many files; returns file:line leads.
- `delegate`: Deputy edits files and runs commands itself.
Never put secrets in any argument: everything is sent to the configured model provider."""

POLICIES = {
    "accuracy": """MODE: ACCURACY (the user wants the most accurate result; cost is secondary).
- Write and change all code yourself. Do NOT use `delegate` unless the user explicitly asks you to.
- Before committing to an approach on a non-trivial task, call `consult` with your plan and 2-3
  lenses. Weigh the ideas below your own analysis; adopt only what you verify.
- After finishing a non-trivial change and before telling the user it is done, call `review`.
  Verify every finding against the code. Fix confirmed problems; briefly note rejected ones.
- Use `investigate` only to locate code; then read the cited lines yourself before acting.""",
    "balanced": """MODE: BALANCED (accuracy first, but save tokens on low-risk work).
- Write logic, algorithms, APIs, security-sensitive and tricky code yourself.
- You may `delegate` low-risk mechanical work: boilerplate, renames, formatting, test
  scaffolding, repetitive edits across many files. Review every delegated diff yourself.
- Use `consult` before non-trivial decisions and `review` before declaring non-trivial work done.
- Use `investigate` for wide reading, then confirm the cited lines yourself.""",
    "savings": """MODE: SAVINGS (the user wants to save tokens).
- `delegate` well-specified coding work: multi-file edits, refactors, tests, boilerplate,
  migrations, lint and type fixes. Give the goal, scope, constraints and a verify command.
  Decide to delegate BEFORE reading lots of source yourself.
- Keep architecture, ambiguous root-cause analysis and security-sensitive changes yourself.
- Always verify delegated work: read the changed files, check the diff, run the tests.
- Use `investigate` for wide reading, `consult` at decision points, `review` before done.""",
}


def build_instructions(mode: str) -> str:
    return f"{COMMON}\n\n{POLICIES.get(mode, POLICIES[DEFAULT_MODE])}"


def _startup_mode() -> str:
    try:
        return read_mode()
    except ConfigError:
        return DEFAULT_MODE


mcp = FastMCP("deputy", instructions=build_instructions(_startup_mode()), log_level="WARNING")

_code_lock = threading.Lock()
_session_lock = threading.Lock()
_session = {"runs": 0, "usage": Usage(), "cost": 0.0}

Thinking = Literal["high", "max"]


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


@mcp.tool(annotations=ToolAnnotations(
    title="Get diverse second opinions from Deputy", readOnlyHint=True, destructiveHint=False,
    idempotentHint=False, openWorldHint=True))
async def consult(question: str, context: str = "", lenses: list[str] | None = None,
                  my_view: str = "", thinking: Thinking | None = None) -> str:
    """Brainstorm with a cheaper model: ideas, risks and alternatives you may have missed.
    Use it before committing to an approach, when stuck, or before declaring a task done.

    question: what you are deciding, including your current plan if you have one.
    context: relevant facts, constraints and what you already ruled out.
    lenses: up to 4 angles, each answered independently in parallel, for example
      ["simplest approach", "edge cases and failure modes", "performance"].
    my_view: your own conclusion, written BEFORE you see Deputy's ideas. It is not sent to
      Deputy, so its ideas stay independent; it is echoed back so you can compare honestly.

    The answers are UNVERIFIED suggestions from a weaker model. Weigh them below your own
    analysis, check them against the code, and adopt only what holds up."""
    settings = _ready_settings()
    try:
        text, usage, cost = await asyncio.to_thread(
            run_consult, question, settings, lambda: make_client(settings), context=context,
            lenses=lenses, effort=thinking or settings.effort)
    except (DeputyError, WorkspaceError) as exc:
        raise ToolError(f"Deputy failed: {exc}") from None
    _record(usage, cost)
    if my_view.strip():
        text = (f"YOUR VIEW BEFORE CONSULTING (not shown to Deputy): {my_view.strip()}\n"
                "Keep it unless an idea below survives your own check.\n\n" + text)
    return text


@mcp.tool(annotations=ToolAnnotations(
    title="Review your change with Deputy", readOnlyHint=True, destructiveHint=False,
    idempotentHint=False, openWorldHint=True))
async def review(focus: str = "", diff: str = "", base: str = "", paths: list[str] | None = None,
                 lenses: list[str] | None = None, thinking: Thinking | None = None) -> str:
    """Have independent cheap reviewers hunt for defects in a change, one per lens, in parallel.
    By default it reviews your uncommitted changes (git diff against HEAD, plus new files).

    focus: what the change is supposed to do, so reviewers can spot mismatches.
    diff: the change to review, if you do not want the automatic git diff.
    base: compare against this revision instead of HEAD (for example "main").
    paths: limit the review to these files or folders.
    lenses: up to 4 review angles; default ["correctness and logic bugs",
      "edge cases, error handling and missing tests"].

    Findings are UNVERIFIED and may be false positives. Verify each against the code; fix only
    what you confirm, and tell the user which findings you rejected and why."""
    settings = _ready_settings()
    try:
        text = diff.strip() or await asyncio.to_thread(
            collect_diff, Workspace(settings.workspace), base=base, paths=paths)
        result, usage, cost = await asyncio.to_thread(
            run_review, text, settings, lambda: make_client(settings), focus=focus,
            lenses=lenses, effort=thinking or settings.effort)
    except (DeputyError, DiffError, WorkspaceError) as exc:
        raise ToolError(f"Deputy review failed: {exc}") from None
    _record(usage, cost)
    return result


@mcp.tool(annotations=ToolAnnotations(
    title="Investigate the codebase with Deputy (read-only)", readOnlyHint=True,
    destructiveHint=False, idempotentHint=True, openWorldHint=True))
async def investigate(question: str, context: str = "", thinking: Thinking | None = None,
                      workdir: str = ".") -> str:
    """Ask Deputy a question that needs a lot of reading: where something is handled, how a flow
    works, what a large log says. Deputy can only list, read and search files. Returns a compact
    answer with file:line evidence. Treat it as leads: read the cited lines before acting."""
    settings = _ready_settings()
    try:
        result = await asyncio.to_thread(
            run_agent, question, settings, make_client(settings), mode="readonly",
            context=context, effort=thinking or settings.effort, workdir=workdir)
    except (DeputyError, WorkspaceError) as exc:
        raise ToolError(f"Deputy failed: {exc}") from None
    _record(result.usage, result.cost)
    return result.to_text()


@mcp.tool(annotations=ToolAnnotations(
    title="Delegate coding work to Deputy", readOnlyHint=False, destructiveHint=True,
    idempotentHint=False, openWorldHint=True))
async def delegate(task: str, context: str = "", thinking: Thinking | None = None,
                   workdir: str = ".") -> str:
    """Hand a well-specified coding task to Deputy. It reads and edits files and runs commands
    in the workspace on its own, then returns a short report with the files it changed.
    In accuracy mode, use this only when the user explicitly asks for delegation.

    task: the goal, scope (files or folders), constraints and acceptance criteria.
    context: facts Deputy cannot discover itself (decisions made, conventions, error messages).
    thinking: "high" (default) or "max" for hard tasks.
    workdir: subfolder of the workspace to treat as the root (default: whole workspace).

    Verify the result yourself before relying on it: review the changed files and run tests."""
    settings = _ready_settings()
    if not _code_lock.acquire(blocking=False):
        raise ToolError("Deputy is already running a coding task; wait for it to finish first.")
    try:
        result = await asyncio.to_thread(
            run_agent, task, settings, make_client(settings), mode="code", context=context,
            effort=thinking or settings.effort, workdir=workdir)
    except (DeputyError, WorkspaceError) as exc:
        raise ToolError(f"Deputy failed: {exc}") from None
    finally:
        _code_lock.release()
    _record(result.usage, result.cost)
    return result.to_text()


@mcp.tool(annotations=ToolAnnotations(
    title="Deputy status", readOnlyHint=True, destructiveHint=False, idempotentHint=True,
    openWorldHint=False))
def status() -> str:
    """Show Deputy's mode, model, thinking level, workspace, whether a key is set, and what this
    session has spent so far. Makes no network calls."""
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
    lines.append("")
    lines.append(POLICIES[settings.mode])
    return "\n".join(lines)


def main() -> None:
    mcp.run()
