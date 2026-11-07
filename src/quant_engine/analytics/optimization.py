"""Optimización de portafolios: máximo Sharpe y frontera eficiente."""

from __future__ import annotations

import numpy as np
import pandas as pd
from scipy.optimize import minimize


def _equal_weights(n: int) -> np.ndarray:
    return np.full(n, 1 / n)


def _normalize(weights: np.ndarray, max_weight: float) -> np.ndarray:
    clipped = np.clip(weights, 0, max_weight)
    total = clipped.sum()
    if total <= 0:
        return _equal_weights(len(weights))
    return clipped / total


def _greedy_extreme(mu: np.ndarray, max_weight: float, highest: bool) -> np.ndarray:
    """Cartera factible que maximiza (o minimiza) el retorno con tope por activo."""
    order = np.argsort(mu)
    if highest:
        order = order[::-1]
    weights = np.zeros(len(mu))
    remaining = 1.0
    for index in order:
        allocation = min(max_weight, remaining)
        weights[index] = allocation
        remaining -= allocation
        if remaining <= 1e-12:
            break
    return weights


def max_sharpe_weights(
    expected_returns: pd.Series,
    covariance: pd.DataFrame,
    risk_free: float = 0.04,
    max_weight: float = 0.18,
) -> pd.Series:
    """Pesos que maximizan el Sharpe con suma 1, sin cortos y tope por activo."""
    tickers = list(expected_returns.index)
    n = len(tickers)
    if n == 0:
        raise ValueError("El universo no contiene activos.")
    if max_weight * n < 1:
        raise ValueError("max_weight es demasiado bajo para cubrir el 100% del portafolio.")

    mu = expected_returns.to_numpy(dtype=float)
    sigma = covariance.loc[tickers, tickers].to_numpy(dtype=float)
    x0 = _equal_weights(n)
    bounds = [(0.0, max_weight)] * n
    constraints = [{"type": "eq", "fun": lambda w: float(w.sum() - 1.0)}]

    def negative_sharpe(w: np.ndarray) -> float:
        volatility = float(np.sqrt(w @ sigma @ w))
        if volatility <= 0:
            return 1e9
        return -(float(w @ mu) - risk_free) / volatility

    best_x: np.ndarray | None = None
    best_score = np.inf
    for start in (x0, _greedy_extreme(mu, max_weight, highest=True)):
        result = minimize(
            negative_sharpe,
            start,
            method="SLSQP",
            bounds=bounds,
            constraints=constraints,
            options={"maxiter": 800, "ftol": 1e-12},
        )
        if result.success and float(result.fun) < best_score:
            best_score = float(result.fun)
            best_x = np.asarray(result.x, dtype=float)

    weights = _normalize(best_x if best_x is not None else x0, max_weight)
    return pd.Series(weights, index=tickers, name="weight")


def efficient_frontier(
    expected_returns: pd.Series,
    covariance: pd.DataFrame,
    max_weight: float = 0.18,
    points: int = 25,
) -> list[dict[str, float]]:
    """Frontera eficiente: mínima varianza para niveles de retorno objetivo.

    Se calcula el rango de retorno factible respetando el tope por activo y se
    resuelve cada objetivo con arranque cálido para mejorar la convergencia.
    """
    tickers = list(expected_returns.index)
    n = len(tickers)
    mu = expected_returns.to_numpy(dtype=float)
    sigma = covariance.loc[tickers, tickers].to_numpy(dtype=float)
    bounds = [(0.0, max_weight)] * n
    sum_to_one = {"type": "eq", "fun": lambda w: float(w.sum() - 1.0)}

    lowest_weights = _greedy_extreme(mu, max_weight, highest=False)
    highest_weights = _greedy_extreme(mu, max_weight, highest=True)
    lowest = float(lowest_weights @ mu)
    highest = float(highest_weights @ mu)
    if highest <= lowest:
        return []

    def solve(target: float, start: np.ndarray) -> np.ndarray | None:
        constraints = [
            sum_to_one,
            {"type": "ineq", "fun": lambda w, t=target: float(w @ mu - t)},
        ]
        result = minimize(
            lambda w: float(w @ sigma @ w),
            start,
            method="SLSQP",
            bounds=bounds,
            constraints=constraints,
            options={"maxiter": 600, "ftol": 1e-10},
        )
        if not result.success:
            return None
        return _normalize(np.asarray(result.x, dtype=float), max_weight)

    targets = np.linspace(lowest, highest, points)
    frontier: list[dict[str, float]] = []
    warm_start = lowest_weights
    for target in targets:
        weights = solve(float(target), warm_start)
        if weights is None:
            # Reintenta desde una cartera intermedia antes de descartar el punto.
            weights = solve(float(target), _equal_weights(n))
        if weights is None:
            continue
        warm_start = weights
        risk = float(np.sqrt(weights @ sigma @ weights))
        ret = float(weights @ mu)
        frontier.append({"risk": risk, "return": ret})

    frontier.sort(key=lambda row: row["risk"])
    unique: list[dict[str, float]] = []
    for row in frontier:
        if not unique or abs(row["risk"] - unique[-1]["risk"]) > 1e-6:
            unique.append(row)
    return unique


__all__ = ["efficient_frontier", "max_sharpe_weights"]
