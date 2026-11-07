import type { ReactNode } from 'react'

export type BadgeTone = 'success' | 'warning' | 'danger' | 'info' | 'neutral'

interface StatusBadgeProps {
  children: ReactNode
  tone?: BadgeTone
  dot?: boolean
}

export function StatusBadge({ children, tone = 'neutral', dot = false }: StatusBadgeProps) {
  return (
    <span className={`badge badge-${tone}`}>
      {dot && <span className="badge-dot" />}
      {children}
    </span>
  )
}
