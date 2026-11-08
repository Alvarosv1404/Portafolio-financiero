"""Paquete de analítica cuantitativa."""

from .forecast import forecast_asset_arima, forecast_portfolio
from .diagnostics import (
    adf_test,
    arch_lm_test,
    arima_diagnostics,
    decide_differencing,
    jarque_bera_test,
    kpss_test,
    ljung_box_test,
)
from .optimization import (
    efficient_frontier,
    max_return_weights,
    max_sharpe_weights,
    min_variance_weights,
    target_volatility_weights,
)
from .signals import combined_signal, asset_signal_from_rows
from .volatility import garch_volatility, portfolio_volatility_path
from .portfolio import (
    profile_weights,
    select_top10,
    candidate_score,
    total_profile_union,
    InvestmentResult,
    compute_investment,
)
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
    "max_return_weights",
    "max_sharpe_weights",
    "min_variance_weights",
    "target_volatility_weights",
    "forecast_asset_arima",
    "forecast_portfolio",
    "adf_test",
    "arch_lm_test",
    "arima_diagnostics",
    "decide_differencing",
    "jarque_bera_test",
    "kpss_test",
    "ljung_box_test",
    "max_drawdown",
    "sharpe_ratio",
    "to_log_returns",
    "year_to_date_return",
    "combined_signal",
    "asset_signal_from_rows",
    "garch_volatility",
    "portfolio_volatility_path",
    "profile_weights",
    "select_top10",
    "candidate_score",
    "total_profile_union",
    "InvestmentResult",
    "compute_investment",
]
