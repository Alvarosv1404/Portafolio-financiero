from __future__ import annotations

import pandas as pd
import pytest

from quant_engine.ingestion import DataProvider
from quant_engine.ingestion.dt_yfinance import cargar_universo, cierre_sect_yf


def test_data_provider_is_abstract():
    with pytest.raises(TypeError):
        DataProvider()


def test_cargar_universo(tmp_path):
    path = tmp_path / "universo.xlsx"
    pd.DataFrame(
        {
            "Ticket": ["AAPL", "MSFT"],
            "Nombre": ["Apple", "Microsoft"],
            "Sector": ["Information Technology", "Information Technology"],
        }
    ).to_excel(path, index=False)

    universo = cargar_universo(path)

    assert list(universo.columns) == ["Ticket", "Nombre", "Sector"]
    assert len(universo) == 2
    assert universo["Ticket"].tolist() == ["AAPL", "MSFT"]


def test_cierre_sect_yf_filtra_por_sector(monkeypatch):
    universo = pd.DataFrame(
        {
            "Ticket": ["AAA", "BBB", "CCC"],
            "Sector": ["Financials", "Financials", "Energy"],
        }
    )
    capturado = {}

    def fake_download(tickers, start, end):
        capturado["tickers"] = tickers
        return pd.DataFrame({"Close": [1.0], "Open": [1.0]})

    monkeypatch.setattr("quant_engine.ingestion.dt_yfinance.yf.download", fake_download)

    resultado = cierre_sect_yf(universo, "Financials", "2024-01-01", "2024-02-01")

    assert capturado["tickers"] == ["AAA", "BBB"]
    assert list(resultado.columns) == ["Close", "Open"]
