"""Paquete de analítica cuantitativa."""

from .forecast import forecast_portfolio
from .optimization import efficient_frontier, max_sharpe_weights
from .stats import (
    annualized_covariance,
    annualized_mean,
    annualized_return,
    annualized_volatility,
    cumulative_index,
    max_drawdown,
    sharpe_ratio,
    to_log_returns,
    year_to_date_return,
)

__all__ = [
    "annualized_covariance",
    "annualized_mean",
    "annualized_return",
    "annualized_volatility",
    "cumulative_index",
    "efficient_frontier",
    "forecast_portfolio",
    "max_drawdown",
    "max_sharpe_weights",
    "sharpe_ratio",
    "to_log_returns",
    "year_to_date_return",
]
