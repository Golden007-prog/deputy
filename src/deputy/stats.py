"""Rough estimates of what Deputy saved, and a running log to total them up.

The estimate assumes your lead model would have used about the same number of tokens to do
the same work. That is rough (tokenizers and working styles differ), so treat the numbers as
an order of magnitude, not a bill. Only numbers are stored, never code or prompts.
"""
from __future__ import annotations

import json
import threading
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path

from .agent import Usage
from .config import Settings

# Work Deputy did instead of the lead model, versus extra checks the lead would not otherwise run.
REPLACED_TOOLS = {"delegate", "investigate"}
CHARS_PER_TOKEN = 4
LOG_NAME = "stats.jsonl"
_lock = threading.Lock()


@dataclass
class Record:
    ts: str
    tool: str
    kind: str  # "replaced" | "check"
    lead: str
    tokens_in: int
    tokens_cached: int
    tokens_out: int
    tokens_returned: int
    deputy_cost: float
    lead_cost: float
    read_cost: float

    @property
    def saved(self) -> float:
        """Money saved versus the lead doing the work itself (only for replaced work)."""
        return self.lead_cost - self.deputy_cost - self.read_cost if self.kind == "replaced" else 0.0

    @property
    def tokens_saved(self) -> int:
        if self.kind != "replaced":
            return 0
        return max(0, self.tokens_in + self.tokens_out - self.tokens_returned)


def estimate(tool: str, usage: Usage, deputy_cost: float | None, result_text: str,
             settings: Settings) -> Record:
    cached = min(usage.cached, usage.prompt)
    returned = len(result_text) // CHARS_PER_TOKEN
    lead_cost = ((usage.prompt - cached) * settings.lead_price_input
                 + cached * settings.lead_price_cached
                 + usage.completion * settings.lead_price_output) / 1_000_000
    return Record(
        ts=datetime.now(timezone.utc).isoformat(timespec="seconds"),
        tool=tool,
        kind="replaced" if tool in REPLACED_TOOLS else "check",
        lead=settings.lead_name,
        tokens_in=usage.prompt,
        tokens_cached=cached,
        tokens_out=usage.completion,
        tokens_returned=returned,
        deputy_cost=round(deputy_cost or 0.0, 6),
        lead_cost=round(lead_cost, 6),
        read_cost=round(returned * settings.lead_price_input / 1_000_000, 6),
    )


def _k(tokens: int) -> str:
    return f"{tokens / 1000:,.1f}k" if tokens >= 1000 else str(tokens)


def footer(record: Record, settings: Settings) -> str:
    """One line appended to each tool result."""
    if not settings.lead_price_input and not settings.lead_price_output:
        return ""
    if record.kind == "replaced":
        return (f"Savings (rough): this work would cost about ${record.lead_cost:.4f} on "
                f"{record.lead}; Deputy did it for ${record.deputy_cost:.4f}. Saved about "
                f"${record.saved:.4f} and {_k(record.tokens_saved)} {record.lead} tokens.")
    return (f"Extra check (rough): ${record.deputy_cost:.4f} on Deputy; the same check on "
            f"{record.lead} would cost about ${record.lead_cost:.4f}.")


def log_path(settings: Settings) -> Path:
    return settings.data_dir / LOG_NAME


def append(record: Record, settings: Settings) -> None:
    """Best effort: a stats problem must never break a tool call."""
    if not settings.stats_enabled:
        return
    try:
        settings.data_dir.mkdir(parents=True, exist_ok=True)
        line = json.dumps(asdict(record), separators=(",", ":")) + "\n"
        with _lock, open(log_path(settings), "a", encoding="utf-8") as handle:
            handle.write(line)
    except OSError:
        pass


def load(settings: Settings) -> list[Record]:
    path = log_path(settings)
    if not path.is_file():
        return []
    records = []
    fields = set(Record.__dataclass_fields__)
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        try:
            data = json.loads(line)
            records.append(Record(**{k: v for k, v in data.items() if k in fields}))
        except (ValueError, TypeError):
            continue
    return records


@dataclass
class Totals:
    runs: int = 0
    replaced_runs: int = 0
    check_runs: int = 0
    deputy_cost: float = 0.0
    saved: float = 0.0
    tokens_saved: int = 0
    check_cost: float = 0.0
    check_lead_cost: float = 0.0

    def add(self, record: Record) -> None:
        self.runs += 1
        self.deputy_cost += record.deputy_cost
        if record.kind == "replaced":
            self.replaced_runs += 1
            self.saved += record.saved
            self.tokens_saved += record.tokens_saved
        else:
            self.check_runs += 1
            self.check_cost += record.deputy_cost
            self.check_lead_cost += record.lead_cost


def totals(records: list[Record], since: datetime | None = None) -> Totals:
    result = Totals()
    for record in records:
        if since is not None:
            try:
                if datetime.fromisoformat(record.ts) < since:
                    continue
            except ValueError:
                continue
        result.add(record)
    return result


def report(settings: Settings, session: list[Record]) -> str:
    """Session, today, last 7 days and all-time totals as a small table."""
    records = load(settings) if settings.stats_enabled else []
    now = datetime.now(timezone.utc)
    start_of_day = now.replace(hour=0, minute=0, second=0, microsecond=0)
    periods = [
        ("This session", totals(session)),
        ("Today (UTC)", totals(records, start_of_day)),
        ("Last 7 days", totals(records, now - timedelta(days=7))),
        ("All time", totals(records)),
    ]
    lines = [
        f"Deputy savings estimate (rough; lead model priced as {settings.lead_name})",
        "",
        "| Period | Runs | Deputy cost | Saved on replaced work | Lead tokens saved | Checks: cost vs on lead |",
        "|---|---|---|---|---|---|",
    ]
    for name, t in periods:
        lines.append(
            f"| {name} | {t.runs} | ${t.deputy_cost:.4f} | ${t.saved:.4f} ({t.replaced_runs} runs) | "
            f"{_k(t.tokens_saved)} | ${t.check_cost:.4f} vs ${t.check_lead_cost:.4f} ({t.check_runs} runs) |"
        )
    lines += [
        "",
        "Replaced work = delegate and investigate (the lead would otherwise do it).",
        "Checks = consult and review: extra quality checks, shown with what they would cost on the lead.",
        "Assumes the lead would use about as many tokens; money is API-equivalent even on a subscription.",
    ]
    if not settings.stats_enabled:
        lines.append("History is off (DEPUTY_STATS=false); only this session is counted.")
    else:
        lines.append(f"Log: {log_path(settings)} (numbers only, no code or prompts).")
    return "\n".join(lines)
