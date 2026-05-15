import { useEffect, useState } from 'react'
import {
  fetchPartsReadinessImpact,
  fetchSitesRiskRanking,
  fetchSuppliersPerformance,
  type PartReadinessRow,
  type SiteRiskRow,
  type SupplierPerformanceRow,
} from '../api'
import Top5Card, { type Top5Column } from './top5card'
import styles from './top5dashboard.module.css'

const SITE_COLUMNS: Top5Column[] = [
  { key: 'site_name', header: 'Site', kind: 'link', idKey: 'site_id', path: '/sites' },
  { key: 'site_region', header: 'Region', kind: 'text' },
  { key: 'mission_priority', header: 'Mission Priority', kind: 'missionPriority' },
  {
    key: 'readiness_risk_score',
    header: 'Risk Score',
    kind: 'badge',
    headerAlign: 'right',
  },
]

const PART_COLUMNS: Top5Column[] = [
  { key: 'part_id', header: 'NSN / Part ID', kind: 'link', idKey: 'part_id', path: '/parts' },
  { key: 'part_name', header: 'Part Name', kind: 'text' },
  { key: 'criticality', header: 'Criticality', kind: 'criticality' },
  {
    key: 'readiness_risk_score',
    header: 'Risk Score',
    kind: 'badge',
    headerAlign: 'right',
  },
]

const SUPPLIER_COLUMNS: Top5Column[] = [
  {
    key: 'supplier_name',
    header: 'Supplier',
    kind: 'link',
    idKey: 'supplier_id',
    path: '/suppliers',
  },
  { key: 'on_time_display', header: 'On-Time Rate', kind: 'text' },
  { key: 'delayed_shipments', header: 'Delayed Shipments', kind: 'text' },
  {
    key: 'performance_risk_score',
    header: 'Risk Score',
    kind: 'badge',
    headerAlign: 'right',
  },
]

function topSites(rows: SiteRiskRow[]): Record<string, unknown>[] {
  return rows.slice(0, 5).map((s) => ({
    site_id: s.site_id,
    site_name: s.site_name,
    site_region: s.site_region,
    mission_priority: s.mission_priority,
    readiness_risk_score: s.readiness_risk_score,
  }))
}

function topParts(rows: PartReadinessRow[]): Record<string, unknown>[] {
  return rows.slice(0, 5).map((p) => ({
    part_id: p.part_id,
    part_name: p.part_name,
    criticality: p.criticality,
    readiness_risk_score: p.readiness_risk_score,
  }))
}

function topSuppliers(rows: SupplierPerformanceRow[]): Record<string, unknown>[] {
  return rows.slice(0, 5).map((s) => ({
    supplier_id: s.supplier_id,
    supplier_name: s.supplier_name,
    on_time_display: `${(s.on_time_delivery_rate * 100).toFixed(1)}%`,
    delayed_shipments: s.delayed_shipments,
    performance_risk_score: s.performance_risk_score,
  }))
}

export default function Top5Dashboard() {
  const [sites, setSites] = useState<Record<string, unknown>[]>([])
  const [parts, setParts] = useState<Record<string, unknown>[]>([])
  const [suppliers, setSuppliers] = useState<Record<string, unknown>[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    let cancelled = false

    async function load() {
      setLoading(true)
      setError(null)
      try {
        const [siteRows, partRows, supplierRows] = await Promise.all([
          fetchSitesRiskRanking(),
          fetchPartsReadinessImpact(),
          fetchSuppliersPerformance(),
        ])
        if (cancelled) return
        setSites(topSites(siteRows))
        setParts(topParts(partRows))
        setSuppliers(topSuppliers(supplierRows))
      } catch (e) {
        if (!cancelled) {
          setError(e instanceof Error ? e.message : 'Failed to load rankings')
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

  const cardError = loading ? null : error

  return (
    <section className={styles.section} aria-label="Top risk rankings">
      <div className={styles.top5cards}>
        <Top5Card
          title="Top 5 Risky Sites"
          icon="location"
          columns={SITE_COLUMNS}
          rows={sites}
          footer="Scores reflect current week risk (0–100). Higher is greater risk."
          viewAllHref="/sites"
          loading={loading}
          error={cardError}
        />
        <Top5Card
          title="Top 5 Readiness-Impact Parts"
          icon="gear"
          columns={PART_COLUMNS}
          rows={parts}
          footer="Criticality based on mission impact and demand."
          viewAllHref="/parts"
          loading={loading}
          error={cardError}
        />
        <Top5Card
          title="Top 5 Supplier Risk"
          icon="building"
          columns={SUPPLIER_COLUMNS}
          rows={suppliers}
          footer="On-time rate and delayed shipments over selected date range."
          viewAllHref="/suppliers"
          loading={loading}
          error={cardError}
        />
      </div>
    </section>
  )
}
