import {
  CloudDownload,
  Database,
  Radio,
  RefreshCw,
  Server,
  ShieldCheck,
} from 'lucide-react'
import type { LucideIcon } from 'lucide-react'
import { providers } from '../data/mockData'
import type { ProviderStatus } from '../data/mockData'
import { StatusBadge } from './StatusBadge'

const statusMeta: Record<ProviderStatus, { label: string; tone: 'success' | 'info' | 'warning' }> = {
  connected: { label: 'Conectado', tone: 'success' },
  fallback: { label: 'Fallback', tone: 'info' },
  limited: { label: 'Limitado', tone: 'warning' },
}

const providerIcons: Record<string, LucideIcon> = {
  yfinance: CloudDownload,
  Finnhub: Radio,
  'Twelve Data': RefreshCw,
  Tiingo: ShieldCheck,
  'Alpha Vantage': Database,
  Marketstack: Server,
}

interface ProviderGridProps {
  limit?: number
}

export function ProviderGrid({ limit }: ProviderGridProps) {
  const visible = typeof limit === 'number' ? providers.slice(0, limit) : providers

  return (
    <section className="panel">
      <div className="panel-head">
        <div>
          <span className="panel-kicker">Infraestructura</span>
          <h3>Proveedores de datos</h3>
        </div>
        <span className="panel-note">{providers.length} integraciones</span>
      </div>

      <div className="provider-grid">
        {visible.map((provider) => {
          const Icon = providerIcons[provider.name] ?? Database
          const status = statusMeta[provider.status]
          return (
            <article key={provider.name} className="provider-card">
              <div className="provider-top">
                <span className="provider-icon">
                  <Icon size={18} />
                </span>
                <StatusBadge tone={status.tone} dot>
                  {status.label}
                </StatusBadge>
              </div>
              <strong>{provider.name}</strong>
              <span className="provider-role">{provider.role}</span>
              <div className="provider-stats">
                <div>
                  <span>Cobertura</span>
                  <strong>{provider.coverage}</strong>
                </div>
                <div>
                  <span>Latencia</span>
                  <strong>{provider.latency}</strong>
                </div>
                <div>
                  <span>Límite</span>
                  <strong>{provider.limit}</strong>
                </div>
              </div>
              <small className="provider-note">{provider.note}</small>
            </article>
          )
        })}
      </div>
    </section>
  )
}
