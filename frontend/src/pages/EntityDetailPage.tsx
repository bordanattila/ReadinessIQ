import { useEffect, useMemo, useState } from 'react'
import { useParams } from 'react-router-dom'
import {
  fetchPartSummary,
  fetchSiteSummary,
  fetchSupplierSummary,
} from '../api'
import {
  buildPartDetailView,
  buildSiteDetailView,
  buildSupplierDetailView,
} from '../components/detailSummaryViewModel'
import DetailedView from '../components/detailedView'
import type { Top5CardIcon } from '../components/top5ColumnTypes'

export type EntityDetailCategory = 'sites' | 'parts' | 'suppliers'

type DetailConfig = {
  icon: Top5CardIcon
  listHref: string
  listLabel: string
  paramKey: 'siteId' | 'partId' | 'supplierId'
  load: (id: string) => Promise<unknown>
  build: (data: never) => {
    title: string
    subtitle: string
    entityId: string
    sections: ReturnType<typeof buildSiteDetailView>['sections']
  }
}

const DETAIL_PAGES: Record<EntityDetailCategory, DetailConfig> = {
  sites: {
    icon: 'location',
    listHref: '/sites',
    listLabel: '← Sites list',
    paramKey: 'siteId',
    load: (id) => fetchSiteSummary(id),
    build: (data) => buildSiteDetailView(data as Parameters<typeof buildSiteDetailView>[0]),
  },
  parts: {
    icon: 'gear',
    listHref: '/parts',
    listLabel: '← Parts list',
    paramKey: 'partId',
    load: (id) => fetchPartSummary(id),
    build: (data) => buildPartDetailView(data as Parameters<typeof buildPartDetailView>[0]),
  },
  suppliers: {
    icon: 'building',
    listHref: '/suppliers',
    listLabel: '← Suppliers list',
    paramKey: 'supplierId',
    load: (id) => fetchSupplierSummary(id),
    build: (data) =>
      buildSupplierDetailView(data as Parameters<typeof buildSupplierDetailView>[0]),
  },
}

export default function EntityDetailPage({ category }: { category: EntityDetailCategory }) {
  const params = useParams()
  const cfg = DETAIL_PAGES[category]
  const entityId = params[cfg.paramKey] ?? ''

  const hasEntityId = entityId.length > 0
  const fetchKey = `${category}:${entityId}`
  const [loaded, setLoaded] = useState<{ key: string; data: unknown } | null>(null)
  const [loading, setLoading] = useState(false)
  const [fetchError, setFetchError] = useState<string | null>(null)

  useEffect(() => {
    if (!hasEntityId) return

    const page = DETAIL_PAGES[category]
    let cancelled = false

    async function run() {
      setLoading(true)
      setFetchError(null)
      try {
        const data = await page.load(entityId)
        if (!cancelled) setLoaded({ key: fetchKey, data })
      } catch (e) {
        if (!cancelled) {
          setFetchError(e instanceof Error ? e.message : 'Failed to load summary')
          setLoaded(null)
        }
      } finally {
        if (!cancelled) setLoading(false)
      }
    }

    void run()
    return () => {
      cancelled = true
    }
  }, [category, entityId, fetchKey, hasEntityId])

  const error = hasEntityId ? fetchError : 'Missing entity id'
  const hasCurrentData = loaded?.key === fetchKey
  const isLoading = hasEntityId && (loading || (!hasCurrentData && !fetchError))

  const view = useMemo(() => {
    if (!hasCurrentData || !loaded) return null
    return DETAIL_PAGES[category].build(loaded.data as never)
  }, [hasCurrentData, loaded, category])

  return (
    <DetailedView
      icon={cfg.icon}
      title={view?.title ?? (isLoading ? 'Loading…' : entityId)}
      subtitle={view?.subtitle}
      entityId={view?.entityId ?? entityId}
      backHref={cfg.listHref}
      backLabel={cfg.listLabel}
      sections={view?.sections ?? []}
      loading={isLoading}
      error={error}
    />
  )
}
