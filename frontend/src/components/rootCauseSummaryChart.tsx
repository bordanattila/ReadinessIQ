import type { ReactElement } from 'react'
import { useEffect, useMemo, useState } from 'react'
import { fetchRootCauseSummary, type RootCauseSummaryRow } from '../api'
import styles from './rootCauseSummaryChart.module.css'

type DriverKey =
  | 'inventory_policy_signals'
  | 'maintenance_demand_signals'
  | 'supplier_delay_signals'
  | 'reactive_site_order_signals'

type DriverRow = {
  key: DriverKey
  label: string
  color: string
  count: number
  pct: number
}

function IconClipboard() {
  return (
    <svg className={styles.glyph} viewBox="0 0 24 24" aria-hidden>
      <path
        fill="none"
        stroke="currentColor"
        strokeWidth="2"
        strokeLinejoin="round"
        d="M9 5H7a2 2 0 0 0-2 2v12a2 2 0 0 0 2 2h10a2 2 0 0 0 2-2V7a2 2 0 0 0-2-2h-2M9 5a2 2 0 0 0 2 2h2a2 2 0 0 0 2-2M9 5a2 2 0 0 1 2-2h2a2 2 0 0 1 2 2"
      />
    </svg>
  )
}

function IconWrench() {
  return (
    <svg className={styles.glyph} viewBox="0 0 24 24" aria-hidden>
      <path
        fill="none"
        stroke="currentColor"
        strokeWidth="2"
        strokeLinecap="round"
        d="M14.7 6.3a1 1 0 0 0 0 1.4l1.6 1.6a1 1 0 0 0 1.4 0l3.77-3.77a6 6 0 0 1-7.94 7.94l-6.91 6.91a2.12 2.12 0 0 1-3-3l6.91-6.91a6 6 0 0 1 7.94-7.94l-3.76 3.76z"
      />
    </svg>
  )
}

function IconTruck() {
  return (
    <svg className={styles.glyph} viewBox="0 0 24 24" aria-hidden>
      <path
        fill="none"
        stroke="currentColor"
        strokeWidth="2"
        strokeLinecap="round"
        strokeLinejoin="round"
        d="M1 3h15v13H1zM16 8h4l3 3v5h-7V8zM5.5 21a2.5 2.5 0 1 0 0-5 2.5 2.5 0 0 0 0 5zm13 0a2.5 2.5 0 1 0 0-5 2.5 2.5 0 0 0 0 5z"
      />
    </svg>
  )
}

function IconBell() {
  return (
    <svg className={styles.glyph} viewBox="0 0 24 24" aria-hidden>
      <path
        fill="none"
        stroke="currentColor"
        strokeWidth="2"
        strokeLinecap="round"
        strokeLinejoin="round"
        d="M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9M13.73 21a2 2 0 0 1-3.46 0"
      />
    </svg>
  )
}

function IconChartSearch() {
  return (
    <svg className={styles.headerGlyph} viewBox="0 0 24 24" aria-hidden>
      <path
        fill="none"
        stroke="currentColor"
        strokeWidth="2"
        strokeLinecap="round"
        d="M3 3v18h18M7 12l3-3 4 4 5-6M19 19l-2-2"
      />
    </svg>
  )
}

function IconInfo() {
  return (
    <svg className={styles.infoGlyph} viewBox="0 0 24 24" aria-hidden>
      <circle cx="12" cy="12" r="10" fill="none" stroke="currentColor" strokeWidth="2" />
      <path fill="currentColor" d="M12 16v-5h-1v5h1zm-1-6.5h2v-2h-2v2z" />
    </svg>
  )
}

const DRIVER_ORDER: DriverKey[] = [
  'inventory_policy_signals',
  'maintenance_demand_signals',
  'supplier_delay_signals',
  'reactive_site_order_signals',
]

const DRIVER_META: Record<
  DriverKey,
  { label: string; color: string; Icon: () => ReactElement }
> = {
  inventory_policy_signals: {
    label: 'Inventory Policy Risk',
    color: '#7c3aed',
    Icon: IconClipboard,
  },
  maintenance_demand_signals: {
    label: 'Maintenance Demand',
    color: '#ea580c',
    Icon: IconWrench,
  },
  supplier_delay_signals: {
    label: 'Supplier Delay',
    color: '#2563eb',
    Icon: IconTruck,
  },
  reactive_site_order_signals: {
    label: 'Late Site Order',
    color: '#dc2626',
    Icon: IconBell,
  },
}

