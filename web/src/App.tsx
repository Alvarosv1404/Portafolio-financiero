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
import { DashboardProvider, useDashboard } from './data/DashboardContext'
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
import { AssetArimaPanel } from './components/AssetArimaPanel'
import { OptimizationPanel } from './components/OptimizationPanel'
import { ProfilesPanel } from './components/ProfilesPanel'
import { Top10Panel } from './components/Top10Panel'
import { InvestmentPanel } from './components/InvestmentPanel'
import { SignalsPanel } from './components/SignalsPanel'
import { GarchPanel } from './components/GarchPanel'
import { UploadPanel } from './components/UploadPanel'
import { SectionHeader } from './components/SectionHeader'
import { StatusBadge } from './components/StatusBadge'
import './App.css'

const viewMeta: Record<View, { title: string; subtitle: string }> = {
  overview: {
    title: 'Resumen del portafolio',
    subtitle: 'Auditoría, riesgo y performance calculados con datos públicos.',
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
    subtitle: 'Serie del portafolio, validación fuera de muestra y bandas de confianza.',
  },
  optimization: {
    title: 'Optimización Markowitz',
    subtitle: 'Frontera eficiente, restricciones y asignación objetivo.',
  },
  profiles: {
    title: 'Carteras',
    subtitle: 'Los 5 perfiles calculados sobre la misma frontera eficiente.',
  },
  top10: {
    title: 'Top 10 activos',
    subtitle: 'Selección por score compuesto y reoptimización de la cartera.',
  },
  investment: {
    title: 'Inversión',
    subtitle: 'Cuántas acciones puedes comprar y cuánto valdría tu inversión.',
  },
  signals: {
    title: 'Señales',
    subtitle: 'Avisos de compra, venta y vigilancia según μ/σ, momentum y ARIMA.',
  },
  garch: {
    title: 'Volatilidad GARCH',
    subtitle: 'Volatilidad condicional de la cartera y de cada activo del Top 10.',
  },
}

function formatPct(value: number, digits = 1) {
  const sign = value >= 0 ? '+' : ''
  return `${sign}${(value * 100).toFixed(digits)}%`
}

function formatMoney(value: number) {
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: 'USD',
    maximumFractionDigits: 0,
  }).format(value)
}

