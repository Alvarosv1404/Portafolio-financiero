import {
  Area,
  AreaChart,
  CartesianGrid,
  Legend,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts'
import { useDashboard } from '../data/DashboardContext'
import { StatusBadge } from './StatusBadge'

export function PerformanceChart() {
  const { data } = useDashboard()
  const ytd = data.metrics.ytdReturn * 100
  return (
    <section className="panel chart-panel">
      <div className="panel-head">
        <div>
          <span className="panel-kicker">Performance</span>
          <h3>Evolución del portafolio</h3>
        </div>
        <div className="panel-tags">
          <StatusBadge tone="neutral">Base 100</StatusBadge>
          <StatusBadge tone={ytd >= 0 ? 'success' : 'danger'}>
            {ytd >= 0 ? '+' : ''}
            {ytd.toFixed(1)}% YTD
          </StatusBadge>
        </div>
      </div>

      <div className="chart-wrap">
        <ResponsiveContainer width="100%" height={310}>
          <AreaChart data={data.performance} margin={{ top: 12, right: 8, left: -18, bottom: 0 }}>
            <defs>
              <linearGradient id="portfolioFill" x1="0" y1="0" x2="0" y2="1">
                <stop offset="0%" stopColor="#2dd4bf" stopOpacity={0.32} />
                <stop offset="100%" stopColor="#2dd4bf" stopOpacity={0} />
              </linearGradient>
              <linearGradient id="benchmarkFill" x1="0" y1="0" x2="0" y2="1">
                <stop offset="0%" stopColor="#38bdf8" stopOpacity={0.18} />
                <stop offset="100%" stopColor="#38bdf8" stopOpacity={0} />
              </linearGradient>
              <linearGradient id="bondsFill" x1="0" y1="0" x2="0" y2="1">
                <stop offset="0%" stopColor="#a78bfa" stopOpacity={0.14} />
                <stop offset="100%" stopColor="#a78bfa" stopOpacity={0} />
              </linearGradient>
            </defs>
            <CartesianGrid strokeDasharray="3 3" stroke="rgba(148, 163, 184, 0.12)" vertical={false} />
            <XAxis dataKey="month" tick={{ fill: '#8b9bb4', fontSize: 11 }} axisLine={false} tickLine={false} />
            <YAxis
              domain={['auto', 'auto']}
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
              itemStyle={{ color: '#e2e8f0' }}
            />
            <Legend
              iconType="circle"
              iconSize={8}
              wrapperStyle={{ fontSize: 12, color: '#94a3b8', paddingTop: 12 }}
            />
            <Area
              type="monotone"
              dataKey="portafolio"
              name="Portafolio"
              stroke="#2dd4bf"
              strokeWidth={2.6}
              fill="url(#portfolioFill)"
              activeDot={{ r: 4 }}
            />
            <Area
              type="monotone"
              dataKey="benchmark"
              name="S&P 500"
              stroke="#38bdf8"
              strokeWidth={1.8}
              fill="url(#benchmarkFill)"
              activeDot={{ r: 3 }}
            />
            <Area
              type="monotone"
              dataKey="bonos"
              name="Bonos (rf)"
              stroke="#a78bfa"
              strokeWidth={1.6}
              fill="url(#bondsFill)"
              activeDot={{ r: 3 }}
            />
          </AreaChart>
        </ResponsiveContainer>
      </div>
    </section>
  )
}
