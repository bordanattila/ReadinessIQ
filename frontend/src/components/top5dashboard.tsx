import { useEffect, useState } from 'react'
import {
  fetchPartsReadinessImpact,
  fetchSitesRiskRanking,
  fetchSuppliersPerformance,
} from '../api'
import Top5Card from './top5card'
import {
  PART_COLUMNS_TOP5,
  SITE_COLUMNS_TOP5,
  SUPPLIER_COLUMNS_TOP5,
  topPartsFromApi,
  topSitesFromApi,
  topSuppliersFromApi,
} from './riskRankingViewModel'
import styles from './top5dashboard.module.css'

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
        setSites(topSitesFromApi(siteRows))
        setParts(topPartsFromApi(partRows))
        setSuppliers(topSuppliersFromApi(supplierRows))
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
          columns={SITE_COLUMNS_TOP5}
          rows={sites}
          footer="Scores reflect current week risk (0–100). Higher is greater risk."
          viewAllHref="/sites"
          loading={loading}
          error={cardError}
        />
        <Top5Card
          title="Top 5 Readiness Impact Parts"
          icon="gear"
          columns={PART_COLUMNS_TOP5}
          rows={parts}
          footer="Criticality based on mission impact and demand."
          viewAllHref="/parts"
          loading={loading}
          error={cardError}
        />
        <Top5Card
          title="Top 5 Supplier Risk"
          icon="building"
          columns={SUPPLIER_COLUMNS_TOP5}
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
