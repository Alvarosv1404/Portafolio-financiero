"""Diagnósticos estadísticos para validar un modelo ARIMA.

Un ARIMA es defendible cuando la serie modelada es estacionaria, los residuos
se comportan como ruido blanco, las raíces quedan fuera del círculo unitario y
el error fuera de muestra es razonable. La normalidad y la homocedasticidad son
deseables, pero en series financieras suelen fallar; por eso se reportan aparte
y se complementan con GARCH.
"""

from __future__ import annotations

import warnings
from typing import Any

import numpy as np
import pandas as pd


def _num(value: Any) -> float | None:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    if not np.isfinite(number):
        return None
    return number


def _kpss_pvalue(value: Any) -> float | None:
    """KPSS devuelve 0.01/0.10 cuando el p-valor cae fuera de la tabla."""
    number = _num(value)
    if number is None:
        return None
    return min(max(number, 0.001), 0.999)


def adf_test(series: pd.Series | np.ndarray) -> dict[str, Any]:
    """Contraste de raíz unitaria ADF: p < 0.05 ⇒ serie estacionaria."""
    from statsmodels.tsa.stattools import adfuller

    values = np.asarray(series, dtype=float)
    values = values[np.isfinite(values)]
    if len(values) < 20:
        return {"stat": None, "pValue": None, "passed": False, "detail": "Muestra insuficiente"}
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            stat, pvalue = adfuller(values, autolag="AIC")[:2]
        pvalue = _num(pvalue)
        return {
            "stat": round(_num(stat) or 0.0, 4),
            "pValue": round(pvalue, 4) if pvalue is not None else None,
            "passed": pvalue is not None and pvalue < 0.05,
            "detail": (
                "Sin raíz unitaria: la serie es estacionaria"
                if pvalue is not None and pvalue < 0.05
                else "No se rechaza raíz unitaria: la serie no es estacionaria"
            ),
        }
    except Exception as exc:  # pragma: no cover - depende de los datos
        return {"stat": None, "pValue": None, "passed": False, "detail": f"ADF no pudo calcularse: {exc}"}


def kpss_test(series: pd.Series | np.ndarray) -> dict[str, Any]:
    """Contraste KPSS: p > 0.05 ⇒ no se rechaza estacionariedad."""
    from statsmodels.tsa.stattools import kpss

    values = np.asarray(series, dtype=float)
    values = values[np.isfinite(values)]
    if len(values) < 20:
        return {"stat": None, "pValue": None, "passed": False, "detail": "Muestra insuficiente"}
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            stat, pvalue = kpss(values, regression="c", nlags="auto")[:2]
        pvalue = _kpss_pvalue(pvalue)
        return {
            "stat": round(_num(stat) or 0.0, 4),
            "pValue": round(pvalue, 4) if pvalue is not None else None,
            "passed": pvalue is not None and pvalue > 0.05,
            "detail": (
                "No se rechaza estacionariedad"
                if pvalue is not None and pvalue > 0.05
                else "Se rechaza estacionariedad"
            ),
        }
    except Exception as exc:  # pragma: no cover
        return {"stat": None, "pValue": None, "passed": False, "detail": f"KPSS no pudo calcularse: {exc}"}


def ljung_box_test(residuals: np.ndarray, lags: int = 10) -> dict[str, Any]:
    """Ljung-Box: p > 0.05 ⇒ no hay autocorrelación residual (ruido blanco)."""
    from statsmodels.stats.diagnostic import acorr_ljungbox

    values = np.asarray(residuals, dtype=float)
    values = values[np.isfinite(values)]
    if len(values) < max(lags + 5, 20):
        return {"stat": None, "pValue": None, "passed": False, "detail": "Muestra insuficiente"}
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            result = acorr_ljungbox(values, lags=[lags], return_df=True)
        stat = _num(result["lb_stat"].iloc[-1])
        pvalue = _num(result["lb_pvalue"].iloc[-1])
        return {
            "stat": round(stat, 4) if stat is not None else None,
            "pValue": round(pvalue, 4) if pvalue is not None else None,
            "passed": pvalue is not None and pvalue > 0.05,
            "detail": (
                "Residuos sin autocorrelación"
                if pvalue is not None and pvalue > 0.05
                else "Los residuos conservan autocorrelación"
            ),
        }
    except Exception as exc:  # pragma: no cover
        return {"stat": None, "pValue": None, "passed": False, "detail": f"Ljung-Box no pudo calcularse: {exc}"}


