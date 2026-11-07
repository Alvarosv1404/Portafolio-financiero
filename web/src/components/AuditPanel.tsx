import { AlertTriangle, CheckCircle2, Info, ShieldCheck } from 'lucide-react'
import { useDashboard } from '../data/DashboardContext'
import { StatusBadge } from './StatusBadge'

export function AuditPanel() {
  const { data } = useDashboard()
  const issues = data.auditIssues
  const warnings = data.auditChecks.filter((check) => check.status !== 'ok').length
  return (
    <div className="stack">
      <section className="panel audit-banner">
        <div className="audit-banner-icon">
          <ShieldCheck size={22} />
        </div>
        <div>
          <strong>Auditoría de datos activa</strong>
          <p>
            Se validaron {data.meta.universeSize} activos y {data.metrics.sectorsCount} sectores sobre{' '}
            {data.auditSummary.rows.toLocaleString('es-PE')} filas. Cobertura{' '}
            {(data.auditSummary.coverage * 100).toFixed(1)}% y {issues.length} observaciones
            registradas.
          </p>
        </div>
        <StatusBadge tone={warnings ? 'warning' : 'success'} dot>
          {warnings ? `${warnings} alertas` : 'Sin alertas'}
        </StatusBadge>
      </section>

      <section className="panel">
        <div className="panel-head">
          <div>
            <span className="panel-kicker">Controles</span>
            <h3>Chequeos de calidad</h3>
          </div>
          <span className="panel-note">{data.auditChecks.length} controles</span>
        </div>

        <div className="audit-grid">
          {data.auditChecks.map((check) => {
            const ok = check.status === 'ok'
            const Icon = ok ? CheckCircle2 : AlertTriangle
            return (
              <article key={check.name} className={`audit-check ${ok ? 'ok' : 'warning'}`}>
                <Icon size={18} />
                <div>
                  <span>{check.name}</span>
                  <strong>{check.value}</strong>
                  <small>{check.detail}</small>
                </div>
              </article>
            )
          })}
        </div>
      </section>

      <section className="panel">
        <div className="panel-head">
          <div>
            <span className="panel-kicker">Incidencias</span>
            <h3>Observaciones detectadas</h3>
          </div>
          <StatusBadge tone="neutral">{issues.length} registros</StatusBadge>
        </div>

        <div className="table-wrap">
          <table>
            <thead>
              <tr>
                <th>ID</th>
                <th>Activo</th>
                <th>Tipo</th>
                <th>Severidad</th>
                <th>Detalle</th>
                <th className="num">Fecha</th>
              </tr>
            </thead>
            <tbody>
              {issues.map((issue) => (
                <tr key={issue.id}>
                  <td className="mono">{issue.id}</td>
                  <td>
                    <strong>{issue.ticker}</strong>
                  </td>
                  <td>{issue.type}</td>
                  <td>
                    <StatusBadge
                      tone={
                        issue.severity === 'Alta'
                          ? 'danger'
                          : issue.severity === 'Media'
                            ? 'warning'
                            : 'info'
                      }
                    >
                      {issue.severity}
                    </StatusBadge>
                  </td>
                  <td className="muted">{issue.detail}</td>
                  <td className="num mono">{issue.date}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>

      <section className="panel info-panel">
        <Info size={20} />
        <div>
          <strong>¿Por qué importa el sesgo de supervivencia?</strong>
          <p>
            El universo usa empresas que hoy cotizan. Un backtest con esa lista elimina a las empresas
            que quebraron o salieron del índice, por lo que el rendimiento pasado puede verse mejor de
            lo que realmente fue. La solución es usar constituyentes históricos (point-in-time) o
            documentar la limitación en los reportes.
          </p>
        </div>
      </section>
    </div>
  )
}
