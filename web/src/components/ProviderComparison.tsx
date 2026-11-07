import { useDashboard } from '../data/DashboardContext'
import { StatusBadge } from './StatusBadge'

export function ProviderComparison() {
  const { data } = useDashboard()
  return (
    <section className="panel">
      <div className="panel-head">
        <div>
          <span className="panel-kicker">Benchmark</span>
          <h3>Comparación de proveedores</h3>
        </div>
        <StatusBadge tone="info">Misma ventana · 12 meses</StatusBadge>
      </div>

      <div className="table-wrap">
        <table>
          <thead>
            <tr>
              <th>Proveedor</th>
              <th className="num">Cobertura</th>
              <th className="num">Días faltantes</th>
              <th className="num">Diferencia vs base</th>
              <th className="num">Latencia</th>
              <th>Veredicto</th>
            </tr>
          </thead>
          <tbody>
            {data.providerComparison.map((row) => (
              <tr key={row.provider}>
                <td>
                  <strong>{row.provider}</strong>
                </td>
                <td className="num">{row.coverage}</td>
                <td className="num">{row.missingDays}</td>
                <td className="num">{row.diff}</td>
                <td className="num">{row.latency}</td>
                <td>
                  <StatusBadge tone={row.verdict === 'Base histórica' ? 'success' : 'neutral'}>
                    {row.verdict}
                  </StatusBadge>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </section>
  )
}
