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
    forecast_asset_arima,
    forecast_portfolio,
    max_drawdown,
    max_sharpe_weights,
    sharpe_ratio,
    to_log_returns,
    year_to_date_return,
    asset_signal_from_rows,
    candidate_score,
    compute_investment,
    garch_volatility,
    InvestmentResult,
    portfolio_volatility_path,
    profile_weights,
    select_top10,
    total_profile_union,
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


def _profile_summary(
    weights: pd.Series,
    expected_returns: pd.Series,
    covariance: pd.DataFrame,
    risk_free: float,
) -> dict[str, Any]:
    """Resume un perfil: pesos (en %) y métricas anualizadas."""
    active = weights[weights > 0.001].sort_values(ascending=False)
    if active.empty:
        return {
            "weights": {},
            "expectedReturn": 0.0,
            "volatility": 0.0,
            "sharpe": 0.0,
        }

    tickers = list(active.index)
    vector = active.to_numpy(dtype=float)
    total = float(vector.sum())
    if total > 0:
        vector = vector / total
    ret = float(vector @ expected_returns.loc[tickers].to_numpy(dtype=float))
    cov = covariance.loc[tickers, tickers].to_numpy(dtype=float)
    vol = float(np.sqrt(max(vector @ cov @ vector, 0.0)))
    return {
        "weights": {ticker: round(float(weight) * 100, 1) for ticker, weight in zip(tickers, vector)},
        "expectedReturn": round(ret, 4),
        "volatility": round(vol, 4),
        "sharpe": round((ret - risk_free) / vol, 2) if vol > 0 else 0.0,
    }


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

    # ── Perfiles de cartera ──────────────────────────────────────────────
    profiles = ["bajo_riesgo", "moderado", "ideal", "riesgoso"]
    profile_weights_dict: dict[str, pd.Series] = {}
    for p in profiles:
        profile_weights_dict[p] = profile_weights(
            expected_returns, covariance, profile=p, max_weight=max_weight, risk_free=risk_free
        )

    # Perfil "Total" = unión de activos en los 4 perfiles
    total_weights = total_profile_union(expected_returns, covariance, max_weight=max_weight)
    profile_payload = {
        p: _profile_summary(profile_weights_dict[p], expected_returns, covariance, risk_free)
        for p in profiles
    }
    profile_payload["total"] = _profile_summary(
        total_weights, expected_returns, covariance, risk_free
    )

    # ── Selección Top-10 ────────────────────────────────────────────────
    # Calculamos sharpe individual y momentum 6M por activo
    asset_annual_returns = pd.Series(
        {ticker: annualized_return(prices[ticker], periods=252) for ticker in prices.columns}
    )
    asset_volatility = annualized_volatility(returns)

    individual_sharpes: dict[str, float] = {}
    momentum_6m: dict[str, float] = {}
    for ticker in prices.columns:
        vol = _safe_float(asset_volatility.get(ticker, 0.0))
        ret = _safe_float(asset_annual_returns.get(ticker, 0.0))
        individual_sharpes[ticker] = (ret - risk_free) / vol if vol > 0 else 0.0
        # Momentum a 6 meses (aprox. 126 días hábiles)
        try:
            mom_series = prices[ticker].pct_change().tail(126)
            momentum_6m[ticker] = float(mom_series.sum()) if len(mom_series) > 0 else 0.0
        except Exception:
            momentum_6m[ticker] = 0.0

    top10 = select_top10(
        tickers=list(prices.columns),
        expected_returns=expected_returns,
        covariance=covariance,
        individual_sharpes=individual_sharpes,
        momentum_6m=momentum_6m,
        profile_order=profiles,
    )
    top10_scores = {
        ticker: candidate_score(
            ticker,
            profile_weights_dict,
            individual_sharpes.get(ticker, 0.0),
            momentum_6m.get(ticker, 0.0),
            profile_order=profiles,
        )
        for ticker in top10
    }

    # Recalcular Markowitz con los top 10 (máximo Sharpe). Si el universo es
    # pequeño, el tope por activo se relaja lo justo para poder sumar 100%.
    top10_max_weight = max(max_weight, 1.0 / len(top10))
    top10_returns = expected_returns[top10]
    top10_cov = covariance.loc[top10, top10]
    top10_weights = max_sharpe_weights(
        top10_returns, top10_cov, risk_free=risk_free, max_weight=top10_max_weight
    )

    # Ajustar pesos: algunos pueden ser 0, rebalanceamos sobre los que tienen peso > 0
    top10_weights = top10_weights[top10_weights > 0.001]
    if top10_weights.sum() > 0:
        top10_weights = top10_weights / top10_weights.sum()
    else:
        top10_weights = pd.Series(np.full(len(top10), 1 / len(top10)), index=top10, name="weight")

    # Asegurarnos de que top10_weights tenga los 10 tickers (rellenar con 0 si faltan)
    for ticker in top10:
        if ticker not in top10_weights.index:
            top10_weights[ticker] = 0.0

    top10_weights = top10_weights / top10_weights.sum()
    weights = max_sharpe_weights(
        expected_returns, covariance, risk_free=risk_free, max_weight=max_weight
    )

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
            "weight": round(_safe_float(top10_weights.get(ticker, 0.0)) * 100, 1),
        }
        for ticker in top10
    ]

    # ── GARCH de cartera y proyección de inversión ───────────────────────
    top10_returns_series = returns[top10]

    # Path de volatilidad del portafolio: GARCH sobre los retornos de la cartera
    # (R @ w), no sobre un activo aislado.
    w_array = top10_weights.to_numpy(dtype=float)
    vol_path_result = portfolio_volatility_path(
        w_array, top10_cov, returns_series=top10_returns_series
    )
    vol_path = vol_path_result["conditional_vol_path"]
    vol_path_values = vol_path.tolist() if hasattr(vol_path, "tolist") else list(vol_path)

    # GARCH por activo (top 10)
    garch_per_asset: dict[str, Any] = {}
    for ticker in top10:
        try:
            fitted = garch_volatility(prices[ticker], vol_origin="prices")
            path = fitted["conditional_vol"]
            path_values = path.tolist() if hasattr(path, "tolist") else list(path)
            garch_per_asset[ticker] = {
                "finalVolatility": round(_safe_float(fitted["final_vol"]) * 100, 2),
                "unconditionalVolatility": round(
                    _safe_float(fitted["unconditional_vol"]) * 100, 2
                ),
                "conditionalVolatility": [
                    round(_safe_float(value) * 100, 2) for value in path_values[-60:]
                ],
            }
        except Exception:
            garch_per_asset[ticker] = {
                "finalVolatility": 0.0,
                "unconditionalVolatility": 0.0,
                "conditionalVolatility": [],
            }

    # Proyección de inversión por activo (todo el top 10)
    last_prices = prices.iloc[-1].to_dict()
    investment_results: list[InvestmentResult] = []
    for ticker in top10:
        price = _safe_float(last_prices.get(ticker, 0.0))
        if price <= 0:
            continue
        # Retornos mensuales simples a partir de precios mensuales.
        try:
            monthly_prices = prices[ticker].resample("ME").last().dropna()
            monthly_ret = monthly_prices.pct_change().dropna()
        except Exception:
            monthly_ret = None
        if monthly_ret is None or len(monthly_ret) == 0:
            try:
                monthly_ret = pd.Series([prices[ticker].pct_change().iloc[-1]])
            except Exception:
                monthly_ret = None

        investment_results.append(
            compute_investment(
                ticker=ticker,
                current_price=price,
                capital=capital,
                monthly_returns=monthly_ret,
                months=[1, 3, 6],
            )
        )

    # Asset rows con señales combinadas (mu/σ + momentum) y score Top-10.
    asset_rows: list[dict[str, Any]] = []
    for ticker in top10:
        weight = _safe_float(top10_weights.get(ticker, 0.0))
        try:
            mom_21 = float(prices[ticker].pct_change().tail(21).sum())
        except Exception:
            mom_21 = 0.0

        annual_ret = _safe_float(asset_annual_returns.get(ticker, 0.0))
        risk = _safe_float(asset_volatility.get(ticker, 0.0))

        signal_data = asset_signal_from_rows(
            {
                "weight": weight * 100,
                "momentum": mom_21 * 100,
                "annualReturn": annual_ret * 100 if annual_ret else 0.0,
                "risk": risk * 100 if risk else 0.0,
            },
            risk_free=risk_free,
        )

        series = prices[ticker].dropna()
        if len(series) < 2:
            continue
        price = _safe_float(series.iloc[-1])
        change = _safe_float(series.iloc[-1] / series.iloc[-2] - 1)

        asset_rows.append(
            {
                "ticker": ticker,
                "name": NAMES.get(ticker, ticker),
                "sector": SECTORS.get(ticker, "Otros"),
                "price": round(price, 2),
                "change": round(change * 100, 2),
                "weight": round(weight * 100, 1),
                "signal": signal_data["signal"],
                "forecast": f"{mom_21 * 100:+.1f}%",
                "annualReturn": round(annual_ret * 100, 1) if annual_ret else 0.0,
                "mu_sharpe": signal_data["mu_sharpe"],
                "mu_score": signal_data["mu_score"],
                "momentum_21d": round(mom_21 * 100, 2),
                "score": top10_scores.get(ticker, 0.0),
            }
        )
    assets = asset_rows

    # ── Forecast ARIMA del portafolio y por activo ───────────────────────
    portfolio_index = cumulative_index(returns[top10] @ top10_weights)
    forecast = forecast_portfolio(portfolio_index, horizon_days=126, history_months=12)

    asset_arima: list[dict[str, Any]] = []
    for ticker in top10:
        try:
            asset_arima.append(forecast_asset_arima(ticker, prices[ticker]))
        except Exception as exc:
            asset_arima.append(
                {
                    "ticker": ticker,
                    "order": None,
                    "orderValues": None,
                    "aic": None,
                    "mape": None,
                    "converged": False,
                    "verdict": "Débil",
                    "summary": f"No se pudo ajustar ARIMA: {str(exc)[:120]}",
                    "assumptions": [],
                    "caveats": [],
                }
            )

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
            "profiles": profile_payload,
            "top10": top10,
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
            "sharpe": round((optimal_return - risk_free) / optimal_risk, 2)
            if optimal_risk > 0
            else 0.0,
            "maxWeight": round(float(top10_weights.max()), 4),
            "positions": int((top10_weights > 0.001).sum()),
        },
        "investment": [
            {
                "ticker": inv.ticker,
                "name": inv.name,
                "currentPrice": inv.current_price,
                "sharesAffordable": inv.shares_affordable,
                "residualCash": inv.residual_cash,
                "investment1m": inv.investment_1m,
                "investment3m": inv.investment_3m,
                "investment6m": inv.investment_6m,
                "projectedPrice1m": inv.projected_price_1m,
                "projectedPrice3m": inv.projected_price_3m,
                "projectedPrice6m": inv.projected_price_6m,
                "signal": inv.signal,
            }
            for inv in investment_results
        ],
        "garch": {
            "portfolioVolatility": {
                "final": round(_safe_float(vol_path_result["final_vol"]) * 100, 4),
                "path": [
                    round(_safe_float(value) * 100, 4) for value in vol_path_values[-120:]
                ],
            },
            "perAsset": garch_per_asset,
        },
        "asset_arima": asset_arima,
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
