import { useState } from 'react'
import { BrainCircuit, CheckCircle2, HelpCircle, XCircle } from 'lucide-react'
import { useDashboard } from '../data/DashboardContext'
import type { DashboardAssetArima } from '../data/types'
import { StatusBadge } from './StatusBadge'

function verdictTone(verdict: string): 'success' | 'info' | 'warning' {
  if (verdict === 'Sólido') return 'success'
  if (verdict === 'Aceptable') return 'info'
  return 'warning'
}

const money = new Intl.NumberFormat('en-US', {
  style: 'currency',
  currency: 'USD',
  maximumFractionDigits: 2,
})

function ProjectionRow({
  label,
  value,
  lower,
  upper,
}: {
  label: string
  value?: number
  lower?: number | null
  upper?: number | null
}) {
  return (
    <div className="arima-projection">
      <span className="proj-label">{label}</span>
      <strong>{value === undefined ? '—' : money.format(value)}</strong>
      <small>
        {lower !== undefined && lower !== null && upper !== undefined && upper !== null
          ? `IC 95%: ${money.format(lower)} – ${money.format(upper)}`
          : 'sin intervalo'}
      </small>
    </div>
  )
}

export function AssetArimaPanel() {
  const { data } = useDashboard()
  const items = data.asset_arima
  const [ticker, setTicker] = useState(items[0]?.ticker ?? '')

  const activeTicker = items.some((item) => item.ticker === ticker)
    ? ticker
    : (items[0]?.ticker ?? '')
  const selected: DashboardAssetArima | undefined =
    items.find((item) => item.ticker === activeTicker) ?? items[0]

  if (!selected) {
    return (
      <section className="panel">
        <div className="panel-head">
          <div>
            <span className="panel-kicker">ARIMA por activo</span>
            <h3>Diagnóstico individual</h3>
          </div>
          <StatusBadge tone="warning">Sin datos</StatusBadge>
        </div>
        <p className="empty-state">
          El motor todavía no devolvió el diagnóstico ARIMA de los activos. Actualiza los datos.
        </p>
      </section>
    )
  }

  const passed = selected.assumptions.filter((item) => item.passed).length
  const total = selected.assumptions.length

  return (
    <div className="stack">
      <section className="panel">
        <div className="panel-head">
          <div>
            <span className="panel-kicker">ARIMA por activo</span>
            <h3>¿Por qué el modelo es bueno? Supuestos y diagnóstico</h3>
          </div>
          <StatusBadge tone={verdictTone(selected.verdict)} dot>
            {selected.verdict}
          </StatusBadge>
        </div>

        <div className="selector-row">
          {items.map((item) => (
            <button
              key={item.ticker}
              type="button"
              className={`pill ${item.ticker === selected.ticker ? 'pill-active' : ''}`}
              onClick={() => setTicker(item.ticker)}
            >
              {item.ticker}
            </button>
          ))}
        </div>

        <div className="garch-summary">
          <div>
            <span>Activo</span>
            <strong>{selected.ticker}</strong>
          </div>
          <div>
            <span>Orden</span>
            <strong className="mono">{selected.order ?? 'Sin modelo'}</strong>
          </div>
          <div>
            <span>AIC</span>
            <strong>{selected.aic !== null ? selected.aic.toFixed(2) : '—'}</strong>
          </div>
          <div>
            <span>MAPE fuera de muestra</span>
            <strong>{selected.mape !== null ? `${selected.mape.toFixed(2)}%` : '—'}</strong>
          </div>
          <div>
            <span>Supuestos cumplidos</span>
            <strong>
              {passed}/{total}
            </strong>
          </div>
          <div>
            <span>Convergencia</span>
            <strong>{selected.converged ? 'Sí' : 'No'}</strong>
          </div>
        </div>

        <p className="arima-summary">{selected.summary}</p>

        {selected.caveats.length > 0 && (
          <ul className="check-list arima-caveats">
            {selected.caveats.map((caveat) => (
              <li key={caveat}>{caveat}</li>
            ))}
          </ul>
        )}
      </section>

      <div className="two-col">
        <section className="panel">
          <div className="panel-head">
            <div>
              <span className="panel-kicker">Supuestos</span>
              <h3>Qué se probó y qué salió</h3>
            </div>
            <span className="panel-note">Verde = cumple · Rojo = revisar</span>
          </div>

          <div className="arima-assumptions">
            {selected.assumptions.map((assumption) => (
              <div
                key={assumption.name}
                className={`assumption-row ${assumption.passed ? 'assumption-pass' : 'assumption-fail'}`}
              >
                <span className="assumption-icon">
                  {assumption.passed ? (
                    <CheckCircle2 size={17} />
                  ) : assumption.pValue === null ? (
                    <HelpCircle size={17} />
                  ) : (
                    <XCircle size={17} />
                  )}
                </span>
                <div className="assumption-copy">
                  <strong>{assumption.name}</strong>
                  <small>
                    {assumption.test} · {assumption.value}
                  </small>
                  <p>{assumption.detail}</p>
                </div>
              </div>
            ))}
          </div>
        </section>

        <section className="panel">
          <div className="panel-head">
            <div>
              <span className="panel-kicker">Proyección</span>
              <h3>Precio estimado por ARIMA</h3>
            </div>
            <span className="panel-note">Sobre log-precio</span>
          </div>

          <div className="projection-table">
            <ProjectionRow label="1 mes" value={selected.projectedPrice1m} />
            <ProjectionRow label="3 meses" value={selected.projectedPrice3m} />
            <ProjectionRow
              label="6 meses"
              value={selected.projectedPrice6m}
              lower={selected.lower6m}
              upper={selected.upper6m}
            />
          </div>

          <p className="panel-footnote">
            El intervalo se amplía con el horizonte. ARIMA pronostica la dirección estadística del
            precio, no un movimiento garantizado del mercado.
          </p>
        </section>
      </div>

      <section className="panel info-panel">
        <BrainCircuit size={20} />
        <div>
          <strong>Cómo se eligió el orden</strong>
          <p>
            Primero se decide la diferenciación con ADF y KPSS. Luego se prueba una grilla pequeña
            de combinaciones (p, d, q) y se elige la de menor AIC. El modelo se considera
            defendible cuando la serie es estacionaria, los residuos no tienen autocorrelación
            (Ljung-Box), las raíces quedan fuera del círculo unitario y el MAPE fuera de muestra
            es razonable. La normalidad y la homocedasticidad se reportan aparte porque en finanzas
            suelen fallar; para eso está GARCH.
          </p>
        </div>
      </section>
    </div>
  )
}
