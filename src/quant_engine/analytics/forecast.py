"""Pronóstico de series de precios con ARIMA."""

from __future__ import annotations

from dataclasses import dataclass

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


__all__ = ["ForecastResult", "forecast_portfolio"]
