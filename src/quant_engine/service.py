"""Servicio que descarga datos reales y arma el payload del dashboard."""

from __future__ import annotations

import json
import threading
import time
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import yfinance as yf

from .analytics import (
    annualized_covariance,
    annualized_mean,
    annualized_return,
    annualized_volatility,
    cumulative_index,
    efficient_frontier,
    forecast_portfolio,
    max_drawdown,
    max_sharpe_weights,
    sharpe_ratio,
    to_log_returns,
    year_to_date_return,
)
from .audit import audit_prices
from .config import get_settings
from .universe import (
    BENCHMARK,
    DEFAULT_UNIVERSE,
    NAMES,
    SECTORS,
    SECTOR_COLORS,
    SECTOR_SHORT,
)

CACHE_TTL_SECONDS = 900
_CACHE: dict[tuple, tuple[float, dict[str, Any]]] = {}
_CACHE_LOCK = threading.Lock()


def _cache_file() -> Path:
    return get_settings().data_cache_dir / "dashboard.json"


def _safe_float(value: Any, default: float = 0.0) -> float:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return default
    if not np.isfinite(number):
        return default
    return number


def fetch_prices(tickers: list[str], start: str, end: str) -> pd.DataFrame:
    """Descarga cierres ajustados de yfinance y devuelve una matriz fecha × ticker."""
    downloaded = yf.download(
        tickers,
        start=start,
        end=end,
        auto_adjust=True,
        progress=False,
        threads=True,
        group_by="column",
    )
    if downloaded is None or downloaded.empty:
        raise RuntimeError("yfinance no devolvió datos. Revisa tu conexión o los tickers.")

    if isinstance(downloaded.columns, pd.MultiIndex):
        close = downloaded["Close"]
    else:
        close = downloaded[["Close"]]
        if len(tickers) == 1:
            close.columns = tickers

    close = close.reindex(columns=[ticker for ticker in tickers if ticker in close.columns])
    close.index = pd.to_datetime(close.index).tz_localize(None)
    close = close.sort_index()
    close = close[~close.index.duplicated(keep="last")]
    return close.astype(float)


def _monthly_performance(
    portfolio: pd.Series,
    benchmark: pd.Series,
    risk_free: float,
    months: int = 12,
) -> list[dict[str, Any]]:
    from .analytics.stats import monthly_labels

    port_monthly = portfolio.resample("ME").last().tail(months)
    bench_monthly = benchmark.resample("ME").last().reindex(port_monthly.index).ffill()
    port_monthly = port_monthly / port_monthly.iloc[0] * 100
    bench_monthly = bench_monthly / bench_monthly.iloc[0] * 100

    labels = monthly_labels(port_monthly.index)
    rows: list[dict[str, Any]] = []
    for position, label in enumerate(labels):
        days = (position + 1) * 21
        bond_value = 100 * (1 + risk_free / 252) ** days
        rows.append(
            {
                "month": label,
                "portafolio": round(_safe_float(port_monthly.iloc[position]), 2),
                "benchmark": round(_safe_float(bench_monthly.iloc[position]), 2),
                "bonos": round(bond_value, 2),
            }
        )
    return rows


def _sector_rows(weights: pd.Series, asset_returns: pd.Series) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for ticker, weight in weights.items():
        sector = SECTORS.get(ticker, "Otros")
        rows.append({"sector": sector, "weight": weight, "return": asset_returns.get(ticker, 0.0)})

    frame = pd.DataFrame(rows)
    grouped = (
        frame.groupby("sector", as_index=False)
        .apply(
            lambda group: pd.Series(
                {
                    "weight": group["weight"].sum(),
                    "return": float((group["weight"] * group["return"]).sum() / group["weight"].sum())
                    if group["weight"].sum() > 0
                    else 0.0,
                }
            ),
            include_groups=False,
        )
        .sort_values("weight", ascending=False)
    )

    return [
        {
            "sector": row["sector"],
            "short": SECTOR_SHORT.get(row["sector"], row["sector"]),
            "weight": round(_safe_float(row["weight"]) * 100, 1),
            "return": round(_safe_float(row["return"]) * 100, 1),
            "color": SECTOR_COLORS.get(row["sector"], "#94a3b8"),
        }
        for _, row in grouped.iterrows()
    ]