def jarque_bera_test(residuals: np.ndarray) -> dict[str, Any]:
    """Jarque-Bera: p > 0.05 ⇒ los residuos no se alejan de la normalidad."""
    from statsmodels.stats.stattools import jarque_bera

    values = np.asarray(residuals, dtype=float)
    values = values[np.isfinite(values)]
    if len(values) < 20:
        return {"stat": None, "pValue": None, "passed": False, "detail": "Muestra insuficiente"}
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            stat, pvalue, skew, kurtosis = jarque_bera(values)
        stat = _num(stat)
        pvalue = _num(pvalue)
        return {
            "stat": round(stat, 4) if stat is not None else None,
            "pValue": round(pvalue, 4) if pvalue is not None else None,
            "passed": pvalue is not None and pvalue > 0.05,
            "detail": (
                "Residuos compatibles con normalidad"
                if pvalue is not None and pvalue > 0.05
                else f"Residuos no normales (asimetría {_num(skew) or 0:+.2f}, curtosis {_num(kurtosis) or 0:.2f})"
            ),
        }
    except Exception as exc:  # pragma: no cover
        return {"stat": None, "pValue": None, "passed": False, "detail": f"Jarque-Bera no pudo calcularse: {exc}"}


def arch_lm_test(residuals: np.ndarray, lags: int = 5) -> dict[str, Any]:
    """ARCH-LM: p > 0.05 ⇒ no hay heterocedasticidad condicional."""
    from statsmodels.stats.diagnostic import het_arch

    values = np.asarray(residuals, dtype=float)
    values = values[np.isfinite(values)]
    if len(values) < max(lags + 5, 20):
        return {"stat": None, "pValue": None, "passed": False, "detail": "Muestra insuficiente"}
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            stat, pvalue = het_arch(values, nlags=lags)[:2]
        stat = _num(stat)
        pvalue = _num(pvalue)
        return {
            "stat": round(stat, 4) if stat is not None else None,
            "pValue": round(pvalue, 4) if pvalue is not None else None,
            "passed": pvalue is not None and pvalue > 0.05,
            "detail": (
                "Varianza residual constante"
                if pvalue is not None and pvalue > 0.05
                else "Heterocedasticidad: conviene modelar la volatilidad con GARCH"
            ),
        }
    except Exception as exc:  # pragma: no cover
        return {"stat": None, "pValue": None, "passed": False, "detail": f"ARCH-LM no pudo calcularse: {exc}"}


def decide_differencing(log_price: pd.Series) -> dict[str, Any]:
    """Elige ``d`` con ADF/KPSS y deja escrito el motivo.

    Primero prueba el log-precio; si no es estacionario, prueba la primera
    diferencia (retornos). Si tampoco, usa d=2 como último recurso.
    """
    series = log_price.dropna().astype(float)
    price_adf = adf_test(series)
    price_kpss = kpss_test(series)
    price_stationary = price_adf["passed"] and price_kpss["passed"]

    diff = series.diff().dropna()
    diff_adf = adf_test(diff)
    diff_kpss = kpss_test(diff)
    diff_stationary = diff_adf["passed"] and diff_kpss["passed"]

    if price_stationary:
        d = 0
        reason = (
            "El log-precio es estacionario según ADF y KPSS; no hace falta diferenciar (d=0)."
        )
    elif diff_stationary:
        d = 1
        reason = (
            "El log-precio no es estacionario, pero sus retornos sí lo son; "
            "se aplica una diferencia (d=1)."
        )
    else:
        d = 2
        reason = (
            "Ni el log-precio ni sus retornos superan ADF/KPSS; se usa d=2 como "
            "último recurso y se recomienda revisar la serie."
        )

    return {
        "d": d,
        "priceStationary": price_stationary,
        "diffStationary": diff_stationary,
        "logPriceAdf": price_adf,
        "logPriceKpss": price_kpss,
        "diffAdf": diff_adf,
        "diffKpss": diff_kpss,
        "reason": reason,
    }


