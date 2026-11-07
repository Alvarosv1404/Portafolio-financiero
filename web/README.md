# Quant Engine Web

Dashboard visual del Motor de Auditoría y Optimización de Portafolios.

## Estado

Demo visual con datos simulados. El motor Python todavía no está conectado a una API; esta interfaz sirve para validar la experiencia antes de pasar el código probado en Jupyter a la web.

## Stack

- Vite
- React 19
- TypeScript
- Recharts
- lucide-react

## Ejecutar

```powershell
cd web
npm install
npm run dev
```

Abre la URL que muestra la terminal, normalmente:

```text
http://localhost:5173
```

## Compilar

```powershell
npm run build
npm run preview
```

## Estructura

```text
web/
├── src/
│   ├── components/       # Paneles, tablas, gráficos y navegación
│   ├── data/mockData.ts  # Datos simulados de la demo
│   ├── App.tsx           # Composición de vistas
│   ├── App.css           # Estilos del dashboard
│   └── main.tsx
├── index.html
└── package.json
```

## Próximo paso

Reemplazar `mockData.ts` por llamadas a una API del motor Python (FastAPI recomendado) con endpoints para:

- resumen del portafolio,
- proveedores y calidad de datos,
- auditoría,
- pronóstico ARIMA,
- optimización Markowitz.

## Aviso

Los datos son simulados. No constituyen asesoría financiera.