def _signal(weight: float, momentum: float) -> str:
    if momentum > 0.05 and weight >= 0.02:
        return "Comprar"
    if momentum < -0.05:
        return "Reducir"
    if weight >= 0.05:
        return "Mantener"
    return "Vigilar"


def _asset_rows(
    prices: pd.DataFrame,
    weights: pd.Series,
    annual_returns: pd.Series,
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for ticker in weights.index:
        series = prices[ticker].dropna()
        if len(series) < 2:
            continue
        price = _safe_float(series.iloc[-1])
        change = _safe_float(series.iloc[-1] / series.iloc[-2] - 1)
        momentum = _safe_float(series.iloc[-1] / series.iloc[-min(21, len(series))] - 1)
        weight = _safe_float(weights.get(ticker, 0.0))
        rows.append(
            {
                "ticker": ticker,
                "name": NAMES.get(ticker, ticker),
                "sector": SECTORS.get(ticker, "Otros"),
                "price": round(price, 2),
                "change": round(change * 100, 2),
                "weight": round(weight * 100, 1),
                "signal": _signal(weight, momentum),
                "forecast": f"{momentum * 100:+.1f}%",
                "annualReturn": round(_safe_float(annual_returns.get(ticker, 0.0)) * 100, 1),
            }
        )
    return sorted(rows, key=lambda row: row["weight"], reverse=True)


def _allocation_rows(sectors: list[dict[str, Any]]) -> list[dict[str, Any]]:
    top = sectors[:6]
    rest = sectors[6:]
    rows = [{"name": row["sector"], "weight": row["weight"], "color": row["color"]} for row in top]
    if rest:
        rows.append(
            {
                "name": "Otros",
                "weight": round(sum(row["weight"] for row in rest), 1),
                "color": "#94a3b8",
            }
        )
    return rows


def _provider_rows(coverage: float, download_ms: float, universe_size: int) -> list[dict[str, Any]]:
    settings = get_settings()
    has = lambda value: bool(value)  # noqa: E731
    return [
        {
            "name": "yfinance",
            "role": "Histórico masivo",
            "status": "connected",
            "latency": f"{download_ms / 1000:.1f} s",
            "coverage": f"{coverage * 100:.1f}%",
            "limit": "Sin límite oficial",
            "note": f"{universe_size} activos descargados",
        },
        {
            "name": "Finnhub",
            "role": "Tiempo real + websocket",
            "status": "fallback" if has(settings.finnhub_api_key) else "limited",
            "latency": "—",
            "coverage": "—",
            "limit": "60 req/min",
            "note": "Clave configurada" if has(settings.finnhub_api_key) else "Sin clave en .env",
        },
        {
            "name": "Twelve Data",
            "role": "Fallback multi-activo",
            "status": "fallback" if has(settings.twelve_data_api_key) else "limited",
            "latency": "—",
            "coverage": "—",
            "limit": "8 req/min",
            "note": "Clave configurada" if has(settings.twelve_data_api_key) else "Sin clave en .env",
        },
        {
            "name": "Tiingo",
            "role": "Validación EOD",
            "status": "fallback" if has(settings.tiingo_api_key) else "limited",
            "latency": "—",
            "coverage": "—",
            "limit": "500 req/día",
            "note": "Clave configurada" if has(settings.tiingo_api_key) else "Sin clave en .env",
        },
        {
            "name": "Alpha Vantage",
            "role": "Pruebas puntuales",
            "status": "limited",
            "latency": "—",
            "coverage": "—",
            "limit": "25 req/día",
            "note": "No se usa como base",
        },
        {
            "name": "Marketstack",
            "role": "EOD secundario",
            "status": "limited",
            "latency": "—",
            "coverage": "—",
            "limit": "100 req/mes",
            "note": "No se usa como base",
        },
    ]


def _provider_comparison(coverage: float, missing_days: int, download_ms: float) -> list[dict[str, str]]:
    return [
        {
            "provider": "yfinance",
            "coverage": f"{coverage * 100:.1f}%",
            "missingDays": str(missing_days),
            "diff": "—",
            "latency": f"{download_ms / 1000:.1f} s",
            "verdict": "Base histórica",
        },
        {
            "provider": "Finnhub",
            "coverage": "—",
            "missingDays": "—",
            "diff": "—",
            "latency": "—",
            "verdict": "No medido",
        },
        {
            "provider": "Twelve Data",
            "coverage": "—",
            "missingDays": "—",
            "diff": "—",
            "latency": "—",
            "verdict": "No medido",
        },
        {
            "provider": "Tiingo",
            "coverage": "—",
            "missingDays": "—",
            "diff": "—",
            "latency": "—",
            "verdict": "No medido",
        },
    ]


def _frontier_rows(frontier: list[dict[str, float]], optimal: dict[str, float]) -> list[dict[str, Any]]:
    by_risk: dict[float, dict[str, Any]] = {}
    for row in frontier:
        risk = round(row["risk"] * 100, 1)
        candidate = {"risk": risk, "return": round(row["return"] * 100, 1), "label": None}
        current = by_risk.get(risk)
        if current is None or candidate["return"] > current["return"]:
            by_risk[risk] = candidate

    rows = [by_risk[key] for key in sorted(by_risk)]
    if not rows:
        return rows

    rows[0]["label"] = "Conservador"
    rows[-1]["label"] = "Máximo retorno"
    optimal_row = {
        "risk": round(optimal["risk"] * 100, 1),
        "return": round(optimal["return"] * 100, 1),
        "label": "Óptimo",
    }
    if all(abs(row["risk"] - optimal_row["risk"]) > 0.15 for row in rows):
        rows.append(optimal_row)
        rows.sort(key=lambda row: row["risk"])
    else:
        closest = min(rows, key=lambda row: abs(row["risk"] - optimal_row["risk"]))
        closest["label"] = "Óptimo"
    return rows


def build_dashboard(
    tickers: list[str] | None = None,
    start: str | None = None,
    end: str | None = None,
    max_weight: float = 0.18,
    risk_free: float = 0.04,
    capital: float = 100_000,
    refresh: bool = False,
) -> dict[str, Any]:
    """Descarga, calcula y devuelve todo lo que consume la web."""
    source = DEFAULT_UNIVERSE if tickers is None else tickers
    requested = [ticker.strip().upper() for ticker in source if ticker.strip()]
    requested = list(dict.fromkeys(requested))
    if not requested:
        raise ValueError("Debes indicar al menos un ticker.")
    if not 0 < max_weight <= 1:
        raise ValueError("max_weight debe estar entre 0 y 1.")
    if max_weight * len(requested) < 1:
        raise ValueError("max_weight es demasiado bajo para el número de activos.")

    end_date = end or date.today().isoformat()
    start_date = start or (date.today() - pd.Timedelta(days=365 * 3)).isoformat()
    cache_key = (tuple(requested), start_date, end_date, round(max_weight, 4), round(risk_free, 4), capital)

    now = time.monotonic()
    with _CACHE_LOCK:
        cached = _CACHE.get(cache_key)
        if cached and not refresh and now - cached[0] < CACHE_TTL_SECONDS:
            payload = json.loads(json.dumps(cached[1]))
            payload["meta"]["cached"] = True
            return payload

    started = time.perf_counter()
    all_tickers = requested + [BENCHMARK]
    raw_all = fetch_prices(all_tickers, start_date, end_date)
    download_ms = (time.perf_counter() - started) * 1000

    if BENCHMARK not in raw_all.columns:
        raise RuntimeError("No se pudo descargar el benchmark SPY.")
    benchmark_raw = raw_all[BENCHMARK].dropna()
    raw = raw_all[[ticker for ticker in requested if ticker in raw_all.columns]]

    warnings = [
        "El rendimiento es in-sample: los pesos se estimaron con el mismo periodo "
        "que se usa para medir la performance, por lo que es optimista."
    ]
    missing_tickers = [ticker for ticker in requested if ticker not in raw.columns]
    if missing_tickers:
        warnings.append(f"Tickers sin datos: {', '.join(missing_tickers)}")

    coverage_by_ticker = raw.notna().mean()
    dropped = [ticker for ticker in raw.columns if coverage_by_ticker.get(ticker, 0) < 0.6]
    if dropped:
        warnings.append(f"Se descartaron por baja cobertura: {', '.join(dropped)}")
        raw = raw.drop(columns=dropped)

    if raw.shape[1] < 2:
        raise RuntimeError("Quedaron menos de 2 activos con datos suficientes.")

    audit = audit_prices(raw, calendar=benchmark_raw.index)

    prices = raw.ffill(limit=5).dropna()
    if len(prices) < 120:
        raise RuntimeError(f"Historial insuficiente: {len(prices)} filas tras limpiar.")

    returns = to_log_returns(prices)
    if returns.empty:
        raise RuntimeError("No se pudieron calcular retornos.")

    expected_returns = annualized_mean(returns)
    covariance = annualized_covariance(returns, shrinkage=0.2)
    weights = max_sharpe_weights(expected_returns, covariance, risk_free=risk_free, max_weight=max_weight)

    portfolio_returns = returns @ weights
    portfolio_index = cumulative_index(portfolio_returns)

    benchmark_close = benchmark_raw.reindex(prices.index).ffill()
    benchmark_returns = benchmark_close.pct_change().fillna(0)
    benchmark_index = cumulative_index(benchmark_returns)

    ann_return = annualized_return(portfolio_index)
    ann_vol = float(annualized_volatility(portfolio_returns))
    bench_return = annualized_return(benchmark_index)
    bench_vol = float(annualized_volatility(benchmark_returns))
    sharpe = sharpe_ratio(ann_return, ann_vol, risk_free)
    drawdown = max_drawdown(portfolio_index)
    ytd = year_to_date_return(portfolio_index)

    asset_annual_returns = pd.Series(
        {
            ticker: annualized_return(prices[ticker], periods=252)
            for ticker in prices.columns
        }
    )
    asset_volatility = annualized_volatility(returns)

    sectors = _sector_rows(weights, asset_annual_returns)
    assets = _asset_rows(prices, weights, asset_annual_returns)
    allocation = _allocation_rows(sectors)

    frontier_raw = efficient_frontier(expected_returns, covariance, max_weight=max_weight, points=25)
    optimal_weights = weights.to_numpy(dtype=float)
    optimal_return = float(optimal_weights @ expected_returns.to_numpy(dtype=float))
    optimal_risk = float(np.sqrt(optimal_weights @ covariance.to_numpy(dtype=float) @ optimal_weights))
    frontier = _frontier_rows(
        frontier_raw,
        {"risk": optimal_risk, "return": optimal_return},
    )

    asset_risk_return = [
        {
            "ticker": ticker,
            "risk": round(_safe_float(asset_volatility.get(ticker, 0.0)) * 100, 1),
            "return": round(_safe_float(asset_annual_returns.get(ticker, 0.0)) * 100, 1),
            "weight": round(_safe_float(weights.get(ticker, 0.0)) * 100, 1),
        }
        for ticker in prices.columns
    ]

    forecast = forecast_portfolio(portfolio_index, horizon_days=126, history_months=12)
    warnings.extend(forecast.warnings)

    payload: dict[str, Any] = {
        "meta": {
            "generatedAt": datetime.now(timezone.utc).isoformat(),
            "isLive": True,
            "stale": False,
            "cached": False,
            "source": "yfinance",
            "benchmark": BENCHMARK,
            "start": str(prices.index[0].date()),
            "end": str(prices.index[-1].date()),
            "universeSize": int(prices.shape[1]),
            "requestedUniverse": requested,
            "dropped": dropped,
            "warnings": warnings,
            "riskFreeRate": risk_free,
            "maxWeight": max_weight,
            "capital": capital,
            "downloadMs": round(download_ms),
        },
        "metrics": {
            "portfolioValue": round(capital * float(portfolio_index.iloc[-1]) / 100, 2),
            "annualReturn": round(ann_return, 4),
            "ytdReturn": round(ytd, 4),
            "volatility": round(ann_vol, 4),
            "sharpe": round(sharpe, 2),
            "maxDrawdown": round(drawdown, 4),
            "universeSize": int(prices.shape[1]),
            "sectorsCount": len(sectors),
            "benchmarkReturn": round(bench_return, 4),
            "benchmarkVolatility": round(bench_vol, 4),
            "excessReturn": round(ann_return - bench_return, 4),
            "excessVolatility": round(ann_vol - bench_vol, 4),
            "capital": capital,
            "riskFreeRate": risk_free,
            "expectedReturn": round(optimal_return, 4),
            "expectedVolatility": round(optimal_risk, 4),
            "maxWeight": round(float(weights.max()), 4),
        },
        "performance": _monthly_performance(portfolio_index, benchmark_index, risk_free),
        "sectors": sectors,
        "assets": assets,
        "providers": _provider_rows(audit["coverage"], download_ms, int(prices.shape[1])),
        "providerComparison": _provider_comparison(
            audit["coverage"], audit["missingDays"], download_ms
        ),
        "auditChecks": audit["checks"],
        "auditIssues": audit["issues"],
        "auditSummary": {
            "coverage": audit["coverage"],
            "missingDays": audit["missingDays"],
            "outliers": audit["outliers"],
            "largeMoves": audit["largeMoves"],
            "rows": int(len(raw)),
            "cells": int(raw.size),
        },
        "forecast": {
            "series": forecast.rows,
            "model": forecast.model,
            "aic": forecast.aic,
            "mape": forecast.mape,
            "horizonMonths": forecast.horizon_months,
            "usedFallback": forecast.used_fallback,
        },
        "frontier": frontier,
        "assetRiskReturn": asset_risk_return,
        "allocation": allocation,
        "optimization": {
            "expectedReturn": round(optimal_return, 4),
            "volatility": round(optimal_risk, 4),
            "sharpe": round((optimal_return - risk_free) / optimal_risk, 2) if optimal_risk > 0 else 0.0,
            "maxWeight": round(float(weights.max()), 4),
            "positions": int((weights > 0.001).sum()),
        },
    }

    with _CACHE_LOCK:
        _CACHE[cache_key] = (time.monotonic(), payload)

    try:
        cache_file = _cache_file()
        cache_file.parent.mkdir(parents=True, exist_ok=True)
        cache_file.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
    except OSError:
        pass

    return payload


def load_cached_payload() -> dict[str, Any] | None:
    """Devuelve el último payload guardado en disco, si existe."""
    path = _cache_file()
    if not path.exists():
        return None
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    payload.setdefault("meta", {})
    payload["meta"]["isLive"] = False
    payload["meta"]["stale"] = True
    payload["meta"]["cached"] = True
    payload["meta"]["warnings"] = list(payload["meta"].get("warnings", [])) + [
        "No se pudo actualizar con yfinance; se muestra la última copia guardada."
    ]
    return payload


__all__ = ["build_dashboard", "fetch_prices", "load_cached_payload"]
