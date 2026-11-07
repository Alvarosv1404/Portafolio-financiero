import { ArrowDownRight, ArrowUpRight } from 'lucide-react'
import { assets } from '../data/mockData'
import type { Signal } from '../data/mockData'
import { StatusBadge } from './StatusBadge'

const signalTone: Record<Signal, 'success' | 'info' | 'warning' | 'danger'> = {
  Comprar: 'success',
  Mantener: 'info',
  Vigilar: 'warning',
  Reducir: 'danger',
}

export function AssetsTable() {
  return (
    <section className="panel">
      <div className="panel-head">
        <div>
          <span className="panel-kicker">Universo</span>
          <h3>Activos destacados</h3>
        </div>
        <span className="panel-note">8 de 503 activos</span>
      </div>

      <div className="table-wrap">
        <table>
          <thead>
            <tr>
              <th>Activo</th>
              <th>Sector</th>
              <th className="num">Precio</th>
              <th className="num">Día</th>
              <th className="num">Peso</th>
              <th>Señal</th>
              <th className="num">ARIMA</th>
            </tr>
          </thead>
          <tbody>
            {assets.map((asset) => (
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
                <td className="muted">{asset.sector}</td>
                <td className="num">${asset.price.toFixed(2)}</td>
                <td className={`num ${asset.change >= 0 ? 'positive' : 'negative'}`}>
                  <span className="inline-trend">
                    {asset.change >= 0 ? <ArrowUpRight size={13} /> : <ArrowDownRight size={13} />}
                    {asset.change >= 0 ? '+' : ''}
                    {asset.change.toFixed(2)}%
                  </span>
                </td>
                <td className="num">{asset.weight.toFixed(1)}%</td>
                <td>
                  <StatusBadge tone={signalTone[asset.signal]} dot>
                    {asset.signal}
                  </StatusBadge>
                </td>
                <td className={`num ${asset.forecast.startsWith('-') ? 'negative' : 'positive'}`}>
                  {asset.forecast}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </section>
  )
}
