# Motor de Auditoría y Optimización de Portafolios

Herramienta cuantitativa en Python para el filtrado, auditoría y evaluación automática de activos financieros mediante series de tiempo (ARIMA) y algoritmos de selección de portafolios eficientes (Markowitz), usando datos públicos.

> Proyecto en construcción. El objetivo es tener una base reproducible, testeable y con una capa de datos desacoplada de los proveedores.

## Estado actual

- [x] Estructura base del paquete `quant_engine`.
- [x] Configuración central con `.env` y `.env.example`.
- [x] Lectura del universo de activos desde Excel.
- [x] Descarga histórica con yfinance.
- [x] Notebooks de exploración (sin credenciales hardcodeadas).
- [x] Capa de datos con yfinance, limpieza y caché en disco.
- [x] Auditoría de calidad (gaps, outliers, cobertura, movimientos extremos).
- [x] Markowitz: máximo Sharpe y frontera eficiente con restricciones.
- [x] ARIMA sobre el portafolio con validación fuera de muestra.
- [x] ARIMA por activo con ADF/KPSS, Ljung-Box, Jarque-Bera, ARCH-LM, raíces y MAPE.
- [x] 5 carteras sobre la misma frontera (bajo riesgo, moderado, ideal, riesgoso y total).
- [x] Top 10 por score compuesto y reoptimización de la cartera.
- [x] Simulador de inversión con acciones enteras y efectivo residual.
- [x] GARCH(1,1) para la cartera y para cada activo del Top 10.
- [x] Señales de compra/venta combinando μ/σ, momentum y ARIMA.
- [x] API FastAPI y dashboard web conectado.
- [x] Dashboard accesible por Tailscale.
- [ ] Comparación automática entre proveedores alternativos.
- [ ] Backtest walk-forward (out-of-sample real).
- [ ] Proveedor Excel/CSV para datos manuales (Perú y derivados).
- [ ] Autenticación si se expone fuera de la red privada.

## Requisitos

- Python 3.11 o superior.
- Node.js 20 o superior (para el dashboard web).
- Git.- Windows, macOS o Linux.

## Instalación

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -e ".[dev,providers,api]"
```

En Linux/macOS:

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -e ".[dev,providers,api]"
```

## Configuración de credenciales

1. Copia la plantilla:

```powershell
Copy-Item config/.env.example config/.env
```

2. Completa las claves en `config/.env`.
3. Nunca subas `config/.env` a GitHub. Ya está en `.gitignore`.

Uso desde Python:

```python
from quant_engine.config import get_settings

settings = get_settings()
token = settings.require("finnhub_api_key")
```

Variables disponibles:

| Variable | Uso |
|---|---|
| `ALPHA_VANTAGE_API_KEY` | Pruebas puntuales (plan gratuito muy limitado) |
| `TWELVE_DATA_API_KEY` | Proveedor secundario / fallback |
| `FINNHUB_API_KEY` | Cotizaciones en tiempo real y websocket (EE. UU.) |
| `MARKETSTACK_API_KEY` | Datos EOD secundarios |
| `TIINGO_API_KEY` | Validación de datos EOD |
| `IPSTACK_API_KEY` | Geolocalización de IPs (no es dato de mercado) |
| `DEFAULT_DATA_PROVIDER` | `yfinance`, `finnhub`, `twelvedata`, etc. |
| `DATA_CACHE_DIR` | Carpeta de caché local |
| `REQUEST_TIMEOUT` | Timeout HTTP en segundos |

## Estructura

```text
.
├── config/
│   ├── .env.example          # plantilla versionada
│   └── SP500_yfinance.xlsx   # universo de activos
├── notebooks/
│   ├── Pruebas_de_importacion.ipynb
│   ├── portafolio.ipynb
│   └── Ideal portafolio.ipynb
├── src/quant_engine/
│   ├── config.py             # configuración tipada
│   ├── universe.py           # universo y metadatos de activos
│   ├── service.py            # descarga, cálculo y payload del dashboard
│   ├── analytics/
│   │   ├── stats.py          # retornos, volatilidad, drawdown
│   │   ├── optimization.py   # máximo Sharpe, mínima varianza y frontera
│   │   ├── portfolio.py      # perfiles, Top 10 e inversión
│   │   ├── diagnostics.py    # ADF/KPSS, Ljung-Box, Jarque-Bera, ARCH-LM
│   │   ├── volatility.py     # GARCH(1,1) de cartera y activos
│   │   ├── signals.py        # señales de compra/venta
│   │   └── forecast.py       # ARIMA, bandas y proyecciones
│   ├── audit/quality.py      # controles de calidad de datos
│   ├── api/app.py            # API FastAPI
│   └── ingestion/
│       ├── base_provider.py  # contrato DataProvider
│       └── dt_yfinance.py    # adaptador yfinance
├── tests/
├── web/                      # dashboard React + Vite
├── pyproject.toml
└── requirements.txt
```

## Uso rápido

```python
import pandas as pd

from quant_engine.ingestion.dt_yfinance import cargar_universo, cierre_sect_yf

universo = cargar_universo("config/SP500_yfinance.xlsx")
finanzas = cierre_sect_yf(universo, "Financials", "2023-02-01", "2023-09-01")
finanzas.head()
```

## API del motor

Terminal 1, desde la raíz:

```powershell
.\.venv\Scripts\Activate.ps1
python -m uvicorn quant_engine.api.app:app --host 0.0.0.0 --port 8000
```

