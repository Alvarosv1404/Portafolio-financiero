import { Bell, CalendarDays, RefreshCw, Search, Sparkles } from 'lucide-react'

interface TopbarProps {
  title: string
  subtitle: string
}

export function Topbar({ title, subtitle }: TopbarProps) {
  return (
    <header className="topbar">
      <div className="topbar-copy">
        <div className="topbar-eyebrow">
          <CalendarDays size={14} />
          Jueves, 6 de noviembre de 2026
        </div>
        <h1>{title}</h1>
        <p>{subtitle}</p>
      </div>

      <div className="topbar-actions">
        <label className="search">
          <Search size={17} />
          <input type="search" placeholder="Buscar activo, sector o métrica..." />
        </label>
        <span className="demo-pill">
          <Sparkles size={14} />
          Modo demo
        </span>
        <button type="button" className="icon-button" aria-label="Actualizar datos">
          <RefreshCw size={17} />
        </button>
        <button type="button" className="icon-button has-dot" aria-label="Notificaciones">
          <Bell size={17} />
        </button>
        <div className="avatar">AS</div>
      </div>
    </header>
  )
}
