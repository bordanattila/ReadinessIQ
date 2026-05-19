import { useEffect, useMemo, useState } from 'react'
import {
  fetchPartsReadinessImpact,
  fetchSitesRiskRanking,
  fetchSuppliersPerformance,
} from '../api'
import type { Top5CardIcon, Top5Column } from '../components/top5ColumnTypes'
import ViewAll from '../components/viewAll'
import {
  PART_COLUMNS_FULL,
  SITE_COLUMNS_FULL,
  SUPPLIER_COLUMNS_FULL,
  partRowToRecord,
  siteRowToRecord,
  supplierRowToRecord,
} from '../components/riskRankingViewModel'

export type RankingViewCategory = 'sites' | 'parts' | 'suppliers'

type PageConfig = {
  title: string
  subtitle: string
  icon: Top5CardIcon
  columns: Top5Column[]
  footer: string
  load: () => Promise<unknown[]>
  mapRow: (row: never) => Record<string, unknown>
}

const PAGES: Record<RankingViewCategory, PageConfig> = {
  sites: {
    title: 'Sites — risk ranking',
    subtitle: 'Every site in the ranking with the same fields used for the dashboard Top 5, plus operational signals.',
    icon: 'location',
    columns: SITE_COLUMNS_FULL,
    footer: 'Scores reflect current week risk (0–100). Higher is greater risk.',
    load: () => fetchSitesRiskRanking() as Promise<unknown[]>,
    mapRow: (row) => siteRowToRecord(row as Parameters<typeof siteRowToRecord>[0]),
  },
  parts: {
    title: 'Parts — readiness impact',
    subtitle: 'Full parts list with criticality, demand, inventory, and maintenance context.',
    icon: 'gear',
    columns: PART_COLUMNS_FULL,
    footer: 'Criticality based on mission impact and demand.',
    load: () => fetchPartsReadinessImpact() as Promise<unknown[]>,
    mapRow: (row) => partRowToRecord(row as Parameters<typeof partRowToRecord>[0]),
  },
  suppliers: {
    title: 'Suppliers — performance & risk',
    subtitle: 'All suppliers with order, shipment, delay, and coverage metrics.',
    icon: 'building',
    columns: SUPPLIER_COLUMNS_FULL,
    footer: 'On-time rate and delayed shipments over the selected operational window.',
    load: () => fetchSuppliersPerformance() as Promise<unknown[]>,
    mapRow: (row) => supplierRowToRecord(row as Parameters<typeof supplierRowToRecord>[0]),
  },
}

export default function RankingViewAllPage({ category }: { category: RankingViewCategory }) {
  const [raw, setRaw] = useState<unknown[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    const page = PAGES[category]
    let cancelled = false
    async function run() {
      setLoading(true)
      setError(null)
      try {
        const data = await page.load()
        if (!cancelled) setRaw(data)
      } catch (e) {
        if (!cancelled) {
          setError(e instanceof Error ? e.message : 'Failed to load data')
        }
      } finally {
        if (!cancelled) setLoading(false)
      }
    }
    void run()
    return () => {
      cancelled = true
    }
  }, [category])

  const rows = useMemo(() => {
    const page = PAGES[category]
    return raw.map((r) => page.mapRow(r as never))
  }, [raw, category])

  const cfg = PAGES[category]
  const meta =
    !loading && !error
      ? `${rows.length} ${category === 'sites' ? 'sites' : category === 'parts' ? 'parts' : 'suppliers'}`
      : undefined

  return (
    <ViewAll
      title={cfg.title}
      subtitle={cfg.subtitle}
      icon={cfg.icon}
      columns={cfg.columns}
      rows={rows}
      footer={cfg.footer}
      loading={loading}
      error={error}
      meta={meta}
    />
  )
}
