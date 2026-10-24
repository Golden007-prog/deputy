<div align="center">

<img src=".claude-plugin/icon.png" alt="Deputy sheriff badge logo" width="128" height="128">

# Deputy

### Deputize cheap models. Claude stays the sheriff.

**A Claude Code plugin that gives Claude a cheap second brain: DeepSeek V4.1 Flash reviews
Claude's code for bugs and offers second opinions, so Claude makes fewer mistakes.**

[![GitHub stars](https://img.shields.io/github/stars/alimohammadiamirhossein/deputy?style=social)](https://github.com/alimohammadiamirhossein/deputy/stargazers)
[![CI](https://github.com/alimohammadiamirhossein/deputy/actions/workflows/ci.yml/badge.svg)](https://github.com/alimohammadiamirhossein/deputy/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![MCP](https://img.shields.io/badge/protocol-MCP-purple.svg)](https://modelcontextprotocol.io/)

**⭐ If Deputy helps you, please [star the repo](https://github.com/alimohammadiamirhossein/deputy/stargazers) so others can find it.**

</div>

## What it does

Claude (for example Opus 5.5) stays in charge and **writes the code**. Deputy adds four tools that
run a much cheaper model as a helper inside your project:

| Tool | What it does |
|---|---|
| **`review`** | Independent reviewers hunt for bugs in Claude's change before it calls the task done |
| **`consult`** | Second opinions from 2–4 angles at once, before Claude commits to a plan |
| **`investigate`** | Reads lots of code and returns `file:line` leads |
| **`delegate`** | Hands a coding task to the cheap model (off by default; on request, or in savings mode) |

Claude treats everything Deputy says as an **unverified hint**: it checks each finding against
the code and keeps only what holds up. A typical review or second opinion costs **under one cent**.

> **Real test:** we planted an off-by-one bug in a new `average()` function. Both reviewers caught
> it independently, each with a runnable repro command and the one-line fix, and flagged the
> missing tests too. Cost: **$0.0011**, about 27 seconds.

## Quick start

**1. Get a DeepInfra API key** (DeepInfra hosts DeepSeek's models in the US)

1. Sign up at **[deepinfra.com](https://deepinfra.com/)** with GitHub, Google or email.
2. In **Dashboard → Billing**, add a card and **$5–10** of credit, then set a **spending limit**
   equal to that amount.
3. In **API Keys**, create a key (it starts with `sk-di-`) and copy it. Keep it private.

You don't need a plan, a model purchase or a dedicated GPU. Pay-as-you-go credit is enough.

**2. Install** [uv](https://docs.astral.sh/uv/getting-started/installation/) and the plugin

```bash
claude plugin marketplace add alimohammadiamirhossein/deputy
claude plugin install deputy@deputy
```

Claude Code asks for your DeepInfra key and stores it in your system's secure storage.

**3. Restart Claude Code and try it**

```text
/deputy:review
/deputy:consult I plan to cache sessions in Redis. What am I missing?
/deputy:investigate how does a request reach the database?
```

Or just work normally: Claude consults and reviews on its own for non-trivial tasks.

## Recommended model: DeepSeek V4.1 Flash, thinking `high`

The default is `deepseek-ai/DeepSeek-V4.1-Flash-1017` on DeepInfra with thinking set to `high`.
It's the best price-to-quality option we found for this job:

- **Cheap:** $0.098 per 1M input tokens and $0.294 per 1M output tokens (October 2026), cheaper
  than DeepSeek's own API.
- **Capable:** about 1M tokens of context and reliable tool calling.
- **Thinking actually on:** DeepInfra leaves its thinking **off** unless asked. Deputy always asks
  (`high`), which we confirmed by measuring the reasoning tokens.
- **Private:** DeepInfra says it doesn't train on your data. Your code isn't sent to DeepSeek's
  own servers.

## Modes

| Mode | Who writes the code | Pick it when |
|---|---|---|
| **accuracy** (default) | Claude, always | You want the best result |
| **balanced** | Claude; Deputy takes boilerplate | You want some savings without risk |
| **savings** | Deputy, Claude verifies | You want to save the most tokens |

Change it in the plugin settings (`/plugin`) or with `DEPUTY_MODE`.

## Learn more

- **[SKILL.md](SKILL.md)**: the playbook Claude follows (consult → decide → implement → review →
  check each finding). Also works without the plugin.
- **[docs/REFERENCE.md](docs/REFERENCE.md)**: all settings, costs, safety, terms of service, the
  research behind the design, troubleshooting and the roadmap.

Deputy stays within Anthropic's rules: Claude Code runs unmodified, and Deputy never touches your
Claude login. It's an ordinary MCP tool using your own DeepInfra key.

## Support the project

If Deputy caught a bug for you, **[give it a ⭐](https://github.com/alimohammadiamirhossein/deputy/stargazers)**
and share it with someone who uses Claude Code. Issues and pull requests are welcome.

[![Star History Chart](https://api.star-history.com/svg?repos=alimohammadiamirhossein/deputy&type=Date)](https://star-history.com/#alimohammadiamirhossein/deputy&Date)

---

[MIT](LICENSE) © 2026 Amirhossein Alimohammadi · Not affiliated with Anthropic, DeepSeek or DeepInfra.

<sub>Keywords: Claude Code plugin, MCP server, Model Context Protocol, AI code review, second
opinion, DeepSeek V4.1 Flash, DeepInfra, subagent, Opus, agentic coding, reduce Claude Code cost.</sub>
