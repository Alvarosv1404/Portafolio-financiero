import { useMemo, useState } from 'react'
import { Banknote, Calculator } from 'lucide-react'
import { useDashboard } from '../data/DashboardContext'
import { StatusBadge } from './StatusBadge'

const money = new Intl.NumberFormat('en-US', {
  style: 'currency',
  currency: 'USD',
  maximumFractionDigits: 2,
})

const quickAmounts = [1_000, 10_000, 50_000, 100_000]

export function InvestmentPanel() {
  const { data } = useDashboard()
  const rows = data.investment
  const [ticker, setTicker] = useState(rows[0]?.ticker ?? '')
  const [capital, setCapital] = useState(data.meta.capital || 100_000)

  const selected = rows.find((row) => row.ticker === ticker) ?? rows[0]

  const calculation = useMemo(() => {
    if (!selected) return null
    const shares = Math.floor(Math.max(capital, 0) / selected.currentPrice)
    const invested = shares * selected.currentPrice
    const residual = Math.max(capital - invested, 0)
    const value = (price?: number | null) =>
      price === null || price === undefined ? null : shares * price
    const values = {
      m1: value(selected.projectedPrice1m),
      m3: value(selected.projectedPrice3m),
      m6: value(selected.projectedPrice6m),
    }
    return { shares, invested, residual, values }
  }, [selected, capital])

  if (!selected || !calculation) {
    return (
      <section className="panel">
        <div className="panel-head">
          <div>
            <span className="panel-kicker">Inversión</span>
            <h3>Cuánto puedes comprar</h3>
          </div>
          <StatusBadge tone="warning">Sin datos</StatusBadge>
        </div>
        <p className="empty-state">El motor todavía no devolvió precios para calcular acciones.</p>
      </section>
    )
  }

  const returnPct = (future: number | null) => {
    if (future === null || calculation.invested <= 0) return null
    return (future / calculation.invested - 1) * 100
  }

  return (
    <div className="stack">
      <section className="panel">
        <div className="panel-head">
          <div>
            <span className="panel-kicker">Simulador de inversión</span>
            <h3>¿Cuántas acciones puedo comprar con un monto?</h3>
          </div>
          <span className="panel-note">Solo acciones enteras · sin fracciones</span>
        </div>

        <div className="capital-row">
          <label className="capital-field">
            <span>Monto a invertir</span>
            <div className="capital-input">
              <Banknote size={16} />
              <input
                type="number"
                min={100}
                step={100}
                value={capital}
                onChange={(event) => setCapital(Number(event.target.value) || 0)}
              />
            </div>
          </label>
          <div className="quick-amounts">
            {quickAmounts.map((amount) => (
              <button
                key={amount}
                type="button"
                className={`pill ${capital === amount ? 'pill-active' : ''}`}
                onClick={() => setCapital(amount)}
              >
                {money.format(amount)}
              </button>
            ))}
          </div>
          <label className="capital-field">
            <span>Activo</span>
            <select
              className="asset-select"
              value={selected.ticker}
              onChange={(event) => setTicker(event.target.value)}
            >
              {rows.map((row) => (
                <option key={row.ticker} value={row.ticker}>
                  {row.ticker} · {row.name}
                </option>
              ))}
            </select>
          </label>
        </div>

        <div className="investment-grid">
          <div className="inv-card">
            <span className="inv-label">Precio actual</span>
            <span className="inv-value">{money.format(selected.currentPrice)}</span>
            <small>{selected.name}</small>
          </div>
          <div className="inv-card inv-card-highlight">
            <span className="inv-label">Acciones enteras</span>
            <span className="inv-value">{calculation.shares.toLocaleString('es-PE')}</span>
            <small>capital invertido {money.format(calculation.invested)}</small>
          </div>
          <div className="inv-card">
            <span className="inv-label">Efectivo residual</span>
            <span className="inv-value">{money.format(calculation.residual)}</span>
            <small>no alcanza para otra acción</small>
          </div>
          <div className="inv-card">
            <span className="inv-label">Señal</span>
            <StatusBadge
              tone={
                selected.signal === 'Comprar'
                  ? 'success'
                  : selected.signal === 'Reducir'
                    ? 'danger'
                    : selected.signal === 'Vigilar'
                      ? 'warning'
                      : 'info'
              }
              dot
            >
              {selected.signal}
            </StatusBadge>
            <small>consejo estadístico, no obligatorio</small>
          </div>
        </div>
      </section>

      <div className="two-col">
        <section className="panel">
          <div className="panel-head">
            <div>
              <span className="panel-kicker">Proyección</span>
              <h3>Valor de la inversión a futuro</h3>
            </div>
            <span className="panel-note">Precio proyectado × acciones</span>
          </div>

          <div className="projection-table">
            {[
              { label: '1 mes', future: calculation.values.m1, price: selected.projectedPrice1m },
              { label: '3 meses', future: calculation.values.m3, price: selected.projectedPrice3m },
              { label: '6 meses', future: calculation.values.m6, price: selected.projectedPrice6m },
            ].map(({ label, future, price }) => {
              const pct = returnPct(future)
              return (
                <div key={label} className="projection-row">
                  <div>
                    <span className="proj-label">{label}</span>
                    <small>precio {price === null || price === undefined ? '—' : money.format(price)}</small>
                  </div>
                  <strong>{future === null ? '—' : money.format(future)}</strong>
                  <span className={`proj-delta ${pct !== null && pct >= 0 ? 'positive' : 'negative'}`}>
                    {pct === null ? '—' : `${pct >= 0 ? '+' : ''}${pct.toFixed(1)}%`}
                  </span>
                </div>
              )
            })}
          </div>

          <p className="panel-footnote">
            Proyección con el retorno mensual promedio del activo. No es una garantía ni una
            predicción de mercado.
          </p>
        </section>

        <section className="panel">
          <div className="panel-head">
            <div>
              <span className="panel-kicker">Comparativa</span>
              <h3>Acciones comprables por activo</h3>
            </div>
            <span className="panel-note">Con {money.format(capital)}</span>
          </div>

          <div className="table-wrap">
            <table>
              <thead>
                <tr>
                  <th>Activo</th>
                  <th className="num">Precio</th>
                  <th className="num">Acciones</th>
                  <th className="num">Invertido</th>
                  <th className="num">Residual</th>
                </tr>
              </thead>
              <tbody>
                {rows.map((row) => {
                  const shares = Math.floor(Math.max(capital, 0) / row.currentPrice)
                  const invested = shares * row.currentPrice
                  return (
                    <tr
                      key={row.ticker}
                      className={row.ticker === selected.ticker ? 'row-selected' : ''}
                      onClick={() => setTicker(row.ticker)}
                    >
                      <td>
                        <div className="ticker-cell">
                          <span className="ticker-avatar">{row.ticker.slice(0, 2)}</span>
                          <div>
                            <strong>{row.ticker}</strong>
                            <small>{row.name}</small>
                          </div>
                        </div>
                      </td>
                      <td className="num">{money.format(row.currentPrice)}</td>
                      <td className="num">{shares.toLocaleString('es-PE')}</td>
                      <td className="num">{money.format(invested)}</td>
                      <td className="num">{money.format(Math.max(capital - invested, 0))}</td>
                    </tr>
                  )
                })}
              </tbody>
            </table>
          </div>
        </section>
      </div>

      <section className="panel info-panel">
        <Calculator size={20} />
        <div>
          <strong>Cómo se calcula</strong>
          <p>
            Acciones = piso(monto ÷ precio actual). El efectivo residual es lo que sobra después
            de comprar solo acciones enteras. La proyección multiplica esas acciones por el
            precio estimado a 1, 3 y 6 meses usando el retorno mensual promedio del activo.
          </p>
          <ul className="check-list">
            <li>
              {calculation.shares.toLocaleString('es-PE')} acciones de {selected.ticker} con{' '}
              {money.format(capital)}
            </li>
            <li>Residual: {money.format(calculation.residual)}</li>
            <li>
              Si el precio sube, ganas; si baja, pierdes. La señal es una referencia, no una
              orden.
            </li>
          </ul>
        </div>
      </section>
    </div>
  )
}
