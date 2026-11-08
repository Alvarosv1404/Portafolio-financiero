export type Signal = 'Comprar' | 'Mantener' | 'Vigilar' | 'Reducir'
export type ProviderStatus = 'connected' | 'fallback' | 'limited'
export type CheckStatus = 'ok' | 'warning' | 'danger'
export type ProfileName = 'bajo_riesgo' | 'moderado' | 'ideal' | 'riesgoso' | 'total'

export interface Asset {
  ticker: string
  name: string
  sector: string
  price: number
  change: number
  weight: number
  signal: Signal
  forecast: string
  annualReturn?: number
  mu_sharpe?: number
  mu_score?: number
  momentum_21d?: number
  score?: number
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

export interface ProviderComparisonRow {
  provider: string
  coverage: string
  missingDays: string
  diff: string
  latency: string
  verdict: string
}

export interface AuditCheck {
  name: string
  value: string
  status: CheckStatus
  detail: string
}

export interface AuditIssue {
  id: string
  ticker: string
  type: string
  severity: string
  detail: string
  date: string
}

export interface PerformancePoint {
  month: string
  portafolio: number
  benchmark: number
  bonos: number
}

export interface SectorRow {
  sector: string
  short: string
  weight: number
  return: number
  color: string
}

export interface ForecastPoint {
  date: string
  actual: number | null
  forecast: number | null
  lower: number | null
  range: number | null
}

export interface FrontierPoint {
  risk: number
  return: number
  label?: string | null
}

export interface AssetRiskReturn {
  ticker: string
  risk: number
  return: number
  weight: number
}

export interface AllocationRow {
  name: string
  weight: number
  color: string
}

export interface ProfileSummary {
  weights: Record<string, number>
  expectedReturn: number
  volatility: number
  sharpe: number
}

export interface DashboardMeta {
  generatedAt: string
  isLive: boolean
  stale: boolean
  cached: boolean
  source: string
  benchmark: string
  start: string
  end: string
  universeSize: number
  requestedUniverse: string[]
  dropped: string[]
  warnings: string[]
  riskFreeRate: number
  maxWeight: number
  capital: number
  downloadMs: number
  profiles?: Partial<Record<ProfileName, ProfileSummary>>
  top10?: string[]
}

export interface DashboardGarch {
  portfolioVolatility: {
    final: number
    path: number[]
  }
  perAsset: {
    [ticker: string]: {
      finalVolatility: number
      unconditionalVolatility?: number
      conditionalVolatility: number[]
    }
  }
}

export interface InvestmentResult {
  ticker: string
  name: string
  currentPrice: number
  sharesAffordable: number
  residualCash: number
  investment1m: number | null
  investment3m: number | null
  investment6m: number | null
  projectedPrice1m: number | null
  projectedPrice3m: number | null
  projectedPrice6m: number | null
  signal: Signal
}

export interface DashboardOptimization {
  expectedReturn: number
  volatility: number
  sharpe: number
  maxWeight: number
  positions: number
}

export interface ArimaAssumption {
  name: string
  test: string
  value: string
  pValue: number | null
  passed: boolean
  detail: string
}

export interface DashboardAssetArima {
  ticker: string
  order: string | null
  orderValues: number[] | null
  aic: number | null
  mape: number | null
  converged: boolean
  verdict: string
  summary: string
  assumptions: ArimaAssumption[]
  caveats: string[]
  passedCount?: number
  total?: number
  projectedPrice1m?: number
  projectedPrice3m?: number
  projectedPrice6m?: number
  lower6m?: number | null
  upper6m?: number | null
}

export interface DashboardMetrics {
  portfolioValue: number
  annualReturn: number
  ytdReturn: number
  volatility: number
  sharpe: number
  maxDrawdown: number
  universeSize: number
  sectorsCount: number
  benchmarkReturn: number
  benchmarkVolatility: number
  excessReturn: number
  excessVolatility: number
  capital: number
  riskFreeRate: number
  expectedReturn: number
  expectedVolatility: number
  maxWeight: number
}

export interface DashboardData {
  meta: DashboardMeta
  metrics: DashboardMetrics
  performance: PerformancePoint[]
  sectors: SectorRow[]
  assets: Asset[]
  providers: Provider[]
  providerComparison: ProviderComparisonRow[]
  auditChecks: AuditCheck[]
  auditIssues: AuditIssue[]
  auditSummary: {
    coverage: number
    missingDays: number
    outliers: number
    largeMoves: number
    rows: number
    cells: number
  }
  forecast: {
    series: ForecastPoint[]
    model: string
    aic: number | null
    mape: number | null
    horizonMonths: number
    usedFallback: boolean
  }
  frontier: FrontierPoint[]
  assetRiskReturn: AssetRiskReturn[]
  allocation: AllocationRow[]
  optimization: DashboardOptimization
  garch: DashboardGarch
  investment: InvestmentResult[]
  asset_arima: DashboardAssetArima[]
}
