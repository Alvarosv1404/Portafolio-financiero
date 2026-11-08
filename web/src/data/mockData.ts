import type { AuditCheck } from './types'

export type Signal = 'Comprar' | 'Mantener' | 'Vigilar' | 'Reducir'
export type ProviderStatus = 'connected' | 'fallback' | 'limited'

export interface Asset {
  ticker: string
  name: string
  sector: string
  price: number
  change: number
  weight: number
  signal: Signal
  forecast: string
}

export interface Provider {
  name: string
  role: string
  status: ProviderStatus
  latency: string
  coverage: string
  limit: string
  note: string
}

export const portfolioSeries = [
  { month: 'Ene', portafolio: 100.0, benchmark: 100.0, bonos: 100.0 },
  { month: 'Feb', portafolio: 102.4, benchmark: 101.1, bonos: 100.6 },
  { month: 'Mar', portafolio: 101.2, benchmark: 100.4, bonos: 101.1 },
  { month: 'Abr', portafolio: 104.6, benchmark: 102.8, bonos: 101.5 },
  { month: 'May', portafolio: 106.1, benchmark: 103.9, bonos: 101.9 },
  { month: 'Jun', portafolio: 105.4, benchmark: 104.2, bonos: 102.3 },
  { month: 'Jul', portafolio: 108.8, benchmark: 105.0, bonos: 102.7 },
  { month: 'Ago', portafolio: 110.2, benchmark: 105.8, bonos: 103.0 },
  { month: 'Sep', portafolio: 109.5, benchmark: 106.1, bonos: 103.3 },
  { month: 'Oct', portafolio: 112.7, benchmark: 107.0, bonos: 103.7 },
  { month: 'Nov', portafolio: 113.8, benchmark: 107.6, bonos: 103.9 },
  { month: 'Dic', portafolio: 114.8, benchmark: 108.2, bonos: 104.1 },
]

export const sectorData = [
  { sector: 'Information Technology', short: 'Tech', weight: 24.8, return: 18.2, color: '#2dd4bf' },
  { sector: 'Financials', short: 'Finanzas', weight: 15.2, return: 12.4, color: '#38bdf8' },
  { sector: 'Health Care', short: 'Salud', weight: 12.4, return: 8.9, color: '#818cf8' },
  { sector: 'Consumer Discretionary', short: 'Consumo', weight: 11.1, return: 10.1, color: '#a78bfa' },
  { sector: 'Industrials', short: 'Industrial', weight: 9.6, return: 9.4, color: '#fbbf24' },
  { sector: 'Communication Services', short: 'Comunicación', weight: 8.7, return: 14.6, color: '#fb7185' },
  { sector: 'Consumer Staples', short: 'Staples', weight: 6.3, return: 5.2, color: '#34d399' },
  { sector: 'Utilities', short: 'Utilities', weight: 4.2, return: 4.1, color: '#22d3ee' },
  { sector: 'Materials', short: 'Materiales', weight: 3.4, return: 6.8, color: '#f472b6' },
  { sector: 'Energy', short: 'Energía', weight: 2.9, return: 7.3, color: '#f59e0b' },
  { sector: 'Real Estate', short: 'Real Estate', weight: 1.4, return: 3.6, color: '#94a3b8' },
]

export const assets: Asset[] = [
  { ticker: 'NVDA', name: 'NVIDIA', sector: 'Information Technology', price: 187.42, change: 2.84, weight: 6.8, signal: 'Comprar', forecast: '+8.4%' },
  { ticker: 'MSFT', name: 'Microsoft', sector: 'Information Technology', price: 512.16, change: 0.92, weight: 6.1, signal: 'Comprar', forecast: '+4.2%' },
  { ticker: 'AAPL', name: 'Apple', sector: 'Information Technology', price: 268.74, change: -0.41, weight: 5.4, signal: 'Mantener', forecast: '+1.8%' },
  { ticker: 'JPM', name: 'JPMorgan Chase', sector: 'Financials', price: 284.35, change: 1.17, weight: 3.9, signal: 'Mantener', forecast: '+2.6%' },
  { ticker: 'LLY', name: 'Eli Lilly', sector: 'Health Care', price: 921.58, change: 1.63, weight: 3.5, signal: 'Comprar', forecast: '+5.1%' },
  { ticker: 'AMZN', name: 'Amazon', sector: 'Consumer Discretionary', price: 241.09, change: -0.76, weight: 3.2, signal: 'Vigilar', forecast: '-0.9%' },
  { ticker: 'GOOGL', name: 'Alphabet', sector: 'Communication Services', price: 219.87, change: 0.58, weight: 3.0, signal: 'Mantener', forecast: '+2.1%' },
  { ticker: 'XOM', name: 'Exxon Mobil', sector: 'Energy', price: 118.42, change: -1.24, weight: 1.8, signal: 'Reducir', forecast: '-2.7%' },
]

export const providers: Provider[] = [
  { name: 'yfinance', role: 'Histórico masivo', status: 'connected', latency: '1.2 s', coverage: '98.4%', limit: 'Sin límite oficial', note: '503 activos' },
  { name: 'Finnhub', role: 'Tiempo real + websocket', status: 'connected', latency: '240 ms', coverage: '100%', limit: '60 req/min', note: 'Mercado EE. UU.' },
  { name: 'Twelve Data', role: 'Fallback multi-activo', status: 'fallback', latency: '890 ms', coverage: '99.1%', limit: '8 req/min', note: 'Plan gratuito' },
  { name: 'Tiingo', role: 'Validación EOD', status: 'connected', latency: '1.5 s', coverage: '97.8%', limit: '500 req/día', note: 'Contraste de precios' },
  { name: 'Alpha Vantage', role: 'Pruebas puntuales', status: 'limited', latency: '2.1 s', coverage: '94.2%', limit: '25 req/día', note: 'No apto como base' },
  { name: 'Marketstack', role: 'EOD secundario', status: 'limited', latency: '2.8 s', coverage: '92.6%', limit: '100 req/mes', note: 'Cobertura limitada' },
]

