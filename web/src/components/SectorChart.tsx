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
import { sectorData } from '../data/mockData'

export function SectorChart() {
  return (
    <section className="panel">
      <div className="panel-head">
        <div>
          <span className="panel-kicker">Distribución</span>
          <h3>Peso por sector</h3>
        </div>
        <span className="panel-note">11 sectores</span>
      </div>

      <div className="chart-wrap">
        <ResponsiveContainer width="100%" height={300}>
          <BarChart data={sectorData} layout="vertical" margin={{ top: 4, right: 16, left: 4, bottom: 0 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="rgba(148, 163, 184, 0.1)" horizontal={false} />
            <XAxis type="number" hide domain={[0, 28]} />
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
              {sectorData.map((sector) => (
                <Cell key={sector.sector} fill={sector.color} />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </div>
    </section>
  )
}
