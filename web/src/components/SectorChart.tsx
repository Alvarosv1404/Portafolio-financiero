import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts'
import { useDashboard } from '../data/DashboardContext'

export function SectorChart() {
  const { data } = useDashboard()
  const sectors = data.sectors
  const maxWeight = Math.max(...sectors.map((sector) => sector.weight), 1)
  return (
    <section className="panel">
      <div className="panel-head">
        <div>
          <span className="panel-kicker">Distribución</span>
          <h3>Peso por sector</h3>
        </div>
        <span className="panel-note">{sectors.length} sectores</span>
      </div>

      <div className="chart-wrap">
        <ResponsiveContainer width="100%" height={300}>
          <BarChart data={sectors} layout="vertical" margin={{ top: 4, right: 16, left: 4, bottom: 0 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="rgba(148, 163, 184, 0.1)" horizontal={false} />
            <XAxis type="number" hide domain={[0, Math.ceil(maxWeight * 1.15)]} />
            <YAxis
              type="category"
              dataKey="short"
              width={82}
              tick={{ fill: '#8b9bb4', fontSize: 11 }}
              axisLine={false}
              tickLine={false}
            />
            <Tooltip
              cursor={{ fill: 'rgba(148, 163, 184, 0.06)' }}
              contentStyle={{
                background: '#0b1220',
                border: '1px solid rgba(148, 163, 184, 0.2)',
                borderRadius: 12,
                color: '#e2e8f0',
                fontSize: 12,
              }}
              formatter={(value) => [`${value}%`, 'Peso']}
            />
            <Bar dataKey="weight" radius={[0, 8, 8, 0]} barSize={13}>
              {sectors.map((sector) => (
                <Cell key={sector.sector} fill={sector.color} />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </div>
    </section>
  )
}
