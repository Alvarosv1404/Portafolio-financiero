from __future__ import annotations

import numpy as np
import pandas as pd

from quant_engine.audit import audit_prices


def test_audit_detects_gaps_nulls_and_invalid_prices() -> None:
    dates = pd.bdate_range("2024-01-02", periods=30)
    rng = np.random.default_rng(3)
    base = 100 * np.exp(np.cumsum(rng.normal(0, 0.005, size=(30, 2)), axis=0))
    raw = pd.DataFrame(base, index=dates, columns=["AAA", "BBB"])

    raw.iloc[10, 0] = np.nan
    raw.iloc[12, 1] = 0.0
    gap_date = dates[15]
    raw = raw.drop(index=gap_date)

    result = audit_prices(raw, calendar=dates)

    assert result["missingDays"] == 1
    assert result["missingCells"] >= 1
    assert result["duplicatedDates"] == 0
    invalid = next(check for check in result["checks"] if check["name"] == "Precios inválidos")
    assert invalid["status"] != "ok"
    gaps = next(check for check in result["checks"] if check["name"] == "Gaps de fechas")
    assert gaps["value"] == "1"
    assert any(issue["type"] == "Gap de fechas" for issue in result["issues"])


def test_audit_flags_extreme_moves() -> None:
    dates = pd.bdate_range("2024-01-02", periods=40)
    prices = np.full((40, 2), 100.0)
    prices[:, 1] += np.linspace(0, 5, 40)
    prices[20, 0] = 200.0
    raw = pd.DataFrame(prices, index=dates, columns=["AAA", "BBB"])

    result = audit_prices(raw, calendar=dates)

    assert result["largeMoves"] >= 1
    assert result["outliers"] >= 1
