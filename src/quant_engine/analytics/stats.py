"""Cálculos estadísticos básicos sobre precios y retornos."""

from __future__ import annotations

import numpy as np
import pandas as pd

TRADING_DAYS = 252


def to_log_returns(prices: pd.DataFrame) -> pd.DataFrame:
    """Convierte precios positivos en retornos logarítmicos diarios."""
    if prices.empty:
        raise ValueError("La matriz de precios está vacía.")
    clean = prices.astype(float).where(prices > 0)
    returns = np.log(clean).diff()
    return returns.replace([np.inf, -np.inf], np.nan).dropna(how="all")


def annualized_mean(returns: pd.DataFrame) -> pd.Series:
    """Retorno medio anualizado (aritmético) por activo."""
    return returns.mean() * TRADING_DAYS


def annualized_covariance(returns: pd.DataFrame, shrinkage: float = 0.2) -> pd.DataFrame:
    """Covarianza anualizada con contracción hacia la diagonal.

    La contracción reduce el error de estimación cuando hay muchos activos
    y pocas observaciones. ``shrinkage=0`` devuelve la covarianza muestral.
    """
    if not 0 <= shrinkage < 1:
        raise ValueError("shrinkage debe estar entre 0 y 1.")
    sample = returns.cov() * TRADING_DAYS
    diagonal = pd.DataFrame(
        np.diag(np.diag(sample.to_numpy())),
        index=sample.index,
        columns=sample.columns,
    )
    return (1 - shrinkage) * sample + shrinkage * diagonal


def annualized_volatility(returns: pd.DataFrame | pd.Series) -> pd.Series | float:
    """Volatilidad anualizada."""
    return returns.std() * np.sqrt(TRADING_DAYS)


def annualized_return(index: pd.Series, periods: int = TRADING_DAYS) -> float:
    """Retorno anualizado (geométrico) de una serie de índice base 100."""
    if len(index) < 2:
        return 0.0
    total = float(index.iloc[-1] / index.iloc[0])
    if total <= 0:
        return 0.0
    years = (len(index) - 1) / periods
    if years <= 0:
        return 0.0
    return total ** (1 / years) - 1


def sharpe_ratio(annual_return: float, annual_volatility: float, risk_free: float) -> float:
    """Sharpe anualizado. Devuelve 0 si la volatilidad es nula."""
    if annual_volatility <= 0:
        return 0.0
    return (annual_return - risk_free) / annual_volatility


def max_drawdown(index: pd.Series) -> float:
    """Máxima caída desde un máximo previo, en negativo (ej. -0.18)."""
    if index.empty:
        return 0.0
    running_max = index.cummax()
    drawdown = index / running_max - 1
    return float(drawdown.min())


def year_to_date_return(index: pd.Series) -> float:
    """Retorno desde el último cierre del año anterior."""
    if len(index) < 2:
        return 0.0
    last_date = index.index[-1]
    previous = index[index.index < pd.Timestamp(year=last_date.year, month=1, day=1)]
    if previous.empty:
        return float(index.iloc[-1] / index.iloc[0] - 1)
    base = float(previous.iloc[-1])
    return float(index.iloc[-1] / base - 1)


def cumulative_index(returns: pd.Series, base: float = 100.0) -> pd.Series:
    """Convierte retornos diarios en un índice acumulado."""
    return (1 + returns.fillna(0)).cumprod() * base


def monthly_labels(index: pd.DatetimeIndex) -> list[str]:
    """Etiquetas mensuales cortas en español, con año si cambia."""
    months = ["Ene", "Feb", "Mar", "Abr", "May", "Jun", "Jul", "Ago", "Sep", "Oct", "Nov", "Dic"]
    labels: list[str] = []
    for date in index:
        label = months[date.month - 1]
        if date.month == 1 or not labels:
            label = f"{label} {date.year % 100:02d}"
        labels.append(label)
    return labels


__all__ = [
    "TRADING_DAYS",
    "annualized_covariance",
    "annualized_mean",
    "annualized_return",
    "annualized_volatility",
    "cumulative_index",
    "max_drawdown",
    "monthly_labels",
    "sharpe_ratio",
    "to_log_returns",
    "year_to_date_return",
]
