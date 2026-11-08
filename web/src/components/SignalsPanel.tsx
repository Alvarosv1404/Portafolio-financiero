import { useMemo } from 'react'
import { Radio, ShieldAlert, Sparkles } from 'lucide-react'
import { useDashboard } from '../data/DashboardContext'
import type { Signal } from '../data/types'
import { StatusBadge } from './StatusBadge'

const signalTone: Record<Signal, 'success' | 'info' | 'warning' | 'danger'> = {
  Comprar: 'success',
  Mantener: 'info',
  Vigilar: 'warning',
  Reducir: 'danger',
}

function verdictTone(verdict: string): 'success' | 'info' | 'warning' {
  if (verdict === 'Sólido') return 'success'
  if (verdict === 'Aceptable') return 'info'
  return 'warning'
}

export function SignalsPanel() {
  const { data } = useDashboard()

  const counts = useMemo(() => {
    const base: Record<Signal, number> = { Comprar: 0, Mantener: 0, Vigilar: 0, Reducir: 0 }
    for (const asset of data.assets) {
      base[asset.signal] += 1
    }
    return base
  }, [data.assets])

  const arimaByTicker = useMemo(
    () => new Map(data.asset_arima.map((item) => [item.ticker, item])),
    [data.asset_arima],
  )

  return (
    <div className="stack">
      <div className="metric-strip">
        <div className="metric-chip">
          <Sparkles size={17} />
          <div>
            <span>Comprar</span>
            <strong>{counts.Comprar}</strong>
          </div>
        </div>
        <div className="metric-chip">
          <Radio size={17} />
          <div>
            <span>Mantener</span>
            <strong>{counts.Mantener}</strong>
          </div>
        </div>
        <div className="metric-chip">
          <ShieldAlert size={17} />
          <div>
            <span>Vigilar</span>
            <strong>{counts.Vigilar}</strong>
          </div>
        </div>
        <div className="metric-chip">
          <ShieldAlert size={17} />
          <div>
            <span>Reducir</span>
            <strong>{counts.Reducir}</strong>
          </div>
        </div>
      </div>

      <section className="panel">
        <div className="panel-head">
          <div>
            <span className="panel-kicker">Señales</span>
            <h3>Compra / venta por activo del Top 10</h3>
          </div>
          <span className="panel-note">μ/σ a 21 días + momentum · son consejos, no órdenes</span>
        </div>

        <div className="table-wrap">
          <table>
            <thead>
              <tr>
                <th>Activo</th>
                <th>Señal</th>
                <th className="num">Sharpe μ/σ</th>
                <th className="num">Score combinado</th>
                <th className="num">Momentum 21d</th>
                <th className="num">Peso</th>
                <th>ARIMA</th>
                <th>Veredicto</th>
              </tr>
            </thead>
            <tbody>
              {data.assets.map((asset) => {
                const arima = arimaByTicker.get(asset.ticker)
                return (
                  <tr key={asset.ticker}>
                    <td>
                      <div className="ticker-cell">
                        <span className="ticker-avatar">{asset.ticker.slice(0, 2)}</span>
                        <div>
                          <strong>{asset.ticker}</strong>
                          <small>{asset.name}</small>
                        </div>
                      </div>
                    </td>
                    <td>
                      <StatusBadge tone={signalTone[asset.signal]} dot>
                        {asset.signal}
                      </StatusBadge>
                    </td>
                    <td className="num">{(asset.mu_sharpe ?? 0).toFixed(2)}</td>
                    <td className="num">{(asset.mu_score ?? 0).toFixed(2)}</td>
                    <td className={`num ${(asset.momentum_21d ?? 0) >= 0 ? 'positive' : 'negative'}`}>
                      {(asset.momentum_21d ?? 0) >= 0 ? '+' : ''}
                      {(asset.momentum_21d ?? 0).toFixed(1)}%
                    </td>
                    <td className="num">{asset.weight.toFixed(1)}%</td>
                    <td className="mono">{arima?.order ?? '—'}</td>
                    <td>
                      {arima ? (
                        <StatusBadge tone={verdictTone(arima.verdict)}>
                          {arima.verdict}
                        </StatusBadge>
                      ) : (
                        <span className="muted">—</span>
                      )}
                    </td>
                  </tr>
                )
              })}
            </tbody>
          </table>
        </div>
      </section>

      <section className="panel info-panel">
        <Radio size={20} />
        <div>
          <strong>Cómo leer las señales</strong>
          <p>
            La señal combina el ratio μ/σ (retorno esperado dividido por volatilidad) con el
            momentum de 21 días. Si el Sharpe es alto y el momentum acompaña, aparece
            “Comprar”; si el momentum cae con fuerza, “Reducir”. La columna ARIMA añade el
            veredicto del modelo de cada activo. Ninguna señal ejecuta una orden: el criterio
            final es tuyo.
          </p>
          <ul className="check-list">
            <li>Verde: el modelo ve condiciones favorables.</li>
            <li>Amarillo: conviene vigilar; el modelo no tiene una señal clara.</li>
            <li>Rojo: momentum negativo; el modelo sugiere reducir exposición.</li>
          </ul>
        </div>
      </section>
    </div>
  )
}
