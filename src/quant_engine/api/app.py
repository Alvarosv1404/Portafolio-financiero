"""API HTTP del motor cuantitativo."""

from __future__ import annotations

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware

from ..service import build_dashboard, load_cached_payload
from ..universe import BENCHMARK, DEFAULT_UNIVERSE

app = FastAPI(
    title="Quant Engine API",
    version="0.1.0",
    description="Motor de auditoría y optimización de portafolios con datos públicos.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "quant-engine", "version": "0.1.0"}


@app.get("/api/universe")
def universe() -> dict:
    return {"benchmark": BENCHMARK, "tickers": DEFAULT_UNIVERSE, "count": len(DEFAULT_UNIVERSE)}


@app.get("/api/dashboard")
def dashboard(
    refresh: bool = Query(False, description="Ignora la caché y vuelve a descargar."),
    tickers: str | None = Query(None, description="Lista separada por comas. Por defecto, 20 activos."),
    start: str | None = Query(None, description="Fecha inicial ISO (YYYY-MM-DD)."),
    end: str | None = Query(None, description="Fecha final ISO (YYYY-MM-DD)."),
    max_weight: float = Query(0.18, gt=0, le=1, description="Peso máximo por activo."),
    risk_free: float = Query(0.04, ge=0, le=1, description="Tasa libre de riesgo anual."),
    capital: float = Query(100_000, gt=0, description="Capital simulado."),
) -> dict:
    selected = None
    if tickers:
        selected = [item.strip().upper() for item in tickers.split(",") if item.strip()]

    try:
        return build_dashboard(
            tickers=selected,
            start=start,
            end=end,
            max_weight=max_weight,
            risk_free=risk_free,
            capital=capital,
            refresh=refresh,
        )
    except Exception as exc:
        cached = load_cached_payload()
        if cached is not None:
            return cached
        raise HTTPException(status_code=503, detail=str(exc)) from exc


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("quant_engine.api.app:app", host="0.0.0.0", port=8000, reload=False)
