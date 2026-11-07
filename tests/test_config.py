from __future__ import annotations

from pathlib import Path

import pytest

from quant_engine import config
from quant_engine.config import Settings, get_settings


@pytest.fixture(autouse=True)
def _clear_settings_cache():
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


def _make_settings(**overrides) -> Settings:
    values = {
        "alpha_vantage_api_key": None,
        "twelve_data_api_key": None,
        "finnhub_api_key": None,
        "marketstack_api_key": None,
        "ipstack_api_key": None,
        "tiingo_api_key": None,
        "default_data_provider": "yfinance",
        "data_cache_dir": Path("data/cache"),
        "request_timeout": 30,
    }
    values.update(overrides)
    return Settings(**values)


def test_get_settings_reads_environment(monkeypatch, tmp_path):
    monkeypatch.setattr(config, "ENV_FILE", tmp_path / "no-existe.env")
    monkeypatch.setenv("FINNHUB_API_KEY", "clave-de-prueba")
    monkeypatch.setenv("DEFAULT_DATA_PROVIDER", "FINNHUB")
    monkeypatch.setenv("REQUEST_TIMEOUT", "15")
    monkeypatch.setenv("DATA_CACHE_DIR", str(tmp_path / "cache"))

    settings = get_settings()

    assert settings.finnhub_api_key == "clave-de-prueba"
    assert settings.default_data_provider == "finnhub"
    assert settings.request_timeout == 15
    assert settings.data_cache_dir == tmp_path / "cache"


def test_get_settings_defaults(monkeypatch, tmp_path):
    monkeypatch.setattr(config, "ENV_FILE", tmp_path / "no-existe.env")
    for name in [
        "ALPHA_VANTAGE_API_KEY",
        "TWELVE_DATA_API_KEY",
        "FINNHUB_API_KEY",
        "MARKETSTACK_API_KEY",
        "IPSTACK_API_KEY",
        "TIINGO_API_KEY",
        "DEFAULT_DATA_PROVIDER",
        "DATA_CACHE_DIR",
        "REQUEST_TIMEOUT",
    ]:
        monkeypatch.delenv(name, raising=False)

    settings = get_settings()

    assert settings.default_data_provider == "yfinance"
    assert settings.request_timeout == 30
    assert settings.data_cache_dir == config.PROJECT_ROOT / "data" / "cache"


def test_require_raises_for_missing_key():
    settings = _make_settings()

    with pytest.raises(RuntimeError, match="FINNHUB_API_KEY"):
        settings.require("finnhub_api_key")


def test_require_returns_key_when_present():
    settings = _make_settings(finnhub_api_key="abc123")

    assert settings.require("finnhub_api_key") == "abc123"


def test_invalid_timeout_raises(monkeypatch, tmp_path):
    monkeypatch.setattr(config, "ENV_FILE", tmp_path / "no-existe.env")
    monkeypatch.setenv("REQUEST_TIMEOUT", "cero")

    with pytest.raises(ValueError, match="REQUEST_TIMEOUT"):
        get_settings()


def test_non_positive_timeout_raises(monkeypatch, tmp_path):
    monkeypatch.setattr(config, "ENV_FILE", tmp_path / "no-existe.env")
    monkeypatch.setenv("REQUEST_TIMEOUT", "0")

    with pytest.raises(ValueError, match="mayor que cero"):
        get_settings()
