import {
  Area,
  CartesianGrid,
  ComposedChart,
  Legend,
  Line,
  ReferenceLine,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts'
import { BrainCircuit, CalendarRange, Crosshair, Percent } from 'lucide-react'
import { forecastSeries } from '../data/mockData'

const metrics = [
  { label: 'Modelo', value: 'ARIMA(2,1,2)', icon: BrainCircuit },
  { label: 'AIC', value: '1842.6', icon: Crosshair },
  { label: 'MAPE', value: '3.8%', icon: Percent },
  { label: 'Horizonte', value: '6 meses', icon: CalendarRange },
]

export function ForecastPanel() {
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
            <span className="panel-kicker">Pronóstico</span>
            <h3>ARIMA sobre retornos logarítmicos</h3>
          </div>
          <span className="panel-note">Intervalo de confianza 95%</span>
        </div>

        <div className="chart-wrap">
          <ResponsiveContainer width="100%" height={330}>
            <ComposedChart data={forecastSeries} margin={{ top: 12, right: 8, left: -18, bottom: 0 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="rgba(148, 163, 184, 0.12)" vertical={false} />
              <XAxis dataKey="date" tick={{ fill: '#8b9bb4', fontSize: 11 }} axisLine={false} tickLine={false} />
              <YAxis
                domain={[104, 124]}
                tick={{ fill: '#8b9bb4', fontSize: 11 }}
                axisLine={false}
                tickLine={false}
                tickFormatter={(value) => String(value)}
              />
              <Tooltip
                contentStyle={{
                  background: '#0b1220',
                  border: '1px solid rgba(148, 163, 184, 0.2)',
                  borderRadius: 12,
                  color: '#e2e8f0',
                  fontSize: 12,
                }}
                labelStyle={{ color: '#94a3b8', marginBottom: 6 }}
              />
              <Legend
                iconType="circle"
                iconSize={8}
                wrapperStyle={{ fontSize: 12, color: '#94a3b8', paddingTop: 12 }}
              />
              <Area dataKey="lower" stackId="band" stroke="none" fill="transparent" />
              <Area
                dataKey="range"
                stackId="band"
                stroke="none"
                fill="#38bdf8"
                fillOpacity={0.12}
                name="Banda 95%"
              />
              <Line
                type="monotone"
                dataKey="actual"
                name="Histórico"
                stroke="#2dd4bf"
                strokeWidth={2.6}
                dot={false}
                connectNulls={false}
              />
              <Line
                type="monotone"
                dataKey="forecast"
                name="Pronóstico"
                stroke="#38bdf8"
                strokeWidth={2.4}
                strokeDasharray="6 4"
                dot={false}
                connectNulls={false}
              />
              <ReferenceLine
                x="Dic"
                stroke="rgba(148, 163, 184, 0.45)"
                strokeDasharray="4 4"
                label={{ value: 'Hoy', fill: '#94a3b8', fontSize: 11, position: 'insideTopRight' }}
              />
            </ComposedChart>
          </ResponsiveContainer>
        </div>
      </section>

      <section className="panel info-panel">
        <BrainCircuit size={20} />
        <div>
          <strong>Buenas prácticas aplicadas</strong>
          <p>
            El modelo se entrena con retornos logarítmicos, no con precios en niveles. Se valida con
            ventanas walk-forward y se reporta MAPE fuera de muestra. En la siguiente fase se conectará
            con statsmodels y se comparará contra un baseline naive.
          </p>
        </div>
      </section>
    </div>
  )
}
