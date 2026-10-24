from pathlib import Path

import pytest

from deputy.config import DEFAULT_BASE_URL, DEFAULT_MODEL, ConfigError, load_settings


def test_defaults_use_deepinfra_v41_flash_with_thinking_high(tmp_path: Path):
    settings = load_settings({}, cwd=tmp_path)
    assert settings.base_url == DEFAULT_BASE_URL
    assert settings.model == DEFAULT_MODEL == "deepseek-ai/DeepSeek-V4.1-Flash-1017"
    assert settings.effort == "high"
    assert settings.mode == "accuracy"
    assert settings.api_key == ""
    assert settings.workspace == tmp_path.resolve()
    assert settings.has_prices


def test_key_precedence_and_no_openai_fallback(tmp_path: Path):
    assert load_settings({"OPENAI_API_KEY": "sk-openai"}, cwd=tmp_path).api_key == ""
    env = {"DEEPINFRA_API_KEY": "infra", "DEPUTY_API_KEY": "deputy"}
    settings = load_settings(env, cwd=tmp_path)
    assert (settings.api_key, settings.key_source) == ("deputy", "DEPUTY_API_KEY")
    assert load_settings({"DEEPINFRA_API_KEY": "infra"}, cwd=tmp_path).key_source == "DEEPINFRA_API_KEY"


def test_unsubstituted_plugin_placeholders_are_ignored(tmp_path: Path):
    env = {"DEPUTY_API_KEY": "${user_config.deepinfra_api_key}", "DEEPINFRA_API_KEY": "real",
           "DEPUTY_WORKSPACE": "${CLAUDE_PROJECT_DIR}", "DEPUTY_THINKING": "${user_config.thinking}"}
    settings = load_settings(env, cwd=tmp_path)
    assert settings.api_key == "real"
    assert settings.workspace == tmp_path.resolve()
    assert settings.effort == "high"


def test_describe_never_contains_the_key(tmp_path: Path):
    settings = load_settings({"DEPUTY_API_KEY": "super-secret"}, cwd=tmp_path)
    assert "super-secret" not in str(settings.describe())
    assert "super-secret" not in repr(settings)


@pytest.mark.parametrize("url", ["http://api.example.com/v1", "ftp://x", "https://user:pw@host/v1"])
def test_insecure_base_urls_are_rejected(tmp_path: Path, url: str):
    with pytest.raises(ConfigError):
        load_settings({"DEPUTY_BASE_URL": url}, cwd=tmp_path)


def test_local_http_is_allowed(tmp_path: Path):
    settings = load_settings({"DEPUTY_BASE_URL": "http://localhost:8080/v1/"}, cwd=tmp_path)
    assert settings.base_url == "http://localhost:8080/v1"
    assert not settings.has_prices  # unknown model and endpoint: no cost estimate


def test_bad_values_raise(tmp_path: Path):
    with pytest.raises(ConfigError):
        load_settings({"DEPUTY_THINKING": "turbo"}, cwd=tmp_path)
    with pytest.raises(ConfigError):
        load_settings({"DEPUTY_MAX_TURNS": "0"}, cwd=tmp_path)
    with pytest.raises(ConfigError):
        load_settings({"DEPUTY_KEEP_REASONING": "maybe"}, cwd=tmp_path)
    with pytest.raises(ConfigError):
        load_settings({"DEPUTY_MODE": "yolo"}, cwd=tmp_path)


def test_modes(tmp_path: Path):
    assert load_settings({"DEPUTY_MODE": "Savings"}, cwd=tmp_path).mode == "savings"
    assert load_settings({"DEPUTY_MODE": "${user_config.mode}"}, cwd=tmp_path).mode == "accuracy"