export const providerComparison = [
  { provider: 'yfinance', coverage: '98.4%', missingDays: '3', diff: '—', latency: '1.2 s', verdict: 'Base histórica' },
  { provider: 'Finnhub', coverage: '100%', missingDays: '0', diff: '0.02%', latency: '240 ms', verdict: 'Tiempo real' },
  { provider: 'Twelve Data', coverage: '99.1%', missingDays: '1', diff: '0.05%', latency: '890 ms', verdict: 'Fallback' },
  { provider: 'Tiingo', coverage: '97.8%', missingDays: '4', diff: '0.01%', latency: '1.5 s', verdict: 'Validación' },
]

export const auditChecks: AuditCheck[] = [
  { name: 'Duplicados', value: '0', status: 'ok', detail: 'Sin fechas repetidas' },
  { name: 'Precios inválidos', value: '0', status: 'ok', detail: 'Sin valores <= 0' },
  { name: 'Gaps de fechas', value: '3', status: 'warning', detail: '3 días sin cotización' },
  { name: 'Outliers', value: '2', status: 'warning', detail: 'Retornos > 5σ' },
  { name: 'Splits / dividendos', value: '1', status: 'warning', detail: '1 ajuste detectado' },
  { name: 'Cobertura', value: '98.4%', status: 'ok', detail: '495 / 503 activos' },
]

export const auditIssues = [
  { id: 'GAP-001', ticker: 'FOX', type: 'Gap de fechas', severity: 'Media', detail: '3 días sin cotización', date: '2026-10-14' },
  { id: 'OUT-002', ticker: 'NVDA', type: 'Outlier de retorno', severity: 'Baja', detail: 'Retorno +5.4% (5.2σ)', date: '2026-09-22' },
  { id: 'SPL-003', ticker: 'AAPL', type: 'Split detectado', severity: 'Media', detail: 'Ajuste 4:1 pendiente de validar', date: '2026-08-31' },
  { id: 'OUT-004', ticker: 'XOM', type: 'Outlier de retorno', severity: 'Baja', detail: 'Retorno -4.8% (4.7σ)', date: '2026-07-18' },
]

export const forecastSeries = [
  { date: 'Jul', actual: 108.8, forecast: null, lower: null, range: null },
  { date: 'Ago', actual: 110.2, forecast: null, lower: null, range: null },
  { date: 'Sep', actual: 109.5, forecast: null, lower: null, range: null },
  { date: 'Oct', actual: 112.7, forecast: null, lower: null, range: null },
  { date: 'Nov', actual: 113.8, forecast: null, lower: null, range: null },
  { date: 'Dic', actual: 114.8, forecast: 114.8, lower: 114.8, range: 0 },
  { date: 'Ene', actual: null, forecast: 116.1, lower: 114.2, range: 1.9 },
  { date: 'Feb', actual: null, forecast: 117.4, lower: 114.6, range: 2.8 },
  { date: 'Mar', actual: null, forecast: 118.2, lower: 114.8, range: 3.4 },
  { date: 'Abr', actual: null, forecast: 119.1, lower: 115.0, range: 4.1 },
  { date: 'May', actual: null, forecast: 120.3, lower: 115.2, range: 5.1 },
  { date: 'Jun', actual: null, forecast: 121.4, lower: 115.4, range: 6.0 },
]

export const frontierData = [
  { risk: 8.1, return: 6.4, label: 'Conservador' },
  { risk: 9.0, return: 8.2, label: 'Defensivo' },
  { risk: 10.8, return: 13.7, label: 'Óptimo' },
  { risk: 11.9, return: 14.8, label: 'Balanceado' },
  { risk: 13.6, return: 15.9, label: 'Crecimiento' },
  { risk: 15.8, return: 17.0, label: 'Agresivo' },
  { risk: 18.4, return: 18.1, label: 'Máximo retorno' },
]

export const assetRiskReturn = [
  { ticker: 'NVDA', risk: 32.4, return: 24.2, weight: 6.8 },
  { ticker: 'MSFT', risk: 22.1, return: 16.8, weight: 6.1 },
  { ticker: 'AAPL', risk: 20.4, return: 13.1, weight: 5.4 },
  { ticker: 'JPM', risk: 18.7, return: 11.6, weight: 3.9 },
  { ticker: 'LLY', risk: 24.6, return: 18.4, weight: 3.5 },
  { ticker: 'AMZN', risk: 26.2, return: 15.2, weight: 3.2 },
  { ticker: 'GOOGL', risk: 21.8, return: 14.0, weight: 3.0 },
  { ticker: 'XOM', risk: 19.2, return: 8.4, weight: 1.8 },
]

export const optimalAllocation = [
  { name: 'Information Technology', weight: 24.8, color: '#2dd4bf' },
  { name: 'Financials', weight: 15.2, color: '#38bdf8' },
  { name: 'Health Care', weight: 12.4, color: '#818cf8' },
  { name: 'Consumer Discretionary', weight: 11.1, color: '#a78bfa' },
  { name: 'Industrials', weight: 9.6, color: '#fbbf24' },
  { name: 'Communication Services', weight: 8.7, color: '#fb7185' },
  { name: 'Otros', weight: 18.2, color: '#94a3b8' },
]
