"""Gestión de perfiles de cartera, selección Top-N, dimensionamiento entero y proyección."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Literal, Tuple

import numpy as np
import pandas as pd

from .optimization import (
    efficient_frontier,
    max_return_weights,
    max_sharpe_weights,
    min_variance_weights,
    target_volatility_weights,
)
from .signals import combined_signal, asset_signal_from_rows
from .volatility import garch_volatility, portfolio_volatility_path
from .forecast import forecast_portfolio


Ticker = str
ProfileName = Literal["riesgoso", "bajo_riesgo", "moderado", "ideal", "total"]


# ── Perfiles de Markowitz sobre la frontera eficiente ──────────────────────

def profile_weights(
    expected_returns: pd.Series,
    covariance: pd.DataFrame,
    profile: ProfileName,
    max_weight: float = 0.18,
    risk_free: float = 0.04,
) -> pd.Series:
    """Devuelve los pesos para un perfil determinado.

    Perfiles disponibles:
      - "bajo_riesgo": mínima varianza
      - "moderado": volatilidad intermedia (aprox. mediana de la frontera)
      - "ideal": máximo Sharpe
      - "riesgoso": máximo retorno esperado
      - "total": unión de activos que aparecen en los 4 perfiles (ver below)
    
    Note: Si max_weight es muy bajo para el número de activos, el optimizador
    puede fallar. Se usa el max_weight proporcionado tal cual.
    """
    n = len(expected_returns)
    # Asegurar que max_weight sea suficiente para al menos un activo
    effective_max_weight = max_weight
    if effective_max_weight * n < 1:
        # Ajustar upward para poder cubrir el portafolio
        effective_max_weight = 1.0 / n
    
    if profile == "bajo_riesgo":
        w = min_variance_weights(expected_returns, covariance, max_weight=effective_max_weight)
    elif profile == "moderado":
        # Volatilidad objetivo ≈ mediana de la frontera eficiente
        frontier = efficient_frontier(expected_returns, covariance, max_weight=effective_max_weight, points=51)
        if frontier:
            med_vol = np.median([r["risk"] for r in frontier])
            w = target_volatility_weights(expected_returns, covariance, target_vol=med_vol, max_weight=effective_max_weight, risk_free=risk_free)
        else:
            w = min_variance_weights(expected_returns, covariance, max_weight=effective_max_weight)
    elif profile == "ideal":
        w = max_sharpe_weights(expected_returns, covariance, risk_free=risk_free, max_weight=effective_max_weight)
    elif profile == "riesgoso":
        w = max_return_weights(expected_returns, covariance, max_weight=effective_max_weight)
    else:
        w = pd.Series(index=expected_returns.index, dtype=float)

    # Normalizar a suma 1 (por si el optimizador no lo hizo exactamente)
    total = w.sum()
    if total > 0 and total != 1.0:
        w = w / total
    return w


# ── Score compuesto para candidatos Top-10 ────────────────────────────────

def candidate_score(
    ticker: Ticker,
    weights_by_profile: dict[ProfileName, pd.Series],
    individual_sharpe: float,
    momentum_6m: float,
    profile_order: list[ProfileName] | None = None,
) -> float:
    """Score compuesto para clasificar candidatos.

    Fórmula: 40% peso promedio en los perfiles + 30% Sharpe individual + 30% momentum 6M.

    El "peso promedio en los perfiles" es la exposición media del activo en los 4
    perfiles (bajo_riesgo, moderado, ideal, riesgoso). Si profile_order limita
    algunos perfiles, solo se computan los presentes.
    """
    if profile_order is None:
        profile_order = ["bajo_riesgo", "moderado", "ideal", "riesgoso"]

    # Promedio de pesos del activo en cada perfil
    active_weights: list[float] = []
    for p in profile_order:
        if p in weights_by_profile:
            w = float(weights_by_profile[p].get(ticker, 0.0))
            if w != 0.0:
                active_weights.append(w)
    peso_promedio = float(np.mean(active_weights)) if active_weights else 0.0

    score = 0.4 * peso_promedio + 0.3 * individual_sharpe + 0.3 * momentum_6m
    return round(score, 4)


def select_top10(
    tickers: list[Ticker],
    expected_returns: pd.Series,
    covariance: pd.DataFrame,
    individual_sharpes: dict[Ticker, float],
    momentum_6m: dict[Ticker, float],
    profile_order: list[ProfileName] | None = None,
) -> list[Ticker]:
    """Selecciona los 10 mejores activos por score compuesto.

    Devuelve la lista de tickers ordenada de mayor a menor score.
    """
    weights_by_profile = {
        p: profile_weights(expected_returns, covariance, profile=p) for p in profile_order or ["bajo_riesgo", "moderado", "ideal", "riesgoso"]
    }

    scores: list[tuple[float, Ticker]] = []
    for tkr in tickers:
        sharpe = individual_sharpes.get(tkr, 0.0)
        mom = momentum_6m.get(tkr, 0.0)
        s = candidate_score(tkr, weights_by_profile, sharpe, mom, profile_order=profile_order)
        scores.append((s, tkr))

    # Orden descendente por score
    scores.sort(key=lambda x: x[0], reverse=True)
    top10 = [tkr for _, tkr in scores[:10]]
    return top10


# ── Dataclass para el resultado de inversión ──────────────────────────────

@dataclass
class InvestmentResult:
    """Resultado de la proyección de inversión para un activo seleccionado."""

    ticker: Ticker
    name: str
    current_price: float
    shares_affordable: int  # entero hacia abajo
    residual_cash: float  # efectivo sobrante después de comprar acciones
    investment_1m: float  # monto invertido proyectado a 1 mes
    investment_3m: float  # monto invertido proyectado a 3 meses
    investment_6m: float  # monto invertido proyectado a 6 meses
    projected_price_1m: float | None = None
    projected_price_3m: float | None = None
    projected_price_6m: float | None = None
    signal: str = "Vigilar"  # señal de compra/venta
    forecast_rows: list[dict] | None = field(default=None)  # filas mensuales del pronóstico


# ── Unión de perfiles ("Total") ──────────────────────────────────────────

def total_profile_union(
    expected_returns: pd.Series,
    covariance: pd.DataFrame,
    max_weight: float = 0.18,
) -> pd.Series:
    """Perfil "Total": unión de activos que aparecen en los 4 perfiles clásicos.

    Un activo se considera "activo" en el perfil "total" si tiene peso > 0 en
    al menos uno de los 4 perfiles (bajo_riesgo, moderado, ideal, riesgoso).
    Los pesos se normalizan sobre la unión.
    """
    profiles = ["bajo_riesgo", "moderado", "ideal", "riesgoso"]
    weight_series_list = []
    for p in profiles:
        w = profile_weights(expected_returns, covariance, profile=p, max_weight=max_weight)
        weight_series_list.append(w)

    # Unión: un activo está si tiene peso > 0 en cualquier perfil
    union_mask = pd.Series(False, index=expected_returns.index)
    for ws in weight_series_list:
        union_mask = union_mask | (ws > 0.001)  # umbral mínimo

    # Construir pesos sobre la unión: promediar los pesos donde el activo existe
    union_tickers = expected_returns.index[union_mask].tolist()
    if not union_tickers:
        return pd.Series(_equal_weights(len(expected_returns)), index=expected_returns.index, name="weight")

    # Promedio simple de los pesos donde el activo esté activo en cada perfil
    # weight_series_list contiene Series con tickers como índice
    # Queremos: para cada ticker en union_tickers, el promedio de sus pesos en cada perfil
    avg_weights: dict[Ticker, float] = {}
    for ticker in union_tickers:
        weights_for_ticker = [ws[ticker] for ws in weight_series_list if ticker in ws.index]
        if weights_for_ticker:
            avg_weights[ticker] = float(np.mean(weights_for_ticker))
        else:
            avg_weights[ticker] = 0.0

    # Normalizar para que sumen 1
    total = sum(avg_weights.values())
    if total > 0:
        avg_weights = {k: v / total for k, v in avg_weights.items()}

    return pd.Series(avg_weights, index=union_tickers, name="weight")


# ── Proyección de inversión (precio, acciones, efectivo residual) ─────────

def compute_investment(
    ticker: Ticker,
    current_price: float,
    capital: float,
    monthly_returns: pd.Series | None = None,
    months: list[int] | None = None,
) -> InvestmentResult:
    """Cuánto se podría invertir y cuántas acciones se pueden comprar.

    Parameters
    ----------
    ticker : str
        Símbolo del activo.
    current_price : float
        Precio de cierre actual.
    capital : float
        Capital total disponible.
    monthly_returns : pd.Series, opcional
        Serie de retornos mensuales históricos (últimos n meses). Si se provee,
        se proyectan los precios futuros. Si no, los precios proyectados son None.
    months : list[int], opcional
        Meses sobre los que proyectar [1, 3, 6]. Si se provee monthly_returns,
        estos meses se usan para la proyección composta.

    Returns
    -------
    InvestmentResult con shares_affordable, residual_cash y proyecciones.
    """
    if months is None:
        months = [1, 3, 6]

    # Acciones enteras hacia abajo, sin fracciones
    max_shares = int(capital // current_price)  # floor hacia abajo
    residual_cash = capital - max_shares * current_price

    # Proyección de precio usando retornos mensuales compuestos
    projected_prices: dict[int, float | None] = {}
    if monthly_returns is not None and len(monthly_returns) > 0:
        # Usar el último retorno mensual observado o el promedio
        last_ret = float(monthly_returns.iloc[-1]) if len(monthly_returns) > 0 else 0.0
        avg_ret = float(monthly_returns.mean()) if len(monthly_returns) > 0 else 0.0

        p = current_price
        for m in months:
            # Proyección compuesta: precio * (1 + retorno promedio)^m
            # Usamos retorno promedio como estimación simple
            projected = current_price * ((1 + avg_ret) ** m)
            projected_prices[m] = round(projected, 2)

    # Inversión efectiva = acciones * precio proyectado
    investment: dict[int, float] = {}
    for m in months:
        proj_price = projected_prices.get(m)
        if proj_price is not None:
            investment[m] = max_shares * proj_price
        else:
            investment[m] = None  # No hay datos para proyectar

    # Señal basada en momentum simple (usando retorno último mes si está disponible)
    signal = "Vigilar"
    if monthly_returns is not None and len(monthly_returns) > 0:
        last_momentum = float(monthly_returns.iloc[-1])
        if last_momentum > 0.05:
            signal = "Comprar"
        elif last_momentum < -0.05:
            signal = "Reducir"
        else:
            signal = "Mantener"

    return InvestmentResult(
        ticker=ticker,
        name=ticker,
        current_price=round(current_price, 2),
        shares_affordable=max_shares,
        residual_cash=round(residual_cash, 2),
        investment_1m=investment.get(1),
        investment_3m=investment.get(3),
        investment_6m=investment.get(6),
        projected_price_1m=projected_prices.get(1),
        projected_price_3m=projected_prices.get(3),
        projected_price_6m=projected_prices.get(6),
        signal=signal,
    )


# ── Exportaciones menores ────────────────────────────────────────────────

__all__ = [
    "profile_weights",
    "select_top10",
    "candidate_score",
    "total_profile_union",
    "InvestmentResult",
    "compute_investment",
]