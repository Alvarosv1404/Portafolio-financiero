import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useRef,
  useState,
} from 'react'
import type { ReactNode } from 'react'
import { mockDashboard } from './mockDashboard'
import type { DashboardData } from './types'

type DataStatus = 'loading' | 'live' | 'offline'

interface DashboardContextValue {
  data: DashboardData
  status: DataStatus
  error: string | null
  refreshing: boolean
  lastFetched: Date | null
  refresh: () => void
}

const DashboardContext = createContext<DashboardContextValue | null>(null)

const API_URL = import.meta.env.VITE_API_URL ?? '/api/dashboard'
const AUTO_REFRESH_MS = 5 * 60 * 1000

export function DashboardProvider({ children }: { children: ReactNode }) {
  const [data, setData] = useState<DashboardData>(mockDashboard)
  const [status, setStatus] = useState<DataStatus>('loading')
  const [error, setError] = useState<string | null>(null)
  const [refreshing, setRefreshing] = useState(false)
  const [lastFetched, setLastFetched] = useState<Date | null>(null)
  const mounted = useRef(true)

  const load = useCallback(async (force: boolean) => {
    setRefreshing(true)
    setError(null)
    const controller = new AbortController()
    const timeout = window.setTimeout(() => controller.abort(), 180_000)
    try {
      const url = force ? `${API_URL}?refresh=true` : API_URL
      const response = await fetch(url, { signal: controller.signal })
      if (!response.ok) {
        throw new Error(`La API respondió ${response.status}`)
      }
      const payload = (await response.json()) as DashboardData
      if (!mounted.current) return
      setData(payload)
      setStatus(payload.meta.isLive ? 'live' : 'offline')
      setLastFetched(new Date())
      if (!payload.meta.isLive && payload.meta.warnings.length) {
        setError(payload.meta.warnings[payload.meta.warnings.length - 1])
      }
    } catch (caught) {
      if (!mounted.current) return
      const message =
        caught instanceof DOMException && caught.name === 'AbortError'
          ? 'La descarga tardó más de 3 minutos.'
          : caught instanceof Error
            ? caught.message
            : 'No se pudo conectar con el motor.'
      setError(message)
      setStatus('offline')
    } finally {
      window.clearTimeout(timeout)
      if (mounted.current) setRefreshing(false)
    }
  }, [])

  useEffect(() => {
    mounted.current = true
    void load(false)
    const interval = window.setInterval(() => void load(false), AUTO_REFRESH_MS)
    return () => {
      mounted.current = false
      window.clearInterval(interval)
    }
  }, [load])

  const refresh = useCallback(() => {
    void load(true)
  }, [load])

  const value = useMemo(
    () => ({ data, status, error, refreshing, lastFetched, refresh }),
    [data, status, error, refreshing, lastFetched, refresh],
  )

  return <DashboardContext.Provider value={value}>{children}</DashboardContext.Provider>
}

export function useDashboard() {
  const context = useContext(DashboardContext)
  if (!context) {
    throw new Error('useDashboard debe usarse dentro de DashboardProvider.')
  }
  return context
}
