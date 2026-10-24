import json
from pathlib import Path

import pytest

from deputy import stats
from deputy.agent import Usage
from deputy.config import ConfigError, load_settings


def usage(prompt=100_000, cached=80_000, completion=5_000) -> Usage:
    u = Usage()
    u.prompt, u.cached, u.completion, u.requests = prompt, cached, completion, 3
    return u


def test_replaced_work_estimate_uses_opus_prices(settings):
    record = stats.estimate("delegate", usage(), 0.002, "x" * 4000, settings)
    # Opus 5.5: 20k uncached * $4 + 80k cached * $0.20 + 5k out * $20, per 1M tokens.
    assert record.lead_cost == pytest.approx((20_000 * 4 + 80_000 * 0.2 + 5_000 * 20) / 1e6)
    assert record.kind == "replaced" and record.tokens_returned == 1000
    assert record.read_cost == pytest.approx(1000 * 4 / 1e6)
    assert record.saved == pytest.approx(record.lead_cost - 0.002 - record.read_cost)
    assert record.tokens_saved == 105_000 - 1000
    line = stats.footer(record, settings)
    assert line.startswith("Savings (rough)") and "Claude Opus 5.5" in line


def test_checks_are_not_counted_as_savings(settings):
    record = stats.estimate("review", usage(), 0.001, "report", settings)
    assert record.kind == "check" and record.saved == 0 and record.tokens_saved == 0
    assert stats.footer(record, settings).startswith("Extra check (rough)")


def test_lead_model_choice_and_custom_prices(project: Path):
    sonnet = load_settings({"DEPUTY_LEAD_MODEL": "sonnet", "DEPUTY_WORKSPACE": str(project)})
    assert sonnet.lead_name == "Claude Sonnet 5.5" and sonnet.lead_price_output == 10.0
    custom = load_settings({"DEPUTY_LEAD_MODEL": "custom", "DEPUTY_LEAD_PRICE_INPUT": "1.25",
                            "DEPUTY_LEAD_PRICE_OUTPUT": "10", "DEPUTY_WORKSPACE": str(project)})
    assert (custom.lead_price_input, custom.lead_price_output) == (1.25, 10.0)
    no_prices = load_settings({"DEPUTY_LEAD_MODEL": "custom", "DEPUTY_WORKSPACE": str(project)})
    assert stats.footer(stats.estimate("delegate", usage(), 0.0, "", no_prices), no_prices) == ""
    with pytest.raises(ConfigError):
        load_settings({"DEPUTY_LEAD_MODEL": "gpt-9", "DEPUTY_WORKSPACE": str(project)})


def test_log_round_trip_and_report(settings):
    first = stats.estimate("delegate", usage(), 0.002, "done", settings)
    second = stats.estimate("consult", usage(10_000, 0, 2_000), 0.001, "ideas", settings)
    stats.append(first, settings)
    stats.append(second, settings)
    lines = stats.log_path(settings).read_text(encoding="utf-8").splitlines()
    assert len(lines) == 2 and json.loads(lines[0])["tool"] == "delegate"
    assert "task" not in lines[0] and "done" not in lines[0]  # numbers only, no text
    loaded = stats.load(settings)
    total = stats.totals(loaded)
    assert total.runs == 2 and total.replaced_runs == 1 and total.check_runs == 1
    assert total.saved == pytest.approx(first.saved)
    text = stats.report(settings, [first])
    assert "| This session | 1 |" in text and "| All time | 2 |" in text


def test_stats_can_be_turned_off(project: Path, tmp_path: Path):
    settings = load_settings({"DEPUTY_STATS": "off", "DEPUTY_WORKSPACE": str(project),
                              "DEPUTY_DATA_DIR": str(tmp_path / "off")})
    stats.append(stats.estimate("delegate", usage(), 0.0, "", settings), settings)
    assert not stats.log_path(settings).exists()
    assert "History is off" in stats.report(settings, [])


def test_corrupt_log_lines_are_skipped(settings):
    path = stats.log_path(settings)
    path.parent.mkdir(parents=True, exist_ok=True)
    good = stats.estimate("investigate", usage(), 0.001, "", settings)
    path.write_text("not json\n{\"tool\": 1}\n", encoding="utf-8")
    stats.append(good, settings)
    assert len(stats.load(settings)) == 1
