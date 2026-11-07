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
import { useDashboard } from '../data/DashboardContext'

export function ForecastPanel() {
  const { data } = useDashboard()
  const forecast = data.forecast
  const metrics = [
    { label: 'Modelo', value: forecast.model, icon: BrainCircuit },
    { label: 'AIC', value: forecast.aic !== null ? forecast.aic.toLocaleString('es-PE') : '—', icon: Crosshair },
    { label: 'MAPE', value: forecast.mape !== null ? `${forecast.mape.toFixed(1)}%` : '—', icon: Percent },
    { label: 'Horizonte', value: `${forecast.horizonMonths} meses`, icon: CalendarRange },
  ]
  const lastActual = [...forecast.series].reverse().find((point) => point.actual !== null)
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
            <ComposedChart data={forecast.series} margin={{ top: 12, right: 8, left: -18, bottom: 0 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="rgba(148, 163, 184, 0.12)" vertical={false} />
              <XAxis dataKey="date" tick={{ fill: '#8b9bb4', fontSize: 11 }} axisLine={false} tickLine={false} />
              <YAxis
                domain={['auto', 'auto']}
                tick={{ fill: '#8b9bb4', fontSize: 11 }}
                axisLine={false}
                tickLine={false}
                tickFormatter={(value) => String(Math.round(Number(value)))}
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
                x={lastActual?.date}
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
            El modelo se entrena con el logaritmo del precio del portafolio y se valida con una
            partición fuera de muestra para reportar MAPE. Por la naturaleza de ARIMA sobre precios, el
            pronóstico converge al último nivel y la banda se amplía con el horizonte. No es una
            predicción de mercado: es una referencia estadística.
          </p>
          {forecast.usedFallback && (
            <p>
              En esta ejecución ARIMA no convergió y se usó el pronóstico ingenuo (último valor
              conocido). Revisa la sección de auditoría o vuelve a actualizar los datos.
            </p>
          )}
        </div>
      </section>
    </div>
  )
}
