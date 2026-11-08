"""Pronóstico de series de precios con ARIMA."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import numpy as np
import pandas as pd



@dataclass
class ForecastResult:
    rows: list[dict[str, float | str | None]]
    model: str
    aic: float | None
    mape: float | None
    horizon_months: int
    used_fallback: bool
    warnings: list[str]


def _spanish_months() -> list[str]:
    return ["Ene", "Feb", "Mar", "Abr", "May", "Jun", "Jul", "Ago", "Sep", "Oct", "Nov", "Dic"]


def _month_label(date: pd.Timestamp) -> str:
    return f"{_spanish_months()[date.month - 1]} {date.year % 100:02d}"


def _fit_and_forecast(
    log_price: pd.Series,
    order: tuple[int, int, int],
    steps: int,
) -> tuple[pd.Series, pd.Series, pd.Series, float, float | None]:
    from statsmodels.tsa.arima.model import ARIMA

    # Se pasa un ndarray para evitar problemas de frecuencia con pandas 3.
    values = log_price.to_numpy(dtype=float)

    # Validación simple fuera de muestra para reportar MAPE.
    split = max(int(len(values) * 0.8), 60)
    mape: float | None = None
    if split < len(values) - 5:
        try:
            train = values[:split]
            test = values[split:]
            validation = ARIMA(train, order=order).fit()
            predicted = np.asarray(validation.get_forecast(steps=len(test)).predicted_mean)
            actual = np.exp(test)
            forecast = np.exp(predicted)
            mask = actual != 0
            if mask.any():
                mape = float(np.mean(np.abs((forecast[mask] - actual[mask]) / actual[mask])))
        except Exception:
            mape = None

    model = ARIMA(values, order=order).fit()
    forecast = model.get_forecast(steps=steps)
    mean = np.exp(np.asarray(forecast.predicted_mean, dtype=float))
    interval = np.exp(np.asarray(forecast.conf_int(alpha=0.05), dtype=float))
    return mean, interval[:, 0], interval[:, 1], float(model.aic), mape


def _fit_best_order(
    values: np.ndarray,
    d: int,
    max_p: int = 2,
    max_q: int = 2,
) -> tuple[Any, tuple[int, int, int]] | None:
    """Busca ``(p, q)`` por AIC con ``d`` fijado por ADF/KPSS.

    Se limita a ``p + q <= 2`` para que el ajuste de los 10 activos no bloquee
    la API. Es una grilla pequeña, pero suficiente para retornos financieros.
    """
    from statsmodels.tsa.arima.model import ARIMA

    best: tuple[float, tuple[int, int, int], Any] | None = None
    for p in range(max_p + 1):
        for q in range(max_q + 1):
            if p + q > 2:
                continue
            try:
                fitted = ARIMA(values, order=(p, d, q)).fit()
            except Exception:
                continue
            if best is None or float(fitted.aic) < best[0]:
                best = (float(fitted.aic), (p, d, q), fitted)
    if best is None:
        return None
    return best[2], best[1]


def _out_of_sample_mape(
    values: np.ndarray,
    order: tuple[int, int, int],
    test_size: int = 60,
) -> float | None:
    """MAPE sobre los últimos días, ajustando el mismo orden con menos datos."""
    from statsmodels.tsa.arima.model import ARIMA

    if len(values) < 160:
        return None
    split = len(values) - min(test_size, max(len(values) // 5, 20))
    try:
        train = values[:split]
        test = values[split:]
        validation = ARIMA(train, order=order).fit()
        predicted = np.asarray(
            validation.get_forecast(steps=len(test)).predicted_mean, dtype=float
        )
        actual = np.exp(test)
        forecast = np.exp(predicted)
        mask = actual != 0
        if not mask.any():
            return None
        return float(np.mean(np.abs((forecast[mask] - actual[mask]) / actual[mask])))
    except Exception:
        return None


def forecast_asset_arima(
    ticker: str,
    prices: pd.Series,
    horizon_days: int = 126,
) -> dict[str, Any]:
    """Ajusta ARIMA a un activo y devuelve el orden, supuestos y veredicto.

    El objetivo no es solo pronosticar: también explicar *por qué* el modelo es
    defendible (o no). Por eso se reportan ADF/KPSS, Ljung-Box, Jarque-Bera,
    ARCH-LM, raíces, significancia de coeficientes y MAPE fuera de muestra.
    """
    from .diagnostics import arima_diagnostics, decide_differencing

    series = prices.replace([np.inf, -np.inf], np.nan).dropna().astype(float)
    if len(series) < 90:
        return {
            "ticker": ticker,
            "order": None,
            "orderValues": None,
            "aic": None,
            "mape": None,
            "converged": False,
            "verdict": "Débil",
            "summary": "Datos insuficientes: se necesitan al menos 90 observaciones.",
            "assumptions": [],
            "caveats": ["La serie es demasiado corta para un ARIMA estable."],
        }

    log_price = np.log(series)
    values = log_price.to_numpy(dtype=float)
    stationarity = decide_differencing(log_price)
    d = int(stationarity["d"])

    fitted = _fit_best_order(values, d=d)
    if fitted is None:
        return {
            "ticker": ticker,
            "order": None,
            "orderValues": None,
            "aic": None,
            "mape": None,
            "converged": False,
            "verdict": "Débil",
            "summary": "Ningún orden ARIMA(p,d,q) de la grilla convergió.",
            "assumptions": [],
            "caveats": ["Prueba con una ventana de datos más larga o revisa la serie."],
        }

    model, order = fitted
    mape = _out_of_sample_mape(values, order)
    diagnostics = arima_diagnostics(model, stationarity, mape)

    forecast = model.get_forecast(steps=horizon_days)
    predicted = np.exp(np.asarray(forecast.predicted_mean, dtype=float))
    intervals = np.exp(np.asarray(forecast.conf_int(alpha=0.05), dtype=float))

    def _at(index: int) -> float:
        return round(float(predicted[min(index, len(predicted) - 1)]), 2)

    p, d_value, q = order
    return {
        "ticker": ticker,
        "order": f"ARIMA({p},{d_value},{q})",
        "orderValues": [p, d_value, q],
        "aic": round(float(model.aic), 2),
        "mape": round(mape * 100, 2) if mape is not None else None,
        "converged": True,
        "verdict": diagnostics["verdict"],
        "summary": diagnostics["summary"],
        "assumptions": diagnostics["assumptions"],
        "caveats": diagnostics["caveats"],
        "passedCount": diagnostics["passedCount"],
        "total": diagnostics["total"],
        "projectedPrice1m": _at(20),
        "projectedPrice3m": _at(62),
        "projectedPrice6m": _at(125),
        "lower6m": round(float(intervals[125, 0]), 2) if len(intervals) > 125 else None,
        "upper6m": round(float(intervals[125, 1]), 2) if len(intervals) > 125 else None,
    }


def forecast_portfolio(
    index: pd.Series,
    horizon_days: int = 126,
    history_months: int = 12,
    order: tuple[int, int, int] = (2, 1, 2),
) -> ForecastResult:
    """Pronostica un índice base 100 y devuelve filas mensuales para graficar.

    El modelo se ajusta sobre el logaritmo del precio (d=1), no sobre retornos
    sueltos, para preservar el nivel de la serie. Si statsmodels falla, devuelve
    un pronóstico ingenuo (último valor) marcado como fallback.
    """
    series = index.dropna().astype(float)
    if len(series) < 90:
        raise ValueError("Se necesitan al menos 90 observaciones para ajustar ARIMA.")

    warnings: list[str] = []
    used_fallback = False
    model_name = f"ARIMA{order}"
    aic: float | None = None
    mape: float | None = None

    log_price = np.log(series)
    try:
        mean_values, lower_values, upper_values, aic, mape = _fit_and_forecast(
            log_price, order, horizon_days
        )
        future_index = pd.bdate_range(
            series.index[-1] + pd.Timedelta(days=1), periods=horizon_days
        )
        mean = pd.Series(mean_values, index=future_index)
        lower = pd.Series(lower_values, index=future_index)
        upper = pd.Series(upper_values, index=future_index)
    except Exception as exc:  # pragma: no cover - depende de la versión de statsmodels
        used_fallback = True
        warnings.append(f"ARIMA no pudo ajustarse ({exc}). Se usó pronóstico ingenuo.")
        last = float(series.iloc[-1])
        future_index = pd.bdate_range(series.index[-1] + pd.Timedelta(days=1), periods=horizon_days)
        mean = pd.Series(np.full(horizon_days, last), index=future_index)
        lower = pd.Series(np.full(horizon_days, last), index=future_index)
        upper = pd.Series(np.full(horizon_days, last), index=future_index)
        model_name = "Naive (fallback)"

    # Serie histórica mensual.
    monthly = series.resample("ME").last().tail(history_months)
    rows: list[dict[str, float | str | None]] = []
    for date, value in monthly.items():
        rows.append(
            {
                "date": _month_label(date),
                "actual": round(float(value), 2),
                "forecast": None,
                "lower": None,
                "range": None,
            }
        )

    # Une el último punto histórico con el inicio del pronóstico.
    if rows:
        last_row = rows[-1]
        last_row["forecast"] = last_row["actual"]
        last_row["lower"] = last_row["actual"]
        last_row["range"] = 0.0

    forecast_monthly = mean.resample("ME").last()
    lower_monthly = lower.resample("ME").last()
    upper_monthly = upper.resample("ME").last()
    for date in forecast_monthly.index[:6]:
        point = float(forecast_monthly.loc[date])
        low = float(lower_monthly.loc[date])
        high = float(upper_monthly.loc[date])
        rows.append(
            {
                "date": _month_label(date),
                "actual": None,
                "forecast": round(point, 2),
                "lower": round(low, 2),
                "range": round(max(high - low, 0.0), 2),
            }
        )

    return ForecastResult(
        rows=rows,
        model=model_name,
        aic=round(aic, 1) if aic is not None else None,
        mape=round(mape * 100, 2) if mape is not None else None,
        horizon_months=min(6, len(forecast_monthly)),
        used_fallback=used_fallback,
        warnings=warnings,
    )


__all__ = ["ForecastResult", "forecast_asset_arima", "forecast_portfolio"]