function Overview() {
  const { data, status, error } = useDashboard()
  const { meta, metrics } = data
  const isLive = meta.isLive && status !== 'loading'
  const bannerTone = isLive ? 'success' : status === 'loading' ? 'info' : 'warning'
  const bannerTitle = isLive
    ? 'Motor calculando con datos reales'
    : status === 'loading'
      ? 'Descargando precios y calculando la cartera…'
      : 'Modo demo: el motor no respondió'
  const bannerText = isLive
    ? `yfinance · ${meta.universeSize} activos · ${meta.start} a ${meta.end} · benchmark ${meta.benchmark} · descarga ${(meta.downloadMs / 1000).toFixed(1)} s.`
    : status === 'loading'
      ? 'La primera carga descarga unos 3 años de precios, estima la covarianza, optimiza Markowitz y ajusta ARIMA. Puede tardar unos segundos.'
      : `${error ?? 'Sin conexión con la API.'} Se muestran datos de respaldo para que puedas navegar la interfaz.`

  return (
    <div className="stack">
      <section className={`demo-banner ${isLive ? 'live-banner' : ''}`}>
        <div className="demo-banner-icon">
          {isLive ? <Activity size={20} /> : <Sparkles size={20} />}
        </div>
        <div>
          <strong>{bannerTitle}</strong>
          <p>{bannerText}</p>
          {meta.warnings.length > 0 && (
            <ul className="banner-warnings">
              {meta.warnings.slice(0, 2).map((warning) => (
                <li key={warning}>{warning}</li>
              ))}
            </ul>
          )}
        </div>
        <StatusBadge tone={bannerTone}>
          {isLive ? 'Datos reales' : status === 'loading' ? 'Calculando' : 'Respaldo'}
        </StatusBadge>
      </section>

      <div className="kpi-grid">
        <KpiCard
          label="Valor simulado"
          value={formatMoney(metrics.portfolioValue)}
          icon={Wallet}
          tone="teal"
          delta={formatPct(metrics.ytdReturn)}
          deltaLabel={`capital inicial ${formatMoney(metrics.capital)}`}
          trend={metrics.ytdReturn >= 0 ? 'up' : 'down'}
        />
        <KpiCard
          label="Rendimiento anual"
          value={formatPct(metrics.annualReturn)}
          icon={TrendingUp}
          tone="blue"
          delta={`${metrics.excessReturn >= 0 ? '+' : ''}${(metrics.excessReturn * 100).toFixed(1)} pp`}
          deltaLabel={`vs ${meta.benchmark} ${formatPct(metrics.benchmarkReturn)}`}
          trend={metrics.excessReturn >= 0 ? 'up' : 'down'}
        />
        <KpiCard
          label="Volatilidad anual"
          value={`${(metrics.volatility * 100).toFixed(1)}%`}
          icon={Activity}
          tone="violet"
          delta={`${metrics.excessVolatility >= 0 ? '+' : ''}${(metrics.excessVolatility * 100).toFixed(1)} pp`}
          deltaLabel={`vs ${(metrics.benchmarkVolatility * 100).toFixed(1)}% del benchmark`}
          trend={metrics.excessVolatility <= 0 ? 'down' : 'up'}
        />
        <KpiCard
          label="Sharpe ratio"
          value={metrics.sharpe.toFixed(2)}
          icon={Gauge}
          tone="amber"
          deltaLabel={`tasa libre de riesgo ${(metrics.riskFreeRate * 100).toFixed(1)}%`}
          trend="flat"
        />
        <KpiCard
          label="Max drawdown"
          value={`${(metrics.maxDrawdown * 100).toFixed(1)}%`}
          icon={ShieldAlert}
          tone="rose"
          deltaLabel="máxima caída pico-valle"
          trend="down"
        />
        <KpiCard
          label="Universo"
          value={String(metrics.universeSize)}
          icon={Layers}
          tone="slate"
          delta={String(metrics.sectorsCount)}
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
  const { data } = useDashboard()
  return (
    <div className="stack">
      <SectionHeader
        eyebrow="Data layer"
        title="Fuentes y conectores"
        description="El motor descarga precios reales de yfinance y deja preparadas las claves de los proveedores alternativos. La comparación marca qué fuentes están realmente medidas."
        action={<StatusBadge tone="success">{data.providers.length} integraciones</StatusBadge>}
      />
      <ProviderGrid />
      <ProviderComparison />
      <UploadPanel />
    </div>
  )
}

function AuditView() {
  const { data } = useDashboard()
  const alerts = data.auditChecks.filter((check) => check.status !== 'ok').length
  return (
    <div className="stack">
      <SectionHeader
        eyebrow="Data quality"
        title="Auditoría del universo"
        description="Controles automáticos sobre fechas, precios, outliers, movimientos extremos y cobertura antes de alimentar el motor."
        action={
          <StatusBadge tone={alerts ? 'warning' : 'success'} dot>
            {alerts ? `${alerts} alertas` : 'Sin alertas'}
          </StatusBadge>
        }
      />
      <AuditPanel />
    </div>
  )
}

function ForecastView() {
  const { data } = useDashboard()
  return (
    <div className="stack">
      <SectionHeader
        eyebrow="Time series"
        title="Pronóstico con ARIMA"
        description="Modelo del portafolio y diagnóstico individual por activo: orden elegido, supuestos, veredicto y proyección."
        action={<StatusBadge tone="info">{data.forecast.model}</StatusBadge>}
      />
      <ForecastPanel />
      <AssetArimaPanel />
    </div>
  )
}

function OptimizationView() {
  const { data } = useDashboard()
  return (
    <div className="stack">
      <SectionHeader
        eyebrow="Portfolio optimization"
        title="Frontera eficiente"
        description="Maximización del Sharpe con restricciones, covarianza regularizada y frontera calculada sobre retornos reales."
        action={<StatusBadge tone="success">Sharpe {data.optimization.sharpe.toFixed(2)}</StatusBadge>}
      />
      <OptimizationPanel />
    </div>
  )
}

function ProfilesView() {
  const { data } = useDashboard()
  const profiles = data.meta.profiles ?? {}
  return (
    <div className="stack">
      <SectionHeader
        eyebrow="Portfolios"
        title="5 carteras, una misma frontera"
        description="Bajo riesgo busca mínima varianza; moderado, volatilidad intermedia; ideal, máximo Sharpe; riesgoso, máximo retorno. Total une los activos de los cuatro."
        action={
          <StatusBadge tone="info">{Object.keys(profiles).length} perfiles calculados</StatusBadge>
        }
      />
      <ProfilesPanel />
    </div>
  )
}

function Top10View() {
  const { data } = useDashboard()
  return (
    <div className="stack">
      <SectionHeader
        eyebrow="Selection"
        title="Los 10 mejores activos"
        description="Score compuesto por peso en perfiles, Sharpe individual y momentum de 6 meses. Con esos 10 se recalcula Markowitz a máximo Sharpe."
        action={<StatusBadge tone="success">{data.meta.top10?.length ?? data.assets.length} activos</StatusBadge>}
      />
      <Top10Panel />
    </div>
  )
}

function InvestmentView() {
  return (
    <div className="stack">
      <SectionHeader
        eyebrow="Capital"
        title="Simulador de inversión"
        description="Elige un monto y un activo. El motor calcula acciones enteras, efectivo residual y el valor proyectado a 1, 3 y 6 meses."
      />
      <InvestmentPanel />
    </div>
  )
}

function SignalsView() {
  return (
    <div className="stack">
      <SectionHeader
        eyebrow="Signals"
        title="Avisos de compra y venta"
        description="Señales estadísticas por activo combinando μ/σ a 21 días, momentum y el veredicto ARIMA. Son consejos: la decisión final es tuya."
      />
      <SignalsPanel />
    </div>
  )
}

function GarchView() {
  return (
    <div className="stack">
      <SectionHeader
        eyebrow="Volatility"
        title="GARCH(1,1)"
        description="Volatilidad condicional anualizada de la cartera Top 10 y de cada activo. La cartera se calcula sobre sus propios retornos (R × w)."
      />
      <GarchPanel />
    </div>
  )
}

const viewIds: View[] = [
  'overview',
  'data',
  'audit',
  'forecast',
  'optimization',
  'profiles',
  'top10',
  'investment',
  'signals',
  'garch',
]

function readViewFromHash(): View {
  const hash = window.location.hash.replace('#', '')
  return viewIds.includes(hash as View) ? (hash as View) : 'overview'
}

function Shell() {
  const [view, setView] = useState<View>(readViewFromHash)
  const { data, status, refreshing, lastFetched, refresh } = useDashboard()

  const changeView = (next: View) => {
    setView(next)
    window.history.replaceState(null, '', `#${next}`)
  }

  const meta = viewMeta[view]
  const isLive = data.meta.isLive && status !== 'loading'
  const updated = lastFetched
    ? lastFetched.toLocaleString('es-PE', {
        day: '2-digit',
        month: 'short',
        hour: '2-digit',
        minute: '2-digit',
      })
    : 'sin datos'

  return (
    <div className="app-shell">
      <Sidebar active={view} onChange={changeView} isLive={isLive} />
      <main className="main">
        <Topbar
          title={meta.title}
          subtitle={meta.subtitle}
          isLive={isLive}
          refreshing={refreshing}
          lastFetched={lastFetched}
          onRefresh={refresh}
        />
        <div className="content">
          {view === 'overview' && <Overview />}
          {view === 'data' && <DataView />}
          {view === 'audit' && <AuditView />}
          {view === 'forecast' && <ForecastView />}
          {view === 'optimization' && <OptimizationView />}
          {view === 'profiles' && <ProfilesView />}
          {view === 'top10' && <Top10View />}
          {view === 'investment' && <InvestmentView />}
          {view === 'signals' && <SignalsView />}
          {view === 'garch' && <GarchView />}
        </div>
        <footer className="app-footer">
          <span>Quant Engine · {isLive ? 'Datos reales vía yfinance' : 'Demo visual'}</span>
          <span>Actualizado: {updated} · No constituye asesoría financiera</span>
        </footer>
      </main>
    </div>
  )
}

function App() {
  return (
    <DashboardProvider>
      <Shell />
    </DashboardProvider>
  )
}

export default App
