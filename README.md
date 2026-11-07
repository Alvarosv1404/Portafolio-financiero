# Motor de Auditoría y Optimización de Portafolios

Herramienta cuantitativa en Python para el filtrado, auditoría y evaluación automática de activos financieros mediante series de tiempo (ARIMA) y algoritmos de selección de portafolios eficientes (Markowitz), usando datos públicos.

> Proyecto en construcción. El objetivo es tener una base reproducible, testeable y con una capa de datos desacoplada de los proveedores.

## Estado actual

- [x] Estructura base del paquete `quant_engine`.
- [x] Configuración central con `.env` y `.env.example`.
- [x] Lectura del universo de activos desde Excel.
- [x] Descarga histórica con yfinance.
- [x] Notebooks de exploración (sin credenciales hardcodeadas).
- [x] Dashboard web demo con React + Vite (datos simulados).
- [ ] Capa de proveedores intercambiables y caché local.
- [ ] Comparación de proveedores y auditoría de calidad de datos.
- [ ] ARIMA con validación walk-forward.
- [ ] Markowitz con restricciones y backtest.
- [ ] Proveedor Excel/CSV para datos manuales (Perú y derivados).

## Requisitos

- Python 3.11 o superior.
- Node.js 20 o superior (para el dashboard web).
- Git.
- Windows, macOS o Linux.

## Instalación

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -e ".[dev,providers]"
```

En Linux/macOS:

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -e ".[dev,providers]"
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
│   └── ingestion/
│       ├── base_provider.py  # contrato DataProvider
│       └── dt_yfinance.py    # adaptador yfinance
├── tests/
├── web/                      # dashboard React + Vite (demo)
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

## Dashboard web

La idea del producto se puede navegar desde ya con datos simulados, mientras el motor Python se prueba en Jupyter.

```powershell
cd web
npm install
npm run dev
```

Abre `http://localhost:5173`. Vistas incluidas: Resumen, Datos, Auditoría, ARIMA y Markowitz.

> La web es una demo visual: `web/src/data/mockData.ts` contiene datos de ejemplo. Todavía no consume el motor Python. El siguiente paso es exponer el motor con una API (FastAPI recomendado) y reemplazar los datos simulados por respuestas reales.

## Tests

```powershell
pytest
```

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
