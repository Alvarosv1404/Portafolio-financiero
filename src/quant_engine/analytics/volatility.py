"""Volatilidad condicional con GARCH(1,1) y fallback."""

from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd

try:
    from arch import arch_model
    ARCH_AVAILABLE = True
except ImportError:  # pragma: no cover - depende del entorno
    ARCH_AVAILABLE = False


def _to_returns(series: pd.Series) -> pd.Series:
    """Convierte precios en retornos logarítmicos diarios."""
    clean = series.replace([np.inf, -np.inf], np.nan).dropna()
    if len(clean) < 2:
        return pd.Series(dtype=float, index=pd.DatetimeIndex([]))
    returns = np.log(clean / clean.shift(1)).dropna()
    return returns


def _annualized_vol(returns: pd.Series) -> float:
    values = returns.replace([np.inf, -np.inf], np.nan).dropna()
    if len(values) < 2:
        return 0.0
    return float(np.std(values, ddof=1) * np.sqrt(252))


def _fit_garch(returns: pd.Series) -> dict[str, Any]:
    """Ajusta GARCH(1,1) y devuelve volatilidad condicional anualizada.

    ``arch`` recomienda reescalar los retornos diarios (≈0.008) a porcentaje
    (≈0.8) para que el optimizador converja mejor. Ajustamos en porcentaje y
    volvemos a fracción antes de devolver los resultados.
    """
    clean = returns.replace([np.inf, -np.inf], np.nan).dropna().astype(float)
    if len(clean) < 20:
        return {
            "conditional_vol": pd.Series(dtype=float),
            "annualized": pd.Series(dtype=float),
            "unconditional_vol": _annualized_vol(clean),
            "final_vol": 0.0,
            "model": None,
        }

    scale = 100.0
    am = arch_model(
        clean.to_numpy(dtype=float) * scale,
        vol="garch",
        p=1,
        q=1,
        dist="normal",
        mean="Zero",
        rescale=False,
    )
    model = am.fit(disp="off", show_warning=False)

    # ``conditional_volatility`` ya es la desviación estándar condicional, no la
    # varianza: no hay que aplicarle otra raíz cuadrada.
    cond_vol = pd.Series(
        np.asarray(model.conditional_volatility, dtype=float) / scale,
        index=clean.index,
    )
    annualized = cond_vol * np.sqrt(252)

    params = model.params
    omega = float(params.get("omega", np.nan))
    alpha = float(params.get("alpha[1]", np.nan))
    beta = float(params.get("beta[1]", np.nan))
    persistence = alpha + beta
    if np.isfinite(omega) and np.isfinite(persistence) and 0 < persistence < 1:
        # omega viene en (porcentaje diario)^2; lo devolvemos a fracción diaria.
        uncond_daily_var = (omega / (1.0 - persistence)) / (scale ** 2)
        uncond_vol = float(np.sqrt(uncond_daily_var) * np.sqrt(252))
    else:
        uncond_vol = _annualized_vol(clean)

    final_vol = float(annualized.iloc[-1]) if len(annualized) else uncond_vol
    return {
        "conditional_vol": cond_vol,
        "annualized": annualized,
        "unconditional_vol": uncond_vol,
        "final_vol": final_vol,
        "model": model,
    }


def _empty_result(message: str = "") -> dict[str, Any]:
    result: dict[str, Any] = {
        "volatility": pd.Series(dtype=float),
        "conditional_vol": pd.Series(dtype=float),
        "unconditional_vol": 0.0,
        "final_vol": 0.0,
        "model": None,
    }
    if message:
        result["_error"] = message
    return result