/** Integer percentages that sum to 100 when total > 0 (largest remainder). */
function sharePercents(counts: number[]): number[] {
  const total = counts.reduce((a, b) => a + b, 0)
  if (total === 0) return counts.map(() => 0)
  const exact = counts.map((c) => (100 * c) / total)
  const floors = exact.map((x) => Math.floor(x))
  const diff = 100 - floors.reduce((a, b) => a + b, 0)
  const order = exact
    .map((x, i) => ({ i, rem: x - Math.floor(x) }))
    .sort((a, b) => b.rem - a.rem)
  const result = [...floors]
  for (let k = 0; k < diff; k++) {
    result[order[k].i]++
  }
  return result
}

function summaryToRows(summary: RootCauseSummaryRow): DriverRow[] {
  const keys = DRIVER_ORDER
  const counts = keys.map((k) => summary[k])
  const pcts = sharePercents(counts)
  const rows = keys.map((key, i) => ({
    key,
    label: DRIVER_META[key].label,
    color: DRIVER_META[key].color,
    count: counts[i],
    pct: pcts[i],
  }))
  return rows.sort((a, b) => b.pct - a.pct || b.count - a.count)
}

const AXIS_TICKS = [0, 10, 20, 30, 40, 50, 60, 70, 80, 90, 100] as const

export default function RootCauseSummaryChart() {
  const [summary, setSummary] = useState<RootCauseSummaryRow | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    let cancelled = false
    async function load() {
      setLoading(true)
      setError(null)
      try {
        const data = await fetchRootCauseSummary()
        if (cancelled) return
        setSummary(data)
      } catch (e) {
        if (!cancelled) {
          setError(e instanceof Error ? e.message : 'Failed to load root cause summary')
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

  const rows = useMemo(() => (summary ? summaryToRows(summary) : []), [summary])

  if (loading) {
    return (
      <article className={styles.card} aria-busy="true">
        <p className={styles.message}>Loading…</p>
      </article>
    )
  }

  if (error) {
    return (
      <article className={styles.card}>
        <p className={styles.messageError}>Error: {error}</p>
      </article>
    )
  }

  if (!summary) {
    return (
      <article className={styles.card}>
        <p className={styles.message}>No data</p>
      </article>
    )
  }

  return (
    <article className={styles.card} aria-labelledby="root-cause-summary-heading">
      <header className={styles.header}>
        <div className={styles.headerMain}>
          <span className={styles.headerIconBadge}>
            <IconChartSearch />
          </span>
          <div className={styles.headerText}>
            <h2 id="root-cause-summary-heading" className={styles.title}>
              Root Cause Summary
            </h2>
            <p className={styles.subtitle}>Breakdown of readiness risk drivers.</p>
          </div>
        </div>
        <button
          type="button"
          className={styles.infoBtn}
          title="Each percentage is that driver’s share of total risk signals in the current dataset."
          aria-label="About root cause percentages"
        >
          <IconInfo />
        </button>
      </header>

      <div className={styles.chartBody}>
        <div className={styles.axisRow}>
          {AXIS_TICKS.map((t) => (
            <span key={t} className={styles.axisTick}>
              {t}%
            </span>
          ))}
        </div>

        <ul className={styles.rows}>
          {rows.map((row) => {
            const { Icon } = DRIVER_META[row.key]
            return (
              <li key={row.key} className={styles.row}>
                <span
                  className={styles.iconBadge}
                  style={{ backgroundColor: row.color }}
                  aria-hidden
                >
                  <Icon />
                </span>
                <span className={styles.label}>{row.label}</span>
                <div className={styles.track}>
                  <div className={styles.grid} aria-hidden />
                  <div
                    className={styles.fill}
                    style={{
                      width: `${row.pct}%`,
                      backgroundColor: row.color,
                    }}
                  />
                </div>
                <span className={styles.pct}>{row.pct}%</span>
              </li>
            )
          })}
        </ul>
      </div>
    </article>
  )
}
