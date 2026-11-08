import { useMemo } from 'react'
import { Shield, Sparkles, Target, TrendingUp, Layers } from 'lucide-react'
import { useDashboard } from '../data/DashboardContext'
import type { ProfileName } from '../data/types'
import { StatusBadge } from './StatusBadge'

const profileOrder: ProfileName[] = [
  'bajo_riesgo',
  'moderado',
  'ideal',
  'riesgoso',
  'total',
]

const profileInfo: Record<
  ProfileName,
  { label: string; hint: string; icon: typeof Shield; tone: 'success' | 'info' | 'warning' | 'neutral' }
> = {
  bajo_riesgo: {
    label: 'Bajo riesgo',
    hint: 'Mínima varianza',
    icon: Shield,
    tone: 'success',
  },
  moderado: {
    label: 'Moderado',
    hint: 'Volatilidad intermedia',
    icon: Layers,
    tone: 'info',
  },
  ideal: {
    label: 'Ideal',
    hint: 'Máximo Sharpe',
    icon: Sparkles,
    tone: 'success',
  },
  riesgoso: {
    label: 'Riesgoso',
    hint: 'Máximo retorno',
    icon: TrendingUp,
    tone: 'warning',
  },
  total: {
    label: 'Total',
    hint: 'Unión de los 4 perfiles',
    icon: Target,
    tone: 'neutral',
  },
}

function pct(value: number, digits = 1) {
  return `${(value * 100).toFixed(digits)}%`
}

export function ProfilesPanel() {
  const { data, status } = useDashboard()
  const profiles = data.meta.profiles

  const cards = useMemo(() => {
    if (!profiles) return []
    return profileOrder
      .map((name) => {
        const summary = profiles[name]
        if (!summary) return null
        const holdings = Object.entries(summary.weights)
          .sort(([, a], [, b]) => b - a)
          .slice(0, 5)
        const maxWeight = Math.max(...holdings.map(([, weight]) => weight), 1)
        return { name, summary, holdings, maxWeight }
      })
      .filter((item): item is NonNullable<typeof item> => item !== null)
  }, [profiles])

  if (cards.length === 0) {
    return (
      <section className="panel">
        <div className="panel-head">
          <div>
            <span className="panel-kicker">Carteras</span>
            <h3>Perfiles de inversión</h3>
          </div>
          <StatusBadge tone="warning">Sin datos</StatusBadge>
        </div>
        <p className="empty-state">
          El motor todavía no devolvió los perfiles. Actualiza los datos para calcularlos.
        </p>
      </section>
    )
  }

  return (
    <section className="panel">
      <div className="panel-head">
        <div>
          <span className="panel-kicker">Carteras</span>
          <h3>5 perfiles sobre la misma frontera eficiente</h3>
        </div>
        <StatusBadge tone={status === 'live' ? 'success' : 'warning'} dot>
          {status === 'live' ? 'Datos reales' : 'Respaldo'}
        </StatusBadge>
      </div>

      <div className="profiles-grid">
        {cards.map(({ name, summary, holdings, maxWeight }) => {
          const info = profileInfo[name]
          const Icon = info.icon
          return (
            <article
              key={name}
              className={`profile-card ${name === 'total' ? 'profile-card-total' : ''}`}
            >
              <header className="profile-card-head">
                <div className="profile-title">
                  <span className="profile-icon">
                    <Icon size={16} />
                  </span>
                  <div>
                    <strong>{info.label}</strong>
                    <small>{info.hint}</small>
                  </div>
                </div>
                <StatusBadge tone={info.tone}>{pct(summary.expectedReturn)}</StatusBadge>
              </header>

              <div className="profile-metrics">
                <div>
                  <span>Retorno esp.</span>
                  <strong>{pct(summary.expectedReturn)}</strong>
                </div>
                <div>
                  <span>Volatilidad</span>
                  <strong>{pct(summary.volatility)}</strong>
                </div>
                <div>
                  <span>Sharpe</span>
                  <strong>{summary.sharpe.toFixed(2)}</strong>
                </div>
              </div>

              <div className="profile-holdings">
                {holdings.map(([ticker, weight]) => (
                  <div key={ticker} className="holding-row">
                    <span className="holding-ticker">{ticker}</span>
                    <span className="holding-track">
                      <span style={{ width: `${(weight / maxWeight) * 100}%` }} />
                    </span>
                    <span className="holding-weight">{weight.toFixed(1)}%</span>
                  </div>
                ))}
              </div>
              <p className="profile-footnote">
                {Object.keys(summary.weights).length} activos · top 5 mostrados
              </p>
            </article>
          )
        })}
      </div>
    </section>
  )
}
