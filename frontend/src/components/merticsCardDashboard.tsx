import { useEffect, useState } from 'react'
import { fetchMetrics } from '../api'
import MetricsCard, { type MetricsCardIcon } from './merticsCard'
import styles from './merticsCardDashboard.module.css'

type CardRow = { title: string; value: string; icon: MetricsCardIcon }

/** Fixed order for a 2×2 grid (matches API labels from `fetchMetrics`). */
const CANONICAL_METRICS: { title: string; icon: MetricsCardIcon }[] = [
  { title: 'Fill rate', icon: 'fill_rate' },
  { title: 'On-time delivery', icon: 'on_time_delivery' },
  { title: 'Overall risk score', icon: 'overall_risk_score' },
  { title: 'Stockout rate', icon: 'stockout_rate' },
]

function mergeToFour(rows: CardRow[]): CardRow[] {
  const map = new Map(rows.map((r) => [r.title, r]))
  return CANONICAL_METRICS.map((c) => map.get(c.title) ?? { title: c.title, value: '—', icon: c.icon })
}

const PLACEHOLDER_ROWS: CardRow[] = CANONICAL_METRICS.map((c) => ({
  ...c,
  value: '…',
}))

function iconForMetric(metric: string): MetricsCardIcon {
  switch (metric) {
    case 'Fill rate':
      return 'fill_rate'
    case 'On-time delivery':
      return 'on_time_delivery'
    case 'Overall risk score':
      return 'overall_risk_score'
    case 'Stockout rate':
      return 'stockout_rate'
    default:
      return 'overall_risk_score'
  }
}

/** Backend sends rates in 0–1; show as a percentage when in that range. */
function formatKpiDisplay(value: number): string {
  if (!Number.isFinite(value)) return '—'
  if (value >= 0 && value <= 1) {
    return `${(value * 100).toFixed(1)}%`
  }
  return value.toFixed(1)
}

function rowsFromApi(
  data: { metric: string; value: number }[],
): CardRow[] {
  return data.map((m) => ({
    title: m.metric,
    value: formatKpiDisplay(m.value),
    icon: iconForMetric(m.metric),
  }))
}

export default function MetricsCardDashboard() {
  const [rows, setRows] = useState<CardRow[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    let cancelled = false
    async function load() {
      setLoading(true)
      setError(null)
      try {
        const data = await fetchMetrics()
        if (cancelled) return
        setRows(rowsFromApi(data))
      } catch (e) {
        if (!cancelled) {
          setError(e instanceof Error ? e.message : 'Failed to load metrics')
          setRows([])
        }
      } finally {
        if (!cancelled) setLoading(false)
      }
    }
    void load()
    return () => {
      cancelled = true
    }
  }, [])

  const displayRows =
    loading && rows.length === 0 ? PLACEHOLDER_ROWS : mergeToFour(rows)
  const cardError = loading ? null : error

  return (
    <section className={styles.section} aria-label="Metrics">
      <div className={styles.metricsCards}>
        {displayRows.map((row) => (
          <MetricsCard key={row.title} title={row.title} value={row.value} icon={row.icon} />
        ))}
      </div>
      {cardError ? (
        <p className={styles.error} role="alert">
          {cardError}
        </p>
      ) : null}
    </section>
  )
}
