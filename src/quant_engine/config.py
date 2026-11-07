"""Configuración central del motor cuantitativo.

Las credenciales se leen desde ``config/.env`` (ignorado por git) o desde
variables de entorno. Nunca deben escribirse en el código ni en los notebooks.

Ejemplo::

    from quant_engine.config import get_settings

    settings = get_settings()
    token = settings.require("finnhub_api_key")
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parents[2]
CONFIG_DIR = PROJECT_ROOT / "config"
ENV_FILE = CONFIG_DIR / ".env"

_DEFAULT_CACHE_DIR = PROJECT_ROOT / "data" / "cache"


def _env(name: str, default: str | None = None) -> str | None:
    """Lee una variable de entorno y normaliza valores vacíos a ``None``."""
    value = os.getenv(name)
    if value is None:
        return default
    value = value.strip()
    return value or default


def _env_path(name: str, default: Path) -> Path:
    value = _env(name)
    if not value:
        return default
    path = Path(value).expanduser()
    return path if path.is_absolute() else PROJECT_ROOT / path


def _env_int(name: str, default: int) -> int:
    value = _env(name)
    if value is None:
        return default
    try:
        parsed = int(value)
    except ValueError as exc:
        raise ValueError(f"{name} debe ser un número entero, se recibió: {value!r}") from exc
    if parsed <= 0:
        raise ValueError(f"{name} debe ser mayor que cero, se recibió: {parsed}")
    return parsed


@dataclass(frozen=True)
class Settings:
    """Configuración tipada del proyecto."""

    alpha_vantage_api_key: str | None
    twelve_data_api_key: str | None
    finnhub_api_key: str | None
    marketstack_api_key: str | None
    ipstack_api_key: str | None
    tiingo_api_key: str | None
    default_data_provider: str
    data_cache_dir: Path
    request_timeout: int

    def require(self, field_name: str) -> str:
        """Devuelve una credencial obligatoria o lanza un error explicativo."""
        value = getattr(self, field_name, None)
        if not value:
            env_name = field_name.upper()
            raise RuntimeError(
                f"Falta la credencial {env_name}. "
                f"Copia config/.env.example a config/.env y completa la clave."
            )
        return str(value)


def _build_settings() -> Settings:
    # override=False: las variables del sistema tienen prioridad sobre el .env.
    load_dotenv(dotenv_path=ENV_FILE, override=False)

    return Settings(
        alpha_vantage_api_key=_env("ALPHA_VANTAGE_API_KEY"),
        twelve_data_api_key=_env("TWELVE_DATA_API_KEY"),
        finnhub_api_key=_env("FINNHUB_API_KEY"),
        marketstack_api_key=_env("MARKETSTACK_API_KEY"),
        ipstack_api_key=_env("IPSTACK_API_KEY"),
        tiingo_api_key=_env("TIINGO_API_KEY"),
        default_data_provider=(_env("DEFAULT_DATA_PROVIDER", "yfinance") or "yfinance").lower(),
        data_cache_dir=_env_path("DATA_CACHE_DIR", _DEFAULT_CACHE_DIR),
        request_timeout=_env_int("REQUEST_TIMEOUT", 30),
    )


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Carga la configuración una sola vez por proceso."""
    return _build_settings()


__all__ = ["CONFIG_DIR", "ENV_FILE", "PROJECT_ROOT", "Settings", "get_settings"]
