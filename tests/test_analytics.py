from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from quant_engine.analytics import (
    annualized_covariance,
    annualized_mean,
    annualized_return,
    cumulative_index,
    efficient_frontier,
    forecast_portfolio,
    max_drawdown,
    max_sharpe_weights,
    sharpe_ratio,
    to_log_returns,
    year_to_date_return,
)


def synthetic_prices(rows: int = 300, columns: int = 4, seed: int = 7) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    dates = pd.bdate_range("2023-01-02", periods=rows)
    returns = rng.normal(0.0004, 0.01, size=(rows, columns))
    prices = 100 * np.exp(np.cumsum(returns, axis=0))
    return pd.DataFrame(prices, index=dates, columns=[f"T{index}" for index in range(columns)])


def test_log_returns_have_expected_shape() -> None:
    prices = synthetic_prices()
    returns = to_log_returns(prices)
    assert returns.shape == (len(prices) - 1, prices.shape[1])
    assert np.isfinite(returns.to_numpy()).all()


def test_covariance_is_symmetric_and_shrunk() -> None:
    returns = to_log_returns(synthetic_prices())
    sample = annualized_covariance(returns, shrinkage=0.0)
    shrunk = annualized_covariance(returns, shrinkage=0.5)
    assert np.allclose(sample.to_numpy(), sample.to_numpy().T)
    assert np.allclose(shrunk.to_numpy(), shrunk.to_numpy().T)
    # La contracción reduce la magnitud de las covarianzas fuera de la diagonal.
    assert np.abs(shrunk.to_numpy()).sum() < np.abs(sample.to_numpy()).sum()


def test_optimizer_respects_bounds_and_budget() -> None:
    returns = to_log_returns(synthetic_prices())
    mu = annualized_mean(returns)
    covariance = annualized_covariance(returns)
    weights = max_sharpe_weights(mu, covariance, risk_free=0.04, max_weight=0.4)
    assert weights.sum() == pytest.approx(1.0, abs=1e-8)
    assert (weights >= -1e-9).all()
    assert (weights <= 0.4 + 1e-8).all()


def test_frontier_is_sorted_and_non_empty() -> None:
    returns = to_log_returns(synthetic_prices())
    mu = annualized_mean(returns)
    covariance = annualized_covariance(returns)
    frontier = efficient_frontier(mu, covariance, max_weight=0.5, points=8)
    assert len(frontier) >= 3
    risks = [row["risk"] for row in frontier]
    assert risks == sorted(risks)
    assert all(row["risk"] > 0 for row in frontier)


def test_portfolio_metrics_are_consistent() -> None:
    prices = synthetic_prices(rows=400, columns=3)
    returns = prices.pct_change().dropna().mean(axis=1)
    index = cumulative_index(returns)
    assert annualized_return(index) == pytest.approx(
        (index.iloc[-1] / index.iloc[0]) ** (252 / (len(index) - 1)) - 1
    )
    assert max_drawdown(index) <= 0
    assert isinstance(year_to_date_return(index), float)
    assert sharpe_ratio(0.1, 0.2, 0.04) == pytest.approx(0.3)


def test_forecast_returns_monthly_rows() -> None:
    prices = synthetic_prices(rows=320, columns=1)
    index = prices.iloc[:, 0] / prices.iloc[0, 0] * 100
    result = forecast_portfolio(index, horizon_days=63, history_months=6, order=(1, 1, 1))
    assert result.rows
    assert any(row["actual"] is not None for row in result.rows)
    assert any(row["forecast"] is not None for row in result.rows)
    assert result.horizon_months >= 1
    assert result.model.startswith("ARIMA")
