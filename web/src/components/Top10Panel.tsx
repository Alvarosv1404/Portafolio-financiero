import { ListFilter, Sparkles } from 'lucide-react'
import { useDashboard } from '../data/DashboardContext'
import type { Signal } from '../data/types'
import { StatusBadge } from './StatusBadge'

const signalTone: Record<Signal, 'success' | 'info' | 'warning' | 'danger'> = {
  Comprar: 'success',
  Mantener: 'info',
  Vigilar: 'warning',
  Reducir: 'danger',
}

export function Top10Panel() {
  const { data } = useDashboard()
  const assets = data.assets

  return (
    <div className="stack">
      <div className="metric-strip">
        <div className="metric-chip">
          <ListFilter size={17} />
          <div>
            <span>Activos seleccionados</span>
            <strong>{assets.length}</strong>
          </div>
        </div>
        <div className="metric-chip">
          <Sparkles size={17} />
          <div>
            <span>Reoptimización</span>
            <strong>Máximo Sharpe</strong>
          </div>
        </div>
        <div className="metric-chip">
          <Sparkles size={17} />
          <div>
            <span>Peso máximo</span>
            <strong>{(data.optimization.maxWeight * 100).toFixed(0)}%</strong>
          </div>
        </div>
        <div className="metric-chip">
          <Sparkles size={17} />
          <div>
            <span>Posiciones</span>
            <strong>{data.optimization.positions}</strong>
          </div>
        </div>
      </div>

      <section className="panel">
        <div className="panel-head">
          <div>
            <span className="panel-kicker">Selección Top 10</span>
            <h3>Los mejores activos por score compuesto</h3>
          </div>
          <span className="panel-note">40% peso en perfiles · 30% Sharpe · 30% momentum 6M</span>
        </div>

        <div className="table-wrap">
          <table>
            <thead>
              <tr>
                <th>#</th>
                <th>Activo</th>
                <th>Sector</th>
                <th className="num">Score</th>
                <th className="num">Peso Top 10</th>
                <th className="num">Retorno anual</th>
                <th className="num">Sharpe μ/σ</th>
                <th className="num">Mom. 21d</th>
                <th>Señal</th>
              </tr>
            </thead>
            <tbody>
              {assets.map((asset, index) => (
                <tr key={asset.ticker}>
                  <td className="muted">{index + 1}</td>
                  <td>
                    <div className="ticker-cell">
                      <span className="ticker-avatar">{asset.ticker.slice(0, 2)}</span>
                      <div>
                        <strong>{asset.ticker}</strong>
                        <small>{asset.name}</small>
                      </div>
                    </div>
                  </td>
                  <td className="muted">{asset.sector}</td>
                  <td className="num">{(asset.score ?? 0).toFixed(3)}</td>
                  <td className="num">{asset.weight.toFixed(1)}%</td>
                  <td className={`num ${(asset.annualReturn ?? 0) >= 0 ? 'positive' : 'negative'}`}>
                    {(asset.annualReturn ?? 0) >= 0 ? '+' : ''}
                    {(asset.annualReturn ?? 0).toFixed(1)}%
                  </td>
                  <td className="num">{(asset.mu_sharpe ?? 0).toFixed(2)}</td>
                  <td className={`num ${(asset.momentum_21d ?? 0) >= 0 ? 'positive' : 'negative'}`}>
                    {(asset.momentum_21d ?? 0) >= 0 ? '+' : ''}
                    {(asset.momentum_21d ?? 0).toFixed(1)}%
                  </td>
                  <td>
                    <StatusBadge tone={signalTone[asset.signal]} dot>
                      {asset.signal}
                    </StatusBadge>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>

      <section className="panel info-panel">
        <ListFilter size={20} />
        <div>
          <strong>¿Cómo se eligen los 10?</strong>
          <p>
            Primero se calculan los 4 perfiles (bajo riesgo, moderado, ideal y riesgoso) sobre
            todo el universo. Cada activo recibe un score: 40% por su peso promedio en esos
            perfiles, 30% por su Sharpe individual y 30% por el momentum de 6 meses. Con esos 10
            activos se vuelve a optimizar Markowitz a máximo Sharpe y ese resultado es el que
            ves en la cartera, la inversión, las señales y GARCH.
          </p>
        </div>
      </section>
    </div>
  )
}
