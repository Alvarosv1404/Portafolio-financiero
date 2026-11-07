from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from quant_engine import service


@pytest.fixture()
def synthetic_market() -> pd.DataFrame:
    dates = pd.bdate_range("2023-01-02", periods=420)
    rng = np.random.default_rng(11)
    columns = ["AAPL", "MSFT", "NVDA", "JPM", "SPY"]
    returns = rng.normal(0.0003, 0.009, size=(len(dates), len(columns)))
    prices = 100 * np.exp(np.cumsum(returns, axis=0))
    return pd.DataFrame(prices, index=dates, columns=columns)


def test_build_dashboard_with_injected_prices(monkeypatch, synthetic_market, tmp_path) -> None:
    monkeypatch.setattr(service, "fetch_prices", lambda tickers, start, end: synthetic_market)
    monkeypatch.setattr(service, "_cache_file", lambda: tmp_path / "dashboard.json")
    service._CACHE.clear()

    payload = service.build_dashboard(
        tickers=["AAPL", "MSFT", "NVDA", "JPM"],
        max_weight=0.4,
        refresh=True,
    )

    assert payload["meta"]["isLive"] is True
    assert payload["meta"]["universeSize"] == 4
    assert payload["metrics"]["universeSize"] == 4
    assert payload["metrics"]["portfolioValue"] > 0
    assert payload["performance"]
    assert abs(sum(row["weight"] for row in payload["assets"]) - 100) < 0.6
    assert payload["auditChecks"]
    assert payload["auditSummary"]["coverage"] > 0
    assert payload["forecast"]["series"]
    assert payload["frontier"]
    assert payload["assetRiskReturn"]
    assert payload["allocation"]
    assert payload["optimization"]["positions"] >= 1
    assert "in-sample" in " ".join(payload["meta"]["warnings"])


def test_dashboard_rejects_empty_universe() -> None:
    with pytest.raises(ValueError):
        service.build_dashboard(tickers=[], refresh=True)
