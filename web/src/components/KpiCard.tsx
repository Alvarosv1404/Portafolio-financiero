import type { LucideIcon } from 'lucide-react'
import { ArrowDownRight, ArrowUpRight, Minus } from 'lucide-react'

type Tone = 'teal' | 'blue' | 'violet' | 'amber' | 'rose' | 'slate'
type Trend = 'up' | 'down' | 'flat'

interface KpiCardProps {
  label: string
  value: string
  icon: LucideIcon
  tone?: Tone
  delta?: string
  deltaLabel?: string
  trend?: Trend
}

const trendIcons = {
  up: ArrowUpRight,
  down: ArrowDownRight,
  flat: Minus,
}

export function KpiCard({
  label,
  value,
  icon: Icon,
  tone = 'teal',
  delta,
  deltaLabel,
  trend = 'flat',
}: KpiCardProps) {
  const TrendIcon = trendIcons[trend]
  return (
    <article className={`kpi-card kpi-${tone}`}>
      <div className="kpi-top">
        <span className="kpi-icon">
          <Icon size={19} strokeWidth={1.8} />
        </span>
        {delta && (
          <span className={`kpi-delta kpi-delta-${trend}`}>
            <TrendIcon size={14} />
            {delta}
          </span>
        )}
      </div>
      <p className="kpi-label">{label}</p>
      <strong className="kpi-value">{value}</strong>
      {deltaLabel && <span className="kpi-delta-label">{deltaLabel}</span>}
    </article>
  )
}
