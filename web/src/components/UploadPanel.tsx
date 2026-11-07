import { useRef, useState } from 'react'
import type { ChangeEvent, DragEvent } from 'react'
import { CheckCircle2, Download, FileSpreadsheet, Table2, UploadCloud } from 'lucide-react'
import { StatusBadge } from './StatusBadge'

const templateCsv = [
  'date,ticker,field,value,currency,source',
  '2026-01-02,AAPL,close,185.64,USD,manual',
  '2026-01-02,ALICORC1,close,6.85,PEN,manual',
  '2026-01-02,USDPEN,rate,3.72,PEN,bcrp',
].join('\n')

export function UploadPanel() {
  const inputRef = useRef<HTMLInputElement>(null)
  const [fileName, setFileName] = useState<string | null>(null)
  const [dragging, setDragging] = useState(false)

  const handleFiles = (files: FileList | null) => {
    const file = files?.[0]
    if (file) setFileName(file.name)
  }

  const handleChange = (event: ChangeEvent<HTMLInputElement>) => {
    handleFiles(event.target.files)
  }

  const handleDrop = (event: DragEvent<HTMLDivElement>) => {
    event.preventDefault()
    setDragging(false)
    handleFiles(event.dataTransfer.files)
  }

  const downloadTemplate = () => {
    const blob = new Blob([templateCsv], { type: 'text/csv;charset=utf-8;' })
    const url = URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.download = 'plantilla_datos_manuales.csv'
    link.click()
    URL.revokeObjectURL(url)
  }

  return (
    <section className="panel">
      <div className="panel-head">
        <div>
          <span className="panel-kicker">Datos manuales</span>
          <h3>Cargar Excel / CSV</h3>
        </div>
        <StatusBadge tone="info">Próximamente</StatusBadge>
      </div>

      <div
        className={`upload-zone ${dragging ? 'dragging' : ''}`}
        onDragEnter={() => setDragging(true)}
        onDragLeave={() => setDragging(false)}
        onDragOver={(event) => event.preventDefault()}
        onDrop={handleDrop}
      >
        <span className="upload-icon">
          <UploadCloud size={28} />
        </span>
        <strong>Arrastra tu archivo aquí</strong>
        <p>Formatos permitidos: .xlsx, .xls y .csv. Útil para datos de Perú y derivados sin API.</p>
        <div className="upload-actions">
          <button type="button" className="button primary" onClick={() => inputRef.current?.click()}>
            Seleccionar archivo
          </button>
          <button type="button" className="button ghost" onClick={downloadTemplate}>
            <Download size={16} />
            Descargar plantilla
          </button>
        </div>
        <input
          ref={inputRef}
          type="file"
          accept=".xlsx,.xls,.csv"
          className="visually-hidden"
          onChange={handleChange}
        />
        {fileName && (
          <div className="upload-file">
            <FileSpreadsheet size={16} />
            <span>{fileName}</span>
            <CheckCircle2 size={16} />
          </div>
        )}
      </div>

      <div className="template-grid">
        <div>
          <div className="template-title">
            <Table2 size={16} />
            <strong>Esquema sugerido</strong>
          </div>
          <code className="schema">date, ticker, field, value, currency, source</code>
          <p>
            Permite precios, tasas, curvas y factores de derivados en un formato largo y validable.
          </p>
        </div>
        <div>
          <div className="template-title">
            <FileSpreadsheet size={16} />
            <strong>Validación pendiente</strong>
          </div>
          <p>
            La carga real se conectará cuando exista el endpoint del motor: validación de columnas,
            duplicados, moneda y fechas antes de calcular.
          </p>
        </div>
      </div>
    </section>
  )
}
