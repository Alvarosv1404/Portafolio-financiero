import { Bell, CalendarDays, RefreshCw, Search, Sparkles } from 'lucide-react'

const TODAY_LABEL = new Date().toLocaleDateString('es-PE', {
  weekday: 'long',
  day: 'numeric',
  month: 'long',
  year: 'numeric',
})

interface TopbarProps {
  title: string
  subtitle: string
  isLive: boolean
  refreshing: boolean
  lastFetched: Date | null
  onRefresh: () => void
}

export function Topbar({ title, subtitle, isLive, refreshing, lastFetched, onRefresh }: TopbarProps) {
  const updated = lastFetched
    ? lastFetched.toLocaleTimeString('es-PE', { hour: '2-digit', minute: '2-digit' })
    : 'sin datos'

  return (
    <header className="topbar">
      <div className="topbar-copy">
        <div className="topbar-eyebrow">
          <CalendarDays size={14} />
          {TODAY_LABEL.charAt(0).toUpperCase() + TODAY_LABEL.slice(1)}
        </div>
        <h1>{title}</h1>
        <p>{subtitle}</p>
      </div>

      <div className="topbar-actions">
        <label className="search">
          <Search size={17} />
          <input type="search" placeholder="Buscar activo, sector o métrica..." />
        </label>
        <span className={`demo-pill ${isLive ? 'live' : ''}`} title={`Última actualización: ${updated}`}>
          <Sparkles size={14} />
          {isLive ? 'Datos reales' : 'Demo'}
        </span>
        <button
          type="button"
          className="icon-button"
          aria-label="Actualizar datos"
          title={`Actualizar desde yfinance · última: ${updated}`}
          onClick={onRefresh}
          disabled={refreshing}
        >
          <RefreshCw size={17} className={refreshing ? 'spin' : undefined} />
        </button>
        <button type="button" className="icon-button has-dot" aria-label="Notificaciones">
          <Bell size={17} />
        </button>
        <div className="avatar">AS</div>
      </div>
    </header>
  )
}
