"""Universo por defecto y metadatos de los activos."""

from __future__ import annotations

BENCHMARK = "SPY"

# 20 activos líquidos del S&P 500, suficientes para que la optimización sea
# rápida y la descarga de yfinance estable.
DEFAULT_UNIVERSE: list[str] = [
    "AAPL",
    "MSFT",
    "NVDA",
    "AVGO",
    "JPM",
    "LLY",
    "UNH",
    "AMZN",
    "TSLA",
    "GOOGL",
    "META",
    "XOM",
    "CVX",
    "CAT",
    "GE",
    "KO",
    "PEP",
    "NEE",
    "LIN",
    "PLD",
]

SECTORS: dict[str, str] = {
    "AAPL": "Information Technology",
    "MSFT": "Information Technology",
    "NVDA": "Information Technology",
    "AVGO": "Information Technology",
    "JPM": "Financials",
    "LLY": "Health Care",
    "UNH": "Health Care",
    "AMZN": "Consumer Discretionary",
    "TSLA": "Consumer Discretionary",
    "GOOGL": "Communication Services",
    "META": "Communication Services",
    "XOM": "Energy",
    "CVX": "Energy",
    "CAT": "Industrials",
    "GE": "Industrials",
    "KO": "Consumer Staples",
    "PEP": "Consumer Staples",
    "NEE": "Utilities",
    "LIN": "Materials",
    "PLD": "Real Estate",
}

NAMES: dict[str, str] = {
    "AAPL": "Apple",
    "MSFT": "Microsoft",
    "NVDA": "NVIDIA",
    "AVGO": "Broadcom",
    "JPM": "JPMorgan Chase",
    "LLY": "Eli Lilly",
    "UNH": "UnitedHealth",
    "AMZN": "Amazon",
    "TSLA": "Tesla",
    "GOOGL": "Alphabet",
    "META": "Meta Platforms",
    "XOM": "Exxon Mobil",
    "CVX": "Chevron",
    "CAT": "Caterpillar",
    "GE": "GE Aerospace",
    "KO": "Coca-Cola",
    "PEP": "PepsiCo",
    "NEE": "NextEra Energy",
    "LIN": "Linde",
    "PLD": "Prologis",
}

SECTOR_COLORS: dict[str, str] = {
    "Information Technology": "#2dd4bf",
    "Financials": "#38bdf8",
    "Health Care": "#818cf8",
    "Consumer Discretionary": "#a78bfa",
    "Industrials": "#fbbf24",
    "Communication Services": "#fb7185",
    "Consumer Staples": "#34d399",
    "Utilities": "#22d3ee",
    "Materials": "#f472b6",
    "Energy": "#f59e0b",
    "Real Estate": "#94a3b8",
}

SECTOR_SHORT: dict[str, str] = {
    "Information Technology": "Tech",
    "Financials": "Finanzas",
    "Health Care": "Salud",
    "Consumer Discretionary": "Consumo",
    "Industrials": "Industrial",
    "Communication Services": "Comunicación",
    "Consumer Staples": "Staples",
    "Utilities": "Utilities",
    "Materials": "Materiales",
    "Energy": "Energía",
    "Real Estate": "Real Estate",
}

__all__ = [
    "BENCHMARK",
    "DEFAULT_UNIVERSE",
    "NAMES",
    "SECTORS",
    "SECTOR_COLORS",
    "SECTOR_SHORT",
]