def _roots(model: Any) -> tuple[np.ndarray, np.ndarray]:
    try:
        ar_roots = np.abs(np.asarray(model.arroots, dtype=complex))
    except Exception:
        ar_roots = np.array([], dtype=float)
    try:
        ma_roots = np.abs(np.asarray(model.maroots, dtype=complex))
    except Exception:
        ma_roots = np.array([], dtype=float)
    return ar_roots, ma_roots


def arima_diagnostics(
    model: Any,
    stationarity: dict[str, Any],
    mape: float | None,
) -> dict[str, Any]:
    """Resume los supuestos del modelo y explica si es defendible.

    Devuelve un diccionario listo para JSON con pruebas, veredicto y texto.
    """
    residuals = np.asarray(model.resid, dtype=float)
    residuals = residuals[np.isfinite(residuals)]

    white_noise = ljung_box_test(residuals)
    normality = jarque_bera_test(residuals)
    homoscedasticity = arch_lm_test(residuals)

    ar_roots, ma_roots = _roots(model)
    ar_ok = bool(len(ar_roots) == 0 or np.all(np.abs(ar_roots) > 1.0))
    ma_ok = bool(len(ma_roots) == 0 or np.all(np.abs(ma_roots) > 1.0))
    roots_ok = ar_ok and ma_ok

    try:
        # statsmodels devuelve ``pvalues`` como Series en algunas versiones y
        # como ndarray en otras; los nombres viven en ``param_names``.
        has_arma = False
        pvalues = np.asarray(model.pvalues, dtype=float).ravel()
        names = [str(name) for name in getattr(model, "param_names", [])]
        if len(names) != len(pvalues):
            names = [f"param_{i}" for i in range(len(pvalues))]
        arma_positions = [i for i, name in enumerate(names) if ".L" in name]
        has_arma = bool(arma_positions)
        if arma_positions:
            significant = sum(1 for i in arma_positions if pvalues[i] < 0.05)
            coefficients_ok = significant == len(arma_positions)
            coefficient_detail = (
                f"{significant}/{len(arma_positions)} coeficientes AR/MA "
                "significativos (p < 0.05)"
            )
        else:
            coefficients_ok = True
            coefficient_detail = "Sin coeficientes AR/MA que evaluar (modelo sin términos)"
    except Exception:  # pragma: no cover
        coefficients_ok = False
        coefficient_detail = "No se pudieron leer los p-valores"

    stationarity_ok = bool(
        stationarity.get("diffStationary") if stationarity.get("d", 1) > 0 else stationarity.get("priceStationary")
    )
    mape_ok = mape is not None and mape < 0.10

    stationarity_adf = (
        stationarity.get("diffAdf", {}) if stationarity.get("d", 1) > 0 else stationarity.get("logPriceAdf", {})
    )
    stationarity_kpss = (
        stationarity.get("diffKpss", {}) if stationarity.get("d", 1) > 0 else stationarity.get("logPriceKpss", {})
    )

    assumptions = [
        {
            "name": "Estacionariedad",
            "test": "ADF / KPSS",
            "value": (
                f"ADF p={stationarity_adf.get('pValue')} · KPSS p={stationarity_kpss.get('pValue')}"
            ),
            "pValue": stationarity_adf.get("pValue"),
            "passed": stationarity_ok,
            "detail": stationarity.get("reason", ""),
        },
        {
            "name": "Ruido blanco",
            "test": "Ljung-Box",
            "value": f"p={white_noise.get('pValue')}",
            "pValue": white_noise.get("pValue"),
            "passed": white_noise["passed"],
            "detail": white_noise["detail"],
        },
        {
            "name": "Normalidad",
            "test": "Jarque-Bera",
            "value": f"p={normality.get('pValue')}",
            "pValue": normality.get("pValue"),
            "passed": normality["passed"],
            "detail": normality["detail"],
        },
        {
            "name": "Homocedasticidad",
            "test": "ARCH-LM",
            "value": f"p={homoscedasticity.get('pValue')}",
            "pValue": homoscedasticity.get("pValue"),
            "passed": homoscedasticity["passed"],
            "detail": homoscedasticity["detail"],
        },
        {
            "name": "Raíces",
            "test": "AR/MA",
            "value": "fuera del círculo" if roots_ok else "dentro del círculo",
            "pValue": None,
            "passed": roots_ok,
            "detail": (
                "Modelo estable e invertible"
                if roots_ok
                else "Hay raíces dentro del círculo unitario; el modelo puede ser inestable"
            ),
        },
        {
            "name": "Coeficientes",
            "test": "p-valores",
            "value": (
                "significativos"
                if coefficients_ok
                else "no significativos"
            )
            if has_arma
            else "sin términos AR/MA",
            "pValue": None,
            "passed": coefficients_ok,
            "detail": coefficient_detail,
        },
    ]

    critical_ok = stationarity_ok and white_noise["passed"] and roots_ok
    if critical_ok and coefficients_ok:
        verdict = "Sólido" if (normality["passed"] and homoscedasticity["passed"] and mape_ok) else "Aceptable"
    elif critical_ok:
        verdict = "Aceptable"
    else:
        verdict = "Débil"

    caveats: list[str] = []
    if not normality["passed"]:
        caveats.append(
            "Los residuos no son normales; es habitual en retornos financieros y afecta "
            "los intervalos, no la dirección puntual del pronóstico."
        )
    if not homoscedasticity["passed"]:
        caveats.append(
            "Hay heterocedasticidad (ARCH-LM); por eso la volatilidad se estima aparte "
            "con GARCH(1,1)."
        )
    if not white_noise["passed"]:
        caveats.append(
            "Los residuos conservan autocorrelación; el orden puede no capturar toda la "
            "dinámica y el pronóstico debe tomarse con cautela."
        )
    if not roots_ok:
        caveats.append(
            "Hay raíces dentro del círculo unitario; revisa el orden o la ventana de "
            "entrenamiento."
        )
    if not coefficients_ok:
        caveats.append(
            "Algún coeficiente AR/MA no es significativo; un orden más simple podría ser "
            "suficiente."
        )
    if mape is not None and not mape_ok:
        caveats.append(
            f"El MAPE fuera de muestra es {mape * 100:.1f}%; por encima del 10% la "
            "referencia es menos fiable."
        )

    summary_parts = [stationarity.get("reason", "")]
    summary_parts.append(
        "Los residuos no muestran autocorrelación (Ljung-Box)."
        if white_noise["passed"]
        else "Los residuos todavía muestran autocorrelación (Ljung-Box)."
    )
    summary_parts.append(
        "Las raíces están fuera del círculo unitario: el modelo es estable e invertible."
        if roots_ok
        else "Las raíces no están todas fuera del círculo unitario."
    )
    if mape is not None:
        summary_parts.append(f"MAPE fuera de muestra: {mape * 100:.1f}%.")
    summary = " ".join(part for part in summary_parts if part)

    return {
        "verdict": verdict,
        "criticalOk": critical_ok,
        "stationary": stationarity_ok,
        "whiteNoise": white_noise["passed"],
        "normalResiduals": normality["passed"],
        "homoscedastic": homoscedasticity["passed"],
        "rootsOk": roots_ok,
        "coefficientsOk": coefficients_ok,
        "passedCount": sum(1 for item in assumptions if item["passed"]),
        "total": len(assumptions),
        "assumptions": assumptions,
        "caveats": caveats,
        "summary": summary,
    }


__all__ = [
    "adf_test",
    "arch_lm_test",
    "arima_diagnostics",
    "decide_differencing",
    "jarque_bera_test",
    "kpss_test",
    "ljung_box_test",
]
