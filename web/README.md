# Quant Engine Web

Dashboard del Motor de Auditoría y Optimización de Portafolios. Consume la API de Python y muestra precios reales de yfinance, la frontera de Markowitz y el pronóstico ARIMA.

## Estado

Conectado al motor Python. Si la API no responde, la interfaz cae automáticamente a datos de respaldo y lo indica en pantalla.

## Stack

- Vite
- React 19
- TypeScript
- Recharts
- lucide-react

## Ejecutar en local

Primero la API (desde la raíz del proyecto):

```powershell
.\.venv\Scripts\Activate.ps1
python -m uvicorn quant_engine.api.app:app --host 0.0.0.0 --port 8000
```

En otra terminal, la web:

```powershell
cd web
npm install
npm run dev
```

Abre `http://localhost:5173`.

## Abrir desde otro dispositivo con Tailscale

Vite ya escucha en todas las interfaces (`server.host = true`) y hace proxy de `/api` hacia la API local. Solo necesitas la IP de Tailscale de tu PC:

```powershell
tailscale ip -4
```

Luego abre desde el otro dispositivo:

```text
http://<IP-TAILSCALE>:5173
```

Ejemplo: `http://100.70.90.19:5173`.

La API no necesita exponerse aparte: Vite la proxya internamente. No abras el puerto a Internet; usa la red privada de Tailscale.

## Variables

- `VITE_API_URL`: opcional. Por defecto usa `/api/dashboard` (proxy de Vite).

## Scripts

```powershell
npm run dev       # desarrollo con HMR
npm run build     # compilación de producción
npm run lint      # oxlint
npm run preview   # sirve la build
```

## Estructura

```text
web/
├── src/
│   ├── components/           # Paneles, tablas, gráficos y navegación
│   ├── data/
│   │   ├── DashboardContext.tsx  # fetch a la API + refresco automático
│   │   ├── types.ts              # contrato de datos del backend
│   │   ├── mockData.ts           # respaldo visual
│   │   └── mockDashboard.ts
│   ├── App.tsx
│   ├── App.css
│   └── main.tsx
├── vite.config.ts            # host + proxy /api
└── package.json
```

## Comportamiento

- Descarga inicial al abrir la página; refresco automático cada 5 minutos.
- Botón de actualización en la barra superior (fuerza recálculo con `refresh=true`).
- Indicador "Datos reales" / "Demo" según el estado de la API.
- Si yfinance falla, la API devuelve la última copia guardada en `data/cache/dashboard.json`.

## Aviso

Los cálculos son educativos y la performance es in-sample (los pesos se estiman con el mismo periodo que se evalúa). No constituye asesoría financiera.