def garch_volatility(
    series: pd.Series,
    vol_origin: str = "prices",
) -> dict[str, Any]:
    """Volatilidad condicional GARCH(1,1) sobre retornos diarios.

    Parameters
    ----------
    series : pd.Series
        Serie de precios o retornos (si ya son retornos, usar
        ``vol_origin="returns"``).
    vol_origin : str
        ``"prices"`` (default): convierte precios a retornos logarítmicos.
        ``"returns"``: la serie ya contiene retornos.

    Returns
    -------
    dict con:
        - ``volatility``: volatilidad anualizada (fracción) por día.
        - ``conditional_vol``: volatilidad condicional diaria (fracción).
        - ``unconditional_vol``: volatilidad anualizada de largo plazo.
        - ``final_vol``: volatilidad anualizada del último día.
        - ``model``: modelo ajustado o ``None``.
    """
    if not ARCH_AVAILABLE:
        return _empty_result("arch package not available")

    try:
        returns = (
            _to_returns(series)
            if vol_origin != "returns"
            else series.replace([np.inf, -np.inf], np.nan).dropna().astype(float)
        )
        if len(returns) < 20:
            return _empty_result("Datos insuficientes para GARCH")
        fitted = _fit_garch(returns)
        return {
            "volatility": fitted["annualized"],
            "conditional_vol": fitted["conditional_vol"],
            "unconditional_vol": fitted["unconditional_vol"],
            "final_vol": fitted["final_vol"],
            "model": fitted["model"],
        }
    except Exception as exc:  # pragma: no cover - depende de los datos
        return _empty_result(str(exc))


def portfolio_volatility_path(
    weights: np.ndarray | list[float],
    covariance: pd.DataFrame,
    returns_series: pd.DataFrame | pd.Series | None = None,
) -> dict[str, Any]:
    """Volatilidad condicional del portafolio con GARCH(1,1).

    Si se pasan los retornos de los activos, se construye primero la serie de
    retornos del portafolio (``R @ w``) y se ajusta GARCH sobre ella. Así la
    volatilidad es realmente la de la cartera y no la de un activo suelto.

    ``covariance`` debe estar anualizada. Se usa solo como respaldo cuando no
    hay retornos o cuando ``arch`` no está disponible.
    """
    weights_array = np.asarray(weights, dtype=float)
    if len(weights_array) == 0:
        return {"conditional_vol_path": pd.Series(dtype=float), "final_vol": 0.0}

    # Normalizar pesos si no suman 1.
    total = float(np.sum(weights_array))
    if total > 0 and abs(total - 1.0) > 1e-9:
        weights_array = weights_array / total

    # Volatilidad de respaldo a partir de la covarianza anualizada.
    cov = covariance.to_numpy(dtype=float)
    fallback_vol = 0.0
    try:
        portfolio_variance = float(weights_array @ cov @ weights_array)
        fallback_vol = float(np.sqrt(max(portfolio_variance, 0.0)))
    except Exception:
        fallback_vol = 0.0

    if not ARCH_AVAILABLE:
        n_days = len(returns_series) if returns_series is not None else max(len(cov), 1)
        path = pd.Series(np.full(max(n_days, 1), fallback_vol, dtype=float))
        return {"conditional_vol_path": path, "final_vol": fallback_vol}

    try:
        if returns_series is None:
            # Sin retornos: usamos una volatilidad constante como aproximación.
            n_days = max(len(cov), 30)
            path = pd.Series(np.full(n_days, fallback_vol, dtype=float))
            return {"conditional_vol_path": path, "final_vol": fallback_vol}

        if isinstance(returns_series, pd.DataFrame):
            frame = returns_series.replace([np.inf, -np.inf], np.nan).dropna()
            if frame.empty:
                raise ValueError("Sin retornos válidos para el portafolio.")
            if len(weights_array) != frame.shape[1]:
                raise ValueError(
                    f"Pesos ({len(weights_array)}) y activos ({frame.shape[1]}) no coinciden."
                )
            portfolio_returns = pd.Series(
                frame.to_numpy(dtype=float) @ weights_array,
                index=frame.index,
            )
        else:
            portfolio_returns = returns_series.replace([np.inf, -np.inf], np.nan).dropna()

        fitted = _fit_garch(portfolio_returns)
        path = fitted["annualized"]
        final_vol = float(fitted["final_vol"]) if len(path) else fallback_vol
        return {
            "conditional_vol_path": path if len(path) else pd.Series(np.full(len(portfolio_returns), fallback_vol)),
            "final_vol": final_vol,
            "model": fitted["model"],
        }
    except Exception:
        n_days = len(returns_series) if returns_series is not None else 30
        path = pd.Series(np.full(max(n_days, 1), fallback_vol, dtype=float))
        return {"conditional_vol_path": path, "final_vol": fallback_vol}


__all__ = ["ARCH_AVAILABLE", "garch_volatility", "portfolio_volatility_path"]
