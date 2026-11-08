import { useState } from 'react'
import {
  CartesianGrid,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts'
import { Activity, Gauge, Layers, Radio } from 'lucide-react'
import { useDashboard } from '../data/DashboardContext'
import { StatusBadge } from './StatusBadge'

const chartStyle = {
  background: '#0b1220',
  border: '1px solid rgba(148, 163, 184, 0.2)',
  borderRadius: 12,
  color: '#e2e8f0',
  fontSize: 12,
}

export function GarchPanel() {
  const { data } = useDashboard()
  const garch = data.garch
  const perAsset = garch?.perAsset ?? {}
  const tickers = Object.keys(perAsset)
  const [selected, setSelected] = useState('portfolio')

  const asset = selected !== 'portfolio' ? perAsset[selected] : undefined
  const isPortfolio = selected === 'portfolio'
  const path = isPortfolio ? garch?.portfolioVolatility.path ?? [] : asset?.conditionalVolatility ?? []

  const series = path.map((value, index) => ({ day: index + 1, volatility: value }))

  const finalVolatility = isPortfolio
    ? garch?.portfolioVolatility.final ?? 0
    : asset?.finalVolatility ?? 0
  const longRun = asset?.unconditionalVolatility

  const maxVol = Math.max(...path, 1)

  return (
    <div className="stack">
      <div className="metric-strip">
        <div className="metric-chip">
          <Gauge size={17} />
          <div>
            <span>Volatilidad actual</span>
            <strong>{finalVolatility.toFixed(2)}%</strong>
          </div>
        </div>
        <div className="metric-chip">
          <Activity size={17} />
          <div>
            <span>Largo plazo</span>
            <strong>{longRun !== undefined ? `${longRun.toFixed(2)}%` : 'Cartera'}</strong>
          </div>
        </div>
        <div className="metric-chip">
          <Radio size={17} />
          <div>
            <span>Observaciones</span>
            <strong>{path.length}</strong>
          </div>
        </div>
        <div className="metric-chip">
          <Layers size={17} />
          <div>
            <span>Activos modelados</span>
            <strong>{tickers.length}</strong>
          </div>
        </div>
      </div>

      <section className="panel">
        <div className="panel-head">
          <div>
            <span className="panel-kicker">GARCH(1,1)</span>
            <h3>Volatilidad condicional: cartera y activos</h3>
          </div>
          <StatusBadge tone="info">Anualizada</StatusBadge>
        </div>

        <div className="selector-row">
          <button
            type="button"
            className={`pill ${isPortfolio ? 'pill-active' : ''}`}
            onClick={() => setSelected('portfolio')}
          >
            Cartera Top 10
          </button>
          {tickers.map((ticker) => (
            <button
              key={ticker}
              type="button"
              className={`pill ${selected === ticker ? 'pill-active' : ''}`}
              onClick={() => setSelected(ticker)}
            >
              {ticker}
            </button>
          ))}
        </div>

        <div className="garch-summary">
          <div>
            <span>Selección</span>
            <strong>{isPortfolio ? 'Cartera Top 10' : selected}</strong>
          </div>
          <div>
            <span>Volatilidad anualizada</span>
            <strong>{finalVolatility.toFixed(2)}%</strong>
          </div>
          <div>
            <span>Volatilidad de largo plazo</span>
            <strong>{longRun !== undefined ? `${longRun.toFixed(2)}%` : '—'}</strong>
          </div>
          <div>
            <span>Pico del periodo</span>
            <strong>{maxVol.toFixed(2)}%</strong>
          </div>
        </div>

        <div className="chart-wrap">
          {series.length > 0 ? (
            <ResponsiveContainer width="100%" height={310}>
              <LineChart data={series} margin={{ top: 12, right: 16, left: -10, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="rgba(148, 163, 184, 0.12)" vertical={false} />
                <XAxis
                  dataKey="day"
                  tick={{ fill: '#8b9bb4', fontSize: 11 }}
                  axisLine={false}
                  tickLine={false}
                  label={{ value: 'Días', position: 'insideBottomRight', offset: -4, fill: '#5f748f', fontSize: 10 }}
                />
                <YAxis
                  unit="%"
                  domain={[0, 'auto']}
                  tick={{ fill: '#8b9bb4', fontSize: 11 }}
                  axisLine={false}
                  tickLine={false}
                />
                <Tooltip
                  contentStyle={chartStyle}
                  labelStyle={{ color: '#94a3b8', marginBottom: 6 }}
                  formatter={(value) => [`${Number(value).toFixed(2)}%`, 'Volatilidad']}
                  labelFormatter={(label) => `Día ${label}`}
                />
                <Line
                  type="monotone"
                  dataKey="volatility"
                  stroke="#2dd4bf"
                  strokeWidth={2.4}
                  dot={false}
                  fill="rgba(45, 212, 191, 0.08)"
                />
              </LineChart>
            </ResponsiveContainer>
          ) : (
            <p className="empty-state">Sin path de volatilidad para esta selección.</p>
          )}
        </div>
      </section>

      <section className="panel">
        <div className="panel-head">
          <div>
            <span className="panel-kicker">Comparativa</span>
            <h3>Volatilidad final por activo</h3>
          </div>
          <span className="panel-note">Haz clic para ver su path</span>
        </div>
        <div className="garch-grid">
          {tickers.map((ticker) => {
            const item = perAsset[ticker]
            return (
              <button
                key={ticker}
                type="button"
                className={`garch-card ${selected === ticker ? 'garch-card-active' : ''}`}
                onClick={() => setSelected(ticker)}
              >
                <span className="garch-ticker">{ticker}</span>
                <strong>{item.finalVolatility.toFixed(2)}%</strong>
                <span className="garch-track">
                  <span
                    style={{
                      width: `${Math.min((item.finalVolatility / Math.max(finalVolatility, 1)) * 100, 100)}%`,
                    }}
                  />
                </span>
              </button>
            )
          })}
          {tickers.length === 0 && (
            <p className="empty-state">El motor no devolvió GARCH por activo todavía.</p>
          )}
        </div>
      </section>

      <section className="panel info-panel">
        <Gauge size={20} />
        <div>
          <strong>Qué estás viendo</strong>
          <p>
            GARCH(1,1) estima la volatilidad condicional: se actualiza cada día con los
            retornos recientes y reacciona a los picos de mercado. El valor mostrado está
            anualizado (√252). La volatilidad de la cartera se calcula sobre los retornos de la
            cartera (R × w), no sobre un activo aislado.
          </p>
        </div>
      </section>
    </div>
  )
}