Endpoints:

| Endpoint | Uso |
|---|---|
| `GET /api/health` | Estado del servicio |
| `GET /api/universe` | Universo por defecto y benchmark |
| `GET /api/dashboard` | Dashboard completo calculado con datos reales |

Parámetros de `/api/dashboard`:

- `refresh=true`: ignora la caché de 15 minutos.
- `tickers=AAPL,MSFT,...`: universo personalizado.
- `start`, `end`: ventana histórica en ISO.
- `max_weight`: tope por activo (por defecto `0.18`).
- `risk_free`: tasa libre de riesgo anual (por defecto `0.04`).
- `capital`: capital simulado para el KPI de valor (por defecto `100000`).

Si yfinance falla, la API devuelve la última copia guardada en `data/cache/dashboard.json` y marca `meta.stale = true`.

## Dashboard web

Terminal 2:

```powershell
cd web
npm install
npm run dev
```

Abre `http://localhost:5173` (si el puerto está ocupado, Vite usa el siguiente y lo muestra en consola). Vistas incluidas: Resumen, Datos, Auditoría, ARIMA, Markowitz, Carteras, Top 10, Inversión, Señales y GARCH. La web consume `/api/dashboard` a través del proxy de Vite y refresca cada 5 minutos.

| Vista | Qué muestra |
|---|---|
| Carteras | Los 5 perfiles con pesos, retorno esperado, volatilidad y Sharpe |
| Top 10 | Score compuesto y la cartera reoptimizada con esos 10 activos |
| Inversión | Acciones enteras comprables, efectivo residual y valor a 1/3/6 meses |
| Señales | Avisos por activo combinando μ/σ, momentum y veredicto ARIMA |
| ARIMA | Pronóstico del portafolio y diagnóstico individual por activo |
| GARCH | Volatilidad condicional de la cartera Top 10 y de cada activo |

### Abrir desde otro dispositivo (Tailscale)

Vite escucha en todas las interfaces. Obtén la IP privada:

```powershell
tailscale ip -4
```

Y abre desde tu otro equipo o teléfono:

```text
http://<IP-TAILSCALE>:5173
```

La API no se expone aparte: Vite proxya `/api` hacia `127.0.0.1:8000`. Mantén el acceso dentro de tu tailnet; no publiques el puerto a Internet.

### Qué se calcula de verdad

1. yfinance descarga cierres ajustados de 20 activos + SPY (3 años).
2. Se limpian precios, se calculan retornos logarítmicos y la covarianza anualizada con contracción.
3. Markowitz maximiza el Sharpe (suma 1, sin cortos, tope por activo) y genera la frontera eficiente.
4. Sobre esa misma frontera se construyen 5 perfiles: mínima varianza, volatilidad intermedia, máximo Sharpe, máximo retorno y la unión de los cuatro.
5. El Top 10 combina peso promedio en los perfiles, Sharpe individual y momentum de 6 meses; luego se reoptimiza a máximo Sharpe.
6. La inversión usa acciones enteras: `piso(monto / precio)`, efectivo residual y proyección con el retorno mensual del activo.
7. ARIMA se ajusta por activo: `d` se decide con ADF/KPSS, `p` y `q` por AIC, y se reportan supuestos, veredicto y MAPE fuera de muestra.
8. GARCH(1,1) estima la volatilidad condicional anualizada del activo y de la cartera (retornos `R × w`).
9. Las señales combinan μ/σ a 21 días, momentum y el veredicto ARIMA; son consejos, no órdenes.
10. La auditoría revisa gaps contra el calendario real de SPY, nulos, precios inválidos, outliers y movimientos extremos.

> Limitación actual: la performance es **in-sample**, porque los pesos se estiman con el mismo periodo que se evalúa. El siguiente paso es un backtest walk-forward. Los datos son educativos y no constituyen asesoría financiera.

## Tests

```powershell
pytest
```

Cubren configuración, ingesta, estadística, optimización, auditoría, ARIMA y el payload del servicio con precios sintéticos (sin depender de la red).

## Proveedores de datos

| Proveedor | Rol recomendado | Limitación |
|---|---|---|
| yfinance | Histórico masivo y prototipos | No oficial, datos delayed, sin SLA |
| Finnhub | Tiempo real y websocket | Solo mercado de EE. UU. |
| Twelve Data | Fallback y activos múltiples | Rate limit en plan gratuito |
| Tiingo | Validación EOD | Plan gratuito limitado |
| Alpha Vantage | Pruebas puntuales | 25 requests/día |
| Marketstack | EOD secundario | Plan gratuito muy limitado |
| Excel/CSV | Perú y derivados | Requiere validación manual |

## Seguridad

- Las credenciales viven en `config/.env`, que está ignorado por git.
- `config/.env.example` solo contiene placeholders.
- **Borrar una rama no elimina los commits del historial de GitHub.** Si una clave estuvo commiteada, debe considerarse comprometida y rotarse en el panel del proveedor.
- Para producción, usa un gestor de secretos (GitHub Actions Secrets, 1Password, Doppler, AWS Secrets Manager, etc.).
- Activa GitHub Secret Scanning y push protection si el repositorio lo permite.

## Aviso

Este proyecto usa datos públicos y tiene fines educativos/de investigación. No constituye asesoría financiera. yfinance no es una fuente oficial ni tiene garantía de disponibilidad.
