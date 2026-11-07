import { useState } from 'react'
import {
  Activity,
  Gauge,
  Layers,
  ShieldAlert,
  Sparkles,
  TrendingUp,
  Wallet,
} from 'lucide-react'
import { Sidebar } from './components/Sidebar'
import type { View } from './components/Sidebar'
import { Topbar } from './components/Topbar'
import { KpiCard } from './components/KpiCard'
import { PerformanceChart } from './components/PerformanceChart'
import { SectorChart } from './components/SectorChart'
import { AssetsTable } from './components/AssetsTable'
import { ProviderGrid } from './components/ProviderGrid'
import { ProviderComparison } from './components/ProviderComparison'
import { AuditPanel } from './components/AuditPanel'
import { ForecastPanel } from './components/ForecastPanel'
import { OptimizationPanel } from './components/OptimizationPanel'
import { UploadPanel } from './components/UploadPanel'
import { SectionHeader } from './components/SectionHeader'
import { StatusBadge } from './components/StatusBadge'
import './App.css'

const viewMeta: Record<View, { title: string; subtitle: string }> = {
  overview: {
    title: 'Resumen del portafolio',
    subtitle: 'Auditoría, riesgo y performance en una sola vista.',
  },
  data: {
    title: 'Capa de datos',
    subtitle: 'Proveedores, comparación de fuentes y carga manual de datos.',
  },
  audit: {
    title: 'Auditoría de datos',
    subtitle: 'Controles de calidad, incidencias y sesgos del universo.',
  },
  forecast: {
    title: 'Pronóstico ARIMA',
    subtitle: 'Series de tiempo, validación walk-forward y bandas de confianza.',
  },
  optimization: {
    title: 'Optimización Markowitz',
    subtitle: 'Frontera eficiente, restricciones y asignación objetivo.',
  },
}

function Overview() {
  return (
    <div className="stack">
      <section className="demo-banner">
        <div className="demo-banner-icon">
          <Sparkles size={20} />
        </div>
        <div>
          <strong>Demo visual con datos simulados</strong>
          <p>
            Esta pantalla muestra la dirección del producto. El motor Python todavía no está conectado:
            los números son de ejemplo para validar la experiencia antes de pasar el código probado en
            Jupyter a la web.
          </p>
        </div>
        <StatusBadge tone="info">Sin backend</StatusBadge>
      </section>

      <div className="kpi-grid">
        <KpiCard
          label="Valor del portafolio"
          value="$1,248,320"
          icon={Wallet}
          tone="teal"
          delta="+3.1%"
          deltaLabel="vs. mes anterior"
          trend="up"
        />
        <KpiCard
          label="Rendimiento YTD"
          value="+14.8%"
          icon={TrendingUp}
          tone="blue"
          delta="+6.6 pp"
          deltaLabel="vs. S&P 500"
          trend="up"
        />
        <KpiCard
          label="Volatilidad anual"
          value="11.2%"
          icon={Activity}
          tone="violet"
          delta="-1.4 pp"
          deltaLabel="vs. benchmark"
          trend="down"
        />
        <KpiCard
          label="Sharpe ratio"
          value="1.42"
          icon={Gauge}
          tone="amber"
          delta="+0.18"
          deltaLabel="vs. trimestre"
          trend="up"
        />
        <KpiCard
          label="Max drawdown"
          value="-6.8%"
          icon={ShieldAlert}
          tone="rose"
          delta="Recuperado"
          deltaLabel="en 42 días"
          trend="flat"
        />
        <KpiCard
          label="Universo"
          value="503"
          icon={Layers}
          tone="slate"
          delta="11"
          deltaLabel="sectores"
          trend="flat"
        />
      </div>

      <PerformanceChart />

      <div className="two-col">
        <SectorChart />
        <ProviderGrid limit={4} />
      </div>

      <AssetsTable />
    </div>
  )
}

function DataView() {
  return (
    <div className="stack">
      <SectionHeader
        eyebrow="Data layer"
        title="Fuentes y conectores"
        description="El motor elegirá el proveedor por configuración y comparará la calidad de cada fuente antes de calcular."
        action={<StatusBadge tone="success">6 integraciones</StatusBadge>}
      />
      <ProviderGrid />
      <ProviderComparison />
      <UploadPanel />
    </div>
  )
}

function AuditView() {
  return (
    <div className="stack">
      <SectionHeader
        eyebrow="Data quality"
        title="Auditoría del universo"
        description="Controles automáticos sobre fechas, precios, outliers, splits y cobertura antes de alimentar el motor."
        action={<StatusBadge tone="warning" dot>1 advertencia</StatusBadge>}
      />
      <AuditPanel />
    </div>
  )
}

function ForecastView() {
  return (
    <div className="stack">
      <SectionHeader
        eyebrow="Time series"
        title="Pronóstico con ARIMA"
        description="Modelo sobre retornos logarítmicos con validación fuera de muestra y bandas de confianza."
        action={<StatusBadge tone="info">ARIMA(2,1,2)</StatusBadge>}
      />
      <ForecastPanel />
    </div>
  )
}

function OptimizationView() {
  return (
    <div className="stack">
      <SectionHeader
        eyebrow="Portfolio optimization"
        title="Frontera eficiente"
        description="Selección de cartera con restricciones, covarianza regularizada y evaluación out-of-sample."
        action={<StatusBadge tone="success">Sharpe 1.58</StatusBadge>}
      />
      <OptimizationPanel />
    </div>
  )
}

function App() {
  const [view, setView] = useState<View>('overview')
  const meta = viewMeta[view]

  return (
    <div className="app-shell">
      <Sidebar active={view} onChange={setView} />
      <main className="main">
        <Topbar title={meta.title} subtitle={meta.subtitle} />
        <div className="content">
          {view === 'overview' && <Overview />}
          {view === 'data' && <DataView />}
          {view === 'audit' && <AuditView />}
          {view === 'forecast' && <ForecastView />}
          {view === 'optimization' && <OptimizationView />}
        </div>
        <footer className="app-footer">
          <span>Quant Engine · Demo visual</span>
          <span>Datos simulados · No constituye asesoría financiera</span>
        </footer>
      </main>
    </div>
  )
}

export default App
