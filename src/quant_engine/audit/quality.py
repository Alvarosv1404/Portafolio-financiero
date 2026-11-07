"""Auditoría de calidad sobre la matriz de precios descargada."""

from __future__ import annotations

import numpy as np
import pandas as pd


def _severity_from_count(count: int) -> str:
    if count == 0:
        return "ok"
    if count <= 3:
        return "warning"
    return "danger"


def audit_prices(
    raw: pd.DataFrame,
    calendar: pd.DatetimeIndex | None = None,
    max_issues: int = 8,
) -> dict:
    """Ejecuta controles de calidad y devuelve chequeos e incidencias.

    ``raw`` debe ser la matriz de cierres tal como llegó del proveedor, con
    ``NaN`` en los días sin cotización. ``calendar`` permite comparar contra
    los días reales de mercado (por ejemplo, el índice del benchmark) en vez
    de contar feriados como gaps.
    """
    if raw.empty:
        raise ValueError("No hay precios para auditar.")

    rows, columns = raw.shape
    duplicated_dates = int(raw.index.duplicated().sum())
    non_positive = int((raw <= 0).sum().sum())
    missing_cells = int(raw.isna().sum().sum())
    total_cells = rows * columns
    coverage = 1 - (missing_cells / total_cells) if total_cells else 0.0

    expected_days = pd.DatetimeIndex(calendar) if calendar is not None else pd.bdate_range(
        raw.index.min(), raw.index.max()
    )
    expected_days = expected_days[(expected_days >= raw.index.min()) & (expected_days <= raw.index.max())]
    missing_days = int(len(expected_days.difference(raw.index)))
    missing_dates = list(expected_days.difference(raw.index))[:3]

    positive = raw.where(raw > 0)
    returns = np.log(positive).diff()
    standardized = (returns - returns.mean()) / returns.std(ddof=0)
    outliers = standardized.abs() > 4
    outlier_count = int(outliers.sum().sum())

    large_moves = returns.abs() > 0.35
    large_move_count = int(large_moves.sum().sum())

    checks = [
        {
            "name": "Duplicados",
            "value": str(duplicated_dates),
            "status": _severity_from_count(duplicated_dates),
            "detail": "Sin fechas repetidas" if duplicated_dates == 0 else "Fechas repetidas en el índice",
        },
        {
            "name": "Precios inválidos",
            "value": str(non_positive),
            "status": _severity_from_count(non_positive),
            "detail": "Sin valores <= 0" if non_positive == 0 else "Precios nulos o negativos",
        },
        {
            "name": "Gaps de fechas",
            "value": str(missing_days),
            "status": _severity_from_count(missing_days),
            "detail": (
                "Calendario bursátil completo"
                if missing_days == 0
                else f"{missing_days} días de mercado sin fila"
            ),
        },
        {
            "name": "Outliers",
            "value": str(outlier_count),
            "status": _severity_from_count(outlier_count),
            "detail": "Retornos dentro de 4σ" if outlier_count == 0 else "Retornos mayores a 4σ",
        },
        {
            "name": "Movimientos > 35%",
            "value": str(large_move_count),
            "status": _severity_from_count(large_move_count),
            "detail": "Sin saltos sospechosos" if large_move_count == 0 else "Revisar splits o errores",
        },
        {
            "name": "Cobertura",
            "value": f"{coverage * 100:.1f}%",
            "status": "ok" if coverage >= 0.95 else "warning" if coverage >= 0.85 else "danger",
            "detail": f"{total_cells - missing_cells} / {total_cells} celdas con precio",
        },
    ]

    issues: list[dict[str, str]] = []
    for date in missing_dates:
        issues.append(
            {
                "id": f"GAP-{len(issues) + 1:03d}",
                "ticker": "—",
                "type": "Gap de fechas",
                "severity": "Media",
                "detail": "Día de mercado sin fila en la matriz",
                "date": date.strftime("%Y-%m-%d"),
            }
        )

    if outlier_count:
        stacked = outliers.stack()
        flagged = stacked[stacked].index.tolist()
        for date, ticker in flagged[: max(0, max_issues - len(issues))]:
            z_value = float(standardized.loc[date, ticker])
            issues.append(
                {
                    "id": f"OUT-{len(issues) + 1:03d}",
                    "ticker": str(ticker),
                    "type": "Outlier de retorno",
                    "severity": "Baja",
                    "detail": f"Retorno {z_value:+.1f}σ respecto a su media",
                    "date": pd.Timestamp(date).strftime("%Y-%m-%d"),
                }
            )

    if large_move_count:
        stacked = large_moves.stack()
        flagged = stacked[stacked].index.tolist()
        for date, ticker in flagged[: max(0, max_issues - len(issues))]:
            move = float(returns.loc[date, ticker])
            issues.append(
                {
                    "id": f"MOV-{len(issues) + 1:03d}",
                    "ticker": str(ticker),
                    "type": "Movimiento extremo",
                    "severity": "Media",
                    "detail": f"Variación diaria de {move * 100:+.1f}%",
                    "date": pd.Timestamp(date).strftime("%Y-%m-%d"),
                }
            )

    return {
        "checks": checks,
        "issues": issues[:max_issues],
        "coverage": round(coverage, 4),
        "missingDays": missing_days,
        "missingCells": missing_cells,
        "duplicatedDates": duplicated_dates,
        "outliers": outlier_count,
        "largeMoves": large_move_count,
    }


__all__ = ["audit_prices"]
