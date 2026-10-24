# Deputy benchmark

Measures what Deputy changes on real Claude Code runs: **did the work pass tests Claude never
saw, and what did it cost?**

Each run copies a task into a fresh temporary git repo and runs `claude -p` headless with the task
prompt. Then it runs that task's hidden tests. Every task is run in up to four configs:

| Config | What Claude gets |
|---|---|
| `claude` | No Deputy at all (baseline) |
| `accuracy` | Deputy in accuracy mode: Claude writes the code, Deputy reviews and consults |
| `balanced` | Deputy in balanced mode |
| `savings` | Deputy in savings mode: Deputy takes well-specified coding work |

Costs come from the tools themselves, not estimates: Claude's from Claude Code's
`total_cost_usd`, Deputy's from the `est. cost` figure on each Deputy result.

## Tasks

| Task | Kind | What the hidden tests check |
|---|---|---|
| `rate_limiter` | implement | half-open window, rejected calls not counted, bad config, bounded speed |
| `booking_ranges` | fix bugs | touching, contained and unsorted ranges; clipping to the day |
| `expense_report` | implement | quoted amounts, BOM, case, empty rows, half-up rounding, line numbers in errors |
| `rename_refactor` | mechanical refactor | new name everywhere, deprecated alias warns, helpers don't warn |

Each task folder has `task.md` (the prompt), `repo/` (the starting code with visible tests) and
`hidden/` (the tests Claude never sees). The hidden tests were checked to fail on the starting
code and pass with a correct solution.

## Run it

You need Claude Code (`claude` on your PATH), Python with `pytest`, and a DeepInfra key. Deputy
starts with `uvx` if you have it, or else from the current Python, so install it there first
(`pip install -e .` from the repo root).

```bash
export DEEPINFRA_API_KEY="sk-di-..."
python bench/run.py                              # all tasks: claude, accuracy, savings
python bench/run.py --configs claude accuracy --repeats 3
python bench/run.py --tasks booking_ranges --model sonnet
```

Results go to `bench/results/<timestamp>/` as `results.md` (tables), `results.json` and one
transcript per run (`*.jsonl`, not committed).

**This spends real money.** Each Opus run costs Claude Code tokens (often $0.10–$1.00), plus a
fraction of a cent for Deputy. The default run is 4 tasks × 3 configs = 12 runs.

## Reading the results

- Compare **pass rate** first, then **total cost** (Claude + Deputy) and time.
- Runs vary, so use `--repeats 3` or more before publishing a number, and publish the whole table,
  including the runs where Deputy didn't help.
- In `accuracy` mode Claude may decide a small task doesn't need Deputy at all. The
  "Deputy calls" column shows what was actually used.
- Your user-level Claude Code settings and `CLAUDE.md` apply to every config equally. Disable the
  Deputy plugin while benchmarking so the `claude` baseline really has no Deputy.

## Adding a task

Create `bench/tasks/<name>/` with `task.md`, `repo/` and `hidden/test_hidden.py`. Hidden tests
run with the work folder on `PYTHONPATH`, and its path in `BENCH_WORKDIR`. Check that they fail
on the starting code and pass with a correct solution before you trust a result.
