"""Señales de compra/venta basadas en μ/σ combinado a horizonte 21 días."""

from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd


def _mu_signal(expected_return: float, volatility: float, risk_free: float = 0.04) -> str:
    """Señal basada en el ratio Sharpe puntual.

    - Si Sharpe > 0.5 y retorno esperado > 0 ⇒ "Comprar"
    - Si Sharpe < -0.5 ⇒ "Reducir"
    - Si 0 < Sharpe <= 0.5 ⇒ "Mantener"
    - Si Sharpe <= 0 y retorno negativo ⇒ "Vigilar"
    """
    if volatility <= 0:
        return "Vigilar"
    sharpe = (expected_return - risk_free) / volatility
    if sharpe > 0.5 and expected_return > 0:
        return "Comprar"
    if sharpe < -0.5:
        return "Reducir"
    if 0 < sharpe <= 0.5 and expected_return > 0:
        return "Mantener"
    return "Vigilar"


def _trend_signal(momentum: float, threshold: float = 0.05) -> str:
    """Señal basada en momentum a 21 días.

    - momentum > threshold     ⇒ "Comprar"
    - momentum < -threshold      ⇒ "Reducir"
    - |momentum| <= threshold    ⇒ "Mantener"
    """
    if momentum > threshold:
        return "Comprar"
    if momentum < -threshold:
        return "Reducir"
    return "Mantener"


def combined_signal(
    expected_return: float,
    volatility: float,
    momentum: float,
    risk_free: float = 0.04,
    mu_weight: float = 0.6,
    momentum_weight: float = 0.4,
) -> dict[str, Any]:
    """Señal combinada ponderando el ratio μ/σ y el momentum a 21 días.

    Parameters
    ----------
    expected_return : float
        Retorno esperado anualizado.
    volatility : float
        Volatilidad anualizada.
    momentum : float
        Momentum a 21 días (retorno simple).
    risk_free : float, opcional
        Tasa libre de riesgo anual.
    mu_weight : float, opcional
        Peso del componente μ/σ en la combinación (default 0.6).
    momentum_weight : float, opcional
        Peso del componente momentum (default 0.4). Se descarta si la suma
        no es 1.0 (se normaliza automáticamente).

    Returns
    -------
    dict con:
        - "signal": "Comprar" | "Mantener" | "Vigilar" | "Reducir"
        - "mu_sharpe": ratio Sharpe puntual.
        - "mu_score": score combinado normalizado.
        - "momentum": momentum informado.
    """
    mu_sharpe = (expected_return - risk_free) / volatility if volatility > 0 else 0.0

    # Score combinado: ponderado
    combined = mu_weight * mu_sharpe + momentum_weight * (momentum * np.sqrt(21) / volatility) if volatility > 0 else mu_sharpe

    # Decodificar señal desde el score combinado
    if combined > 0.5:
        signal = "Comprar"
    elif combined < -0.5:
        signal = "Reducir"
    elif combined > 0:
        signal = "Mantener"
    else:
        signal = "Vigilar"

    return {
        "signal": signal,
        "mu_sharpe": round(mu_sharpe, 4),
        "mu_score": round(combined, 4),
        "momentum": round(momentum, 4),
    }


def asset_signal_from_rows(
    row: dict[str, Any],
    risk_free: float = 0.04,
) -> dict[str, Any]:
    """Genera una señal para un activo a partir de una fila de datos (como las de _asset_rows).

    Parameters
    ----------
    row : dict
        Fila con al menos: "weight", "momentum", "annualReturn", "risk" (o se
        calcularán a partir de los disponibles).
    risk_free : float, opcional
        Tasa libre de riesgo anual.

    Returns
    -------
    dict con "signal", "mu_sharpe", "mu_score", "momentum".
    """
    weight = row.get("weight", 0.0) / 100.0  # fraccion
    momentum = row.get("momentum", 0.0)  # retorno a 21 días (%)
    annual_return = row.get("annualReturn", 0.0) / 100.0  # retorno anual (%)
    risk = row.get("risk", 0.0) / 100.0  # volatilidad anual (%)

    # Si no hay riesgo definido, usar volatilidad implícita a partir del retorno
    if risk <= 0 and annual_return != 0:
        # Approximation: risk ≈ sqrt(annual_return) * 0.2 (muy ruidoso)
        risk = max(abs(annual_return) * 0.1, 0.01)

    return combined_signal(
        expected_return=annual_return,
        volatility=risk,
        momentum=momentum / 100.0,  # pasar a fracción
        risk_free=risk_free,
    )