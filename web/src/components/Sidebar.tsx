import {
  Activity,
  Database,
  Gauge,
  LayoutDashboard,
  ListOrdered,
  PieChart as PieChartIcon,
  Radio,
  ShieldCheck,
  TrendingUp,
  Users,
  Wallet,
} from 'lucide-react'
import type { LucideIcon } from 'lucide-react'

export type View =
  | 'overview'
  | 'data'
  | 'audit'
  | 'forecast'
  | 'optimization'
  | 'profiles'
  | 'investment'
  | 'signals'
  | 'garch'
  | 'top10'

interface NavItem {
  id: View
  label: string
  hint: string
  icon: LucideIcon
}

const navItems: NavItem[] = [
  { id: 'overview', label: 'Resumen', hint: 'Vista general', icon: LayoutDashboard },
  { id: 'data', label: 'Datos', hint: 'Proveedores y Excel', icon: Database },
  { id: 'audit', label: 'Auditoría', hint: 'Calidad de datos', icon: ShieldCheck },
  { id: 'forecast', label: 'ARIMA', hint: 'Pronóstico', icon: TrendingUp },
  { id: 'optimization', label: 'Markowitz', hint: 'Frontera eficiente', icon: PieChartIcon },
  { id: 'profiles', label: 'Carteras', hint: '5 perfiles y métricas', icon: Users },
  { id: 'top10', label: 'Top 10', hint: 'Selección y reoptimización', icon: ListOrdered },
  { id: 'investment', label: 'Inversión', hint: 'Acciones y proyección', icon: Wallet },
  { id: 'signals', label: 'Señales', hint: 'μ/σ y momentum', icon: Radio },
  { id: 'garch', label: 'GARCH', hint: 'Volatilidad cartera/activo', icon: Gauge },
]

interface SidebarProps {
  active: View
  onChange: (view: View) => void
  isLive: boolean
}

export function Sidebar({ active, onChange, isLive }: SidebarProps) {
  return (
    <aside className="sidebar">
      <div className="brand">
        <div className="brand-mark">
          <Activity size={22} strokeWidth={2.2} />
        </div>
        <div>
          <strong>Quant Engine</strong>
          <span>Portfolio Lab</span>
        </div>
      </div>

      <div className="sidebar-label">Workspace</div>
      <nav className="nav">
        {navItems.map(({ id, label, hint, icon: Icon }) => (
          <button
            key={id}
            type="button"
            className={`nav-item ${active === id ? 'active' : ''}`}
            onClick={() => onChange(id)}
          >
            <span className="nav-icon">
              <Icon size={18} strokeWidth={1.9} />
            </span>
            <span className="nav-copy">
              <strong>{label}</strong>
              <small>{hint}</small>
            </span>
            <span className="nav-chevron">›</span>
          </button>
        ))}
      </nav>

      <div className="sidebar-card">
        <div className="sidebar-card-head">
          <span className={`status-dot ${isLive ? '' : 'offline'}`} />
          Motor Python
        </div>
        <strong>v0.1.0 · {isLive ? 'En vivo' : 'Demo'}</strong>
        <p>
          {isLive
            ? 'Precios reales de yfinance, Markowitz y ARIMA calculados en el backend.'
            : 'Sin conexión al backend. Se muestran datos de respaldo.'}
        </p>
      </div>

      <div className="sidebar-footer">
        <span>Alvarosv1404</span>
        <span>2026</span>
      </div>
    </aside>
  )
}
