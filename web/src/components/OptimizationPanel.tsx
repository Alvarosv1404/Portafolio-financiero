import {
  CartesianGrid,
  ReferenceDot,
  ResponsiveContainer,
  Scatter,
  ScatterChart,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts'
import { Gauge, SlidersHorizontal, Sparkles, Target } from 'lucide-react'
import { assetRiskReturn, frontierData, optimalAllocation } from '../data/mockData'

const metrics = [
  { label: 'Retorno esperado', value: '13.7%', icon: Target },
  { label: 'Volatilidad', value: '10.8%', icon: Gauge },
  { label: 'Sharpe', value: '1.58', icon: Sparkles },
  { label: 'Máx. peso', value: '18.0%', icon: SlidersHorizontal },
]

export function OptimizationPanel() {
  return (
    <div className="stack">
      <div className="metric-strip">
        {metrics.map(({ label, value, icon: Icon }) => (
          <div key={label} className="metric-chip">
            <Icon size={17} />
            <div>
              <span>{label}</span>
              <strong>{value}</strong>
            </div>
          </div>
        ))}
      </div>

      <section className="panel chart-panel">
        <div className="panel-head">
          <div>
            <span className="panel-kicker">Markowitz</span>
            <h3>Frontera eficiente</h3>
          </div>
          <span className="panel-note">Riesgo vs retorno anualizado</span>
        </div>

        <div className="chart-wrap">
          <ResponsiveContainer width="100%" height={340}>
            <ScatterChart margin={{ top: 12, right: 18, left: -10, bottom: 0 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="rgba(148, 163, 184, 0.12)" />
              <XAxis
                type="number"
                dataKey="risk"
                name="Riesgo"
                unit="%"
                domain={[0, 36]}
                tick={{ fill: '#8b9bb4', fontSize: 11 }}
                axisLine={false}
                tickLine={false}
              />
              <YAxis
                type="number"
                dataKey="return"
                name="Retorno"
                unit="%"
                domain={[0, 28]}
                tick={{ fill: '#8b9bb4', fontSize: 11 }}
                axisLine={false}
                tickLine={false}
              />
              <Tooltip
                cursor={{ strokeDasharray: '3 3' }}
                contentStyle={{
                  background: '#0b1220',
                  border: '1px solid rgba(148, 163, 184, 0.2)',
                  borderRadius: 12,
                  color: '#e2e8f0',
                  fontSize: 12,
                }}
                labelStyle={{ color: '#94a3b8', marginBottom: 6 }}
              />
              <Scatter
                name="Frontera eficiente"
                data={frontierData}
                fill="#2dd4bf"
                line={{ stroke: '#2dd4bf', strokeWidth: 2 }}
              />
              <Scatter name="Activos" data={assetRiskReturn} fill="#fbbf24" />
              <ReferenceDot
                x={10.8}
                y={13.7}
                r={7}
                fill="#fb7185"
                stroke="#f8fafc"
                strokeWidth={2}
                label={{ value: 'Óptimo', fill: '#fb7185', fontSize: 11, position: 'top' }}
              />
            </ScatterChart>
          </ResponsiveContainer>
        </div>
      </section>

      <div className="two-col">
        <section className="panel">
          <div className="panel-head">
            <div>
              <span className="panel-kicker">Asignación</span>
              <h3>Portafolio óptimo</h3>
            </div>
            <span className="panel-note">Suma 100%</span>
          </div>

          <div className="allocation-list">
            {optimalAllocation.map((item) => (
              <div key={item.name} className="allocation-row">
                <div className="allocation-label">
                  <span className="allocation-dot" style={{ background: item.color }} />
                  <span>{item.name}</span>
                  <strong>{item.weight.toFixed(1)}%</strong>
                </div>
                <div className="allocation-track">
                  <span style={{ width: `${item.weight}%`, background: item.color }} />
                </div>
              </div>
            ))}
          </div>
        </section>

        <section className="panel info-panel">
          <SlidersHorizontal size={20} />
          <div>
            <strong>Restricciones del modelo</strong>
            <p>
              Sin posiciones en corto, suma de pesos igual a 1, máximo 18% por activo y covarianza con
              shrinkage para reducir el error de estimación. La frontera se calcula con datos simulados
              en esta demo; el motor Python entregará los pesos reales vía API.
            </p>
            <ul className="check-list">
              <li>Sin ventas en corto</li>
              <li>Máximo 18% por activo</li>
              <li>Covarianza Ledoit-Wolf</li>
              <li>Backtest out-of-sample</li>
            </ul>
          </div>
        </section>
      </div>
    </div>
  )
}
