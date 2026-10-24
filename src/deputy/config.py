"""Settings loaded from environment variables.

Deputy never reads secrets from files. The API key comes from the
environment (or from Claude Code's plugin secure storage, which is passed
in as an environment variable).
"""
from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Mapping
from urllib.parse import urlsplit

DEFAULT_BASE_URL = "https://api.deepinfra.com/v1/openai"
DEFAULT_MODEL = "deepseek-ai/DeepSeek-V4.1-Flash-1017"
DEFAULT_EFFORT = "high"
EFFORTS = ("none", "low", "medium", "high", "max")
# accuracy: Claude writes all code; Deputy only gives second opinions and reviews.
# balanced: Deputy also takes low-risk mechanical work. savings: Deputy takes most coding work.
MODES = ("accuracy", "balanced", "savings")
DEFAULT_MODE = "accuracy"

# Checked in order. OPENAI_API_KEY is deliberately NOT a fallback: sending
# someone's real OpenAI key to another provider would leak it.
KEY_VARS = ("DEPUTY_API_KEY", "DEEPINFRA_API_KEY", "DEEPINFRA_TOKEN")

# USD per 1M tokens for the default model on DeepInfra (October 2026).
# Prices change; override with DEPUTY_PRICE_INPUT / _CACHED / _OUTPUT.
KNOWN_PRICES = {
    (DEFAULT_BASE_URL, DEFAULT_MODEL): (0.098, 0.0029, 0.294),
}

LOOPBACK_HOSTS = {"localhost", "127.0.0.1", "::1"}


class ConfigError(RuntimeError):
    """Raised when the environment holds an invalid setting."""


def _get(env: Mapping[str, str], name: str) -> str:
    value = (env.get(name) or "").strip()
    # An unsubstituted plugin placeholder such as "${user_config.x}" means
    # "not set", not a literal value.
    if not value or "${" in value:
        return ""
    return value


def _int(env: Mapping[str, str], name: str, default: int, low: int, high: int) -> int:
    raw = _get(env, name)
    if not raw:
        return default
    try:
        value = int(raw)
    except ValueError:
        raise ConfigError(f"{name} must be an integer, got {raw!r}") from None
    if not low <= value <= high:
        raise ConfigError(f"{name} must be between {low} and {high}, got {value}")
    return value


def _float(env: Mapping[str, str], name: str, default: float) -> float:
    raw = _get(env, name)
    if not raw:
        return default
    try:
        value = float(raw)
    except ValueError:
        raise ConfigError(f"{name} must be a number, got {raw!r}") from None
    if value < 0:
        raise ConfigError(f"{name} must not be negative")
    return value


def _bool(env: Mapping[str, str], name: str, default: bool) -> bool:
    raw = _get(env, name).lower()
    if not raw:
        return default
    if raw in {"1", "true", "yes", "on"}:
        return True
    if raw in {"0", "false", "no", "off"}:
        return False
    raise ConfigError(f"{name} must be true or false, got {raw!r}")


def validate_base_url(url: str) -> str:
    parts = urlsplit(url)
    host = (parts.hostname or "").lower()
    if not host:
        raise ConfigError(f"DEPUTY_BASE_URL has no host: {url!r}")
    if parts.username or parts.password:
        raise ConfigError("DEPUTY_BASE_URL must not contain credentials")
    if parts.scheme == "https":
        return url.rstrip("/")
    if parts.scheme == "http" and host in LOOPBACK_HOSTS:
        return url.rstrip("/")
    raise ConfigError("DEPUTY_BASE_URL must use https (http is allowed only for localhost)")


def is_deepseek_api(url: str) -> bool:
    host = (urlsplit(url).hostname or "").lower()
    return host == "deepseek.com" or host.endswith(".deepseek.com")


@dataclass(frozen=True)
class Settings:
    api_key: str = field(repr=False)
    key_source: str
    base_url: str
    model: str
    effort: str
    mode: str
    workspace: Path
    max_turns: int
    max_run_tokens: int
    max_output_tokens: int
    run_timeout: int
    command_timeout: int
    keep_reasoning: bool
    price_input: float
    price_cached: float
    price_output: float

    @property
    def has_prices(self) -> bool:
        return self.price_input > 0 or self.price_output > 0

    def describe(self) -> dict:
        """A summary that is safe to show: it never contains the key."""
        return {
            "mode": self.mode,
            "model": self.model,
            "endpoint": self.base_url,
            "thinking": self.effort,
            "api_key": f"set (from {self.key_source})" if self.api_key else "MISSING",
            "workspace": str(self.workspace),
            "max_turns": self.max_turns,
            "max_tokens_per_run": self.max_run_tokens,
        }


def read_mode(env: Mapping[str, str] | None = None) -> str:
    env = os.environ if env is None else env
    mode = (_get(env, "DEPUTY_MODE") or DEFAULT_MODE).lower()
    if mode not in MODES:
        raise ConfigError(f"DEPUTY_MODE must be one of {', '.join(MODES)}, got {mode!r}")
    return mode


def _workspace(env: Mapping[str, str], cwd: Path | None) -> Path:
    for name in ("DEPUTY_WORKSPACE", "CLAUDE_PROJECT_DIR"):
        value = _get(env, name)
        if value:
            return Path(value).expanduser().resolve()
    return (cwd or Path.cwd()).resolve()


def load_settings(env: Mapping[str, str] | None = None, cwd: Path | None = None) -> Settings:
    env = os.environ if env is None else env
    api_key, key_source = "", ""
    for name in KEY_VARS:
        value = _get(env, name)
        if value:
            api_key, key_source = value, name
            break

    base_url = validate_base_url(_get(env, "DEPUTY_BASE_URL") or DEFAULT_BASE_URL)
    model = _get(env, "DEPUTY_MODEL") or DEFAULT_MODEL
    effort = (_get(env, "DEPUTY_THINKING") or DEFAULT_EFFORT).lower()
    if effort not in EFFORTS:
        raise ConfigError(f"DEPUTY_THINKING must be one of {', '.join(EFFORTS)}, got {effort!r}")
    mode = read_mode(env)

    known = KNOWN_PRICES.get((base_url, model), (0.0, 0.0, 0.0))
    return Settings(
        api_key=api_key,
        key_source=key_source,
        base_url=base_url,
        model=model,
        effort=effort,
        mode=mode,
        workspace=_workspace(env, cwd),
        max_turns=_int(env, "DEPUTY_MAX_TURNS", 40, 1, 200),
        max_run_tokens=_int(env, "DEPUTY_MAX_RUN_TOKENS", 2_000_000, 10_000, 50_000_000),
        max_output_tokens=_int(env, "DEPUTY_MAX_OUTPUT_TOKENS", 16_384, 256, 65_536),
        run_timeout=_int(env, "DEPUTY_RUN_TIMEOUT", 1_800, 30, 86_400),
        command_timeout=_int(env, "DEPUTY_COMMAND_TIMEOUT", 180, 5, 3_600),
        keep_reasoning=_bool(env, "DEPUTY_KEEP_REASONING", True),
        price_input=_float(env, "DEPUTY_PRICE_INPUT", known[0]),
        price_cached=_float(env, "DEPUTY_PRICE_CACHED", known[1]),
        price_output=_float(env, "DEPUTY_PRICE_OUTPUT", known[2]),
    )
