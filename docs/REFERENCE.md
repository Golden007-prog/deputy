# Deputy reference

Everything that is not in the [README](../README.md). For how Claude should use Deputy, see
[SKILL.md](../SKILL.md).

- [Tools](#tools)
- [Modes](#modes)
- [Configuration](#configuration)
- [Install without the plugin](#install-without-the-plugin)
- [Costs](#costs)
- [Safety](#safety)
- [Terms of service and privacy](#terms-of-service-and-privacy)
- [Why the design looks like this](#why-the-design-looks-like-this)
- [Comparison](#comparison)
- [Troubleshooting](#troubleshooting)
- [Roadmap](#roadmap)
- [Contributing](#contributing)
- [Credits](#credits)

## Tools

| Tool | Parameters | Changes files? |
|---|---|---|
| `consult` | `question`, `context`, `lenses` (up to 4), `my_view`, `thinking` | No |
| `review` | `focus`, `diff`, `base`, `paths`, `lenses` (up to 4), `thinking` | No |
| `investigate` | `question`, `context`, `thinking`, `workdir` | No |
| `delegate` | `task`, `context`, `thinking`, `workdir` | Yes |
| `status` | none | No |

- `thinking` is `high` (default) or `max`.
- `review` without `diff` reviews uncommitted changes (staged and unstaged) against `HEAD`, plus
  untracked files; with `base` it compares against that revision.
- `consult` and `review` run one independent pass per lens, in parallel.
- `my_view` is never sent to the model; it is echoed back so Claude can compare honestly.

Plugin slash commands: `/deputy:consult`, `/deputy:review`, `/deputy:investigate`,
`/deputy:delegate`.

## Modes

| Mode | Claude writes | Deputy does |
|---|---|---|
| `accuracy` (default) | All code | Second opinions, reviews, wide searches. Delegation only on request |
| `balanced` | Logic and risky code | Also low-risk mechanical work |
| `savings` | Plans and reviews | Most well-specified coding |

The mode is set in the plugin settings or with `DEPUTY_MODE`, and it changes the instructions the
Deputy server gives Claude. Restart Claude Code after changing it.

## Configuration

All settings are environment variables. The plugin sets the first four for you.

| Variable | Default | Meaning |
|---|---|---|
| `DEPUTY_MODE` | `accuracy` | `accuracy`, `balanced` or `savings` |
| `DEPUTY_API_KEY` | (plugin prompt) | API key. Falls back to `DEEPINFRA_API_KEY`, then `DEEPINFRA_TOKEN` |
| `DEPUTY_THINKING` | `high` | `none`, `low`, `medium`, `high` or `max` |
| `DEPUTY_WORKSPACE` | project folder | Folder Deputy may touch. Home folders and drive roots are refused |
| `DEPUTY_MODEL` | `deepseek-ai/DeepSeek-V4.1-Flash-1017` | Any model your endpoint serves |
| `DEPUTY_BASE_URL` | `https://api.deepinfra.com/v1/openai` | Any OpenAI-compatible endpoint (https, or http on localhost) |
| `DEPUTY_MAX_TURNS` | `40` | Tool-calling rounds per run |
| `DEPUTY_MAX_RUN_TOKENS` | `2000000` | Token budget per run |
| `DEPUTY_MAX_OUTPUT_TOKENS` | `16384` | Output limit per response |
| `DEPUTY_RUN_TIMEOUT` | `1800` | Seconds per run |
| `DEPUTY_COMMAND_TIMEOUT` | `180` | Seconds per shell command |
| `DEPUTY_KEEP_REASONING` | `true` | Send the model's reasoning back between tool calls |
| `DEPUTY_PRICE_INPUT` / `_CACHED` / `_OUTPUT` | DeepInfra prices | USD per 1M tokens, for cost estimates |

Deputy never reads `OPENAI_API_KEY`, so a real OpenAI key cannot leak to another provider.

Set the key as an environment variable instead of the plugin prompt:

```bash
export DEEPINFRA_API_KEY="sk-di-..."   # macOS/Linux, add to ~/.zshrc or ~/.bashrc
```

```powershell
[Environment]::SetEnvironmentVariable('DEEPINFRA_API_KEY', 'sk-di-...', 'User')   # Windows
```

## Install without the plugin

```bash
claude mcp add deputy -s user -- uvx --from git+https://github.com/alimohammadiamirhossein/deputy deputy serve
```

Then copy [SKILL.md](../SKILL.md) to `~/.claude/skills/deputy/SKILL.md`. For Cursor, Cline,
Windsurf or Claude Desktop, add a stdio MCP server with the same `uvx ... deputy serve` command.

Check your setup (key, endpoint, and that thinking is really on):

```bash
uvx --from git+https://github.com/alimohammadiamirhossein/deputy deputy doctor
```

## Costs

Default model: DeepSeek V4.1 Flash (1017) on DeepInfra's standard tier, $0.098 / 1M input,
$0.294 / 1M output, cached input about 3% of the input price (October 2026; check
[deepinfra.com/pricing](https://deepinfra.com/pricing)).

**Measured** on a small demo project, thinking `high`:

| Run | Tokens | Time | Cost |
|---|---|---|---|
| `delegate`: fix a bug, add 3 tests, run pytest until green | 17k in (83% cached), 1k out | 46 s | $0.0006 |
| `investigate`: list functions and their tests | 6k in, 0.9k out | 18 s | $0.0004 |
| `consult` with 2 lenses | 6.5k in, 5k out | 68 s | $0.0018 |

**Estimated** for real projects: `consult` or `review` under $0.01; `investigate` $0.002–0.02;
`delegate` a multi-file change $0.01–0.10. Every result shows its real tokens and cost, and
`status` shows the session total.

## Safety

- **Workspace jail.** Paths are resolved (symlinks included) and must stay inside the project.
  Writing inside `.git` is refused.
- **Read-only means read-only.** `consult`, `review` and `investigate` get no write or shell tools.
- **No secrets in the shell.** `delegate` commands run without environment variables that look like
  secrets (`*KEY*`, `*TOKEN*`, `*SECRET*`, `*PASSWORD*`, `DEPUTY_*`, `ANTHROPIC_*`, `OPENAI_*`).
- **Stays in its lane.** Deputy is told never to install packages globally or edit system config.
- **Bounded.** Limits on rounds, tokens, run time and command time; one coding run at a time.
- **Not a full sandbox.** `delegate` can run shell commands in your project. Use version control.
- **Your code goes to the provider** you configure. Don't send files you may not share with it.

## Terms of service and privacy

- Claude Code runs unmodified and keeps using Claude. Deputy never re-routes Claude Code to other
  models, which Anthropic [does not support](https://code.claude.com/docs/en/llm-gateway).
- Deputy never touches your Claude login or subscription credentials, which Anthropic's
  [rules](https://code.claude.com/docs/en/legal-and-compliance) forbid third-party tools from using.
- Deputy is an ordinary MCP tool with your own DeepInfra key, billed to you.
- DeepInfra [states](https://docs.deepinfra.com/account/data-privacy) that it does not train on
  your data and does not store inputs to disk.

Not legal advice. Deputy is independent and not affiliated with Anthropic, DeepSeek or DeepInfra.
Claude is a trademark of Anthropic, PBC; DeepSeek is a trademark of its owner.

## Why the design looks like this

- **Independent passes, not debate.** Majority voting explains most of the gains of multi-agent
  debate ([Debate or Vote, 2025](https://arxiv.org/abs/2508.17536)), and debate can lower accuracy
  when models switch from right answers to agree ([arXiv 2509.05396](https://arxiv.org/abs/2509.05396)).
  So lenses never see each other, and Claude takes their input once.
- **Critics catch bugs, but hallucinate.** LLM critics find many real bugs and some false ones
  ([CriticGPT](https://arxiv.org/abs/2407.00215)), so every finding needs evidence, a location and
  ideally a repro, and Claude verifies each one.
- **Tool-grounded checks beat self-reflection.** Self-correction without outside feedback does not
  help reliably ([arXiv 2310.01798](https://arxiv.org/abs/2310.01798)); checks grounded in tools do
  ([CRITIC](https://arxiv.org/abs/2305.11738)).
- **Commit first.** `my_view` records Claude's conclusion before it sees the helper's ideas, so it
  doesn't drift toward a weaker model's opinion.
- **Thinking on, reasoning passed back.** DeepInfra leaves DeepSeek's thinking off unless
  `reasoning_effort` is sent (we measured zero reasoning tokens without it). Deputy always sends it
  and returns the model's reasoning during tool calls, as DeepSeek's thinking mode expects.

## Comparison

| | Deputy | Proxy routers (Claude Code → DeepSeek) | DeepSeek-only wrappers | Single-call DeepSeek MCP servers |
|---|---|---|---|---|
| Claude writes the code (accuracy mode) | ✅ | ❌ | ❌ | ✅ |
| Independent parallel reviews of Claude's diff | ✅ | ❌ | ❌ | ❌ |
| Helper has its own agent loop | ✅ | n/a | n/a | ❌ |
| Thinking on + reasoning passed back | ✅ | varies | varies | varies |
| Within Anthropic's terms with a subscription | ✅ | ⚠️ risky | ⚠️ unsupported | ✅ |
| Workspace sandbox and read-only modes | ✅ | ❌ | ❌ | n/a |

## Troubleshooting

| Problem | Fix |
|---|---|
| `Deputy has no API key` | Enter the key in the plugin settings, or set `DEEPINFRA_API_KEY`, then restart Claude Code |
| `the provider rejected the API key` | Create a new key on DeepInfra; check billing has funds |
| `refusing to use your home folder` | Start Claude Code in a project folder |
| `not a git repository` from `review` | Run `git init`, or pass the change as `diff` |
| Deputy missing in Claude Code | Check `/plugin`; make sure `uvx` is on your PATH; restart Claude Code |
| Slow first start on Windows | Antivirus scans the new files once; later starts are fast |
| Thinking seems off | Run `deputy doctor`; make sure `DEPUTY_THINKING` is not `none` |

## Roadmap

- [ ] Optional review gate: review the diff automatically when Claude finishes a turn (Stop hook)
- [ ] Follow-up threads, so Claude can question a reviewer about one finding
- [ ] Background jobs with progress, steering and cancel
- [ ] Benchmarks: accuracy and cost with and without Deputy on real tasks
- [ ] PyPI release

## Contributing

```bash
git clone https://github.com/alimohammadiamirhossein/deputy
cd deputy
python -m venv .venv && . .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -e ".[dev]"
pytest
```

## Credits

Deputy is an independent implementation inspired by
[codex-plugin-cc](https://github.com/openai/codex-plugin-cc) (adversarial review prompt),
[pal-mcp-server](https://github.com/BeehiveInnovations/pal-mcp-server) (multi-model consensus and
stance guardrails), [deliberation](https://github.com/antonbabenko/deliberation) (commit-first and
an adjudication ledger), [llm-council](https://github.com/karpathy/llm-council),
[deepseek-as-subagent](https://github.com/PsChina/deepseek-as-subagent) (an agent loop for the cheap
model), [claude-code-router](https://github.com/musistudio/claude-code-router),
[deepclaude](https://github.com/aattaran/deepclaude), and Anthropic's advisor pattern.
