import { afterEach, describe, expect, it, vi } from 'vitest'
import {
  fetchMetrics,
  fetchPartSummary,
  fetchPartsReadinessImpact,
  fetchSiteSummary,
  fetchSitesRiskRanking,
  fetchSupplierSummary,
  fetchSuppliersPerformance,
} from './api'

function mockFetchJson(body: unknown, ok = true, status = ok ? 200 : 500) {
  return vi.fn().mockResolvedValue({
    ok,
    status,
    json: async () => body,
  })
}

describe('fetchSitesRiskRanking', () => {
  afterEach(() => {
    vi.unstubAllGlobals()
  })

  it('returns sites and calls the configured base URL', async () => {
    const sites = [
      {
        site_id: 's1',
        site_name: 'Alpha',
        site_region: 'US',
        site_type: 'depot',
        mission_priority: 4,
        stockout_count: 1,
        below_reorder_count: 0,
        delayed_shipments: 0,
        open_maintenance_events: 0,
        avg_backlog_days: 2,
        readiness_risk_score: 72,
      },
    ]
    vi.stubGlobal('fetch', mockFetchJson({ sites }))
    const result = await fetchSitesRiskRanking()
    expect(result).toEqual(sites)
    expect(fetch).toHaveBeenCalledWith('http://localhost:8000/api/sites/risk-ranking')
  })

  it('throws when response is not ok', async () => {
    vi.stubGlobal('fetch', mockFetchJson({}, false, 503))
    await expect(fetchSitesRiskRanking()).rejects.toThrow('Sites risk ranking failed: 503')
  })

  it('throws when API body reports error', async () => {
    vi.stubGlobal('fetch', mockFetchJson({ status: 'error', message: 'db down' }))
    await expect(fetchSitesRiskRanking()).rejects.toThrow('db down')
  })

  it('returns empty array when sites key is missing', async () => {
    vi.stubGlobal('fetch', mockFetchJson({}))
    const result = await fetchSitesRiskRanking()
    expect(result).toEqual([])
  })
})

describe('fetchPartsReadinessImpact', () => {
  afterEach(() => {
    vi.unstubAllGlobals()
  })

  it('returns parts on success', async () => {
    const parts = [
      {
        part_id: 'p1',
        part_name: 'Bolt',
        part_family: 'hardware',
        criticality: 'High',
        sites_impacted: 2,
        stockout_count: 0,
        below_reorder_count: 1,
        total_quantity_available: 10,
        open_maintenance_events: 0,
        readiness_risk_score: 65,
      },
    ]
    vi.stubGlobal('fetch', mockFetchJson({ parts }))
    await expect(fetchPartsReadinessImpact()).resolves.toEqual(parts)
  })
})

describe('fetchSuppliersPerformance', () => {
  afterEach(() => {
    vi.unstubAllGlobals()
  })

  it('returns suppliers on success', async () => {
    const suppliers = [
      {
        supplier_id: 'v1',
        supplier_name: 'Vendor',
        total_orders: 10,
        open_orders: 1,
        total_shipments: 8,
        delayed_shipments: 2,
        average_delay_days: 3,
        on_time_delivery_rate: 0.875,
        sites_supported: 4,
        parts_supported: 20,
        average_days_non_mission_capable: 1,
        performance_risk_score: 55,
        risk_drivers: ['delays'],
      },
    ]
    vi.stubGlobal('fetch', mockFetchJson({ suppliers }))
    await expect(fetchSuppliersPerformance()).resolves.toEqual(suppliers)
  })
})

describe('fetchMetrics', () => {
  afterEach(() => {
    vi.unstubAllGlobals()
  })

  it('maps KPI overview metrics object into dashboard rows', async () => {
    vi.stubGlobal(
      'fetch',
      mockFetchJson({
        status: 'ok',
        metrics: {
          fill_rate: 0.95,
          on_time_delivery_rate: 0.9,
          overall_risk_score: 0.72,
        },
        inventory: { stockout_rate: 0.03 },
      }),
    )
    await expect(fetchMetrics()).resolves.toEqual([
      { metric: 'Fill rate', value: 0.95 },
      { metric: 'On-time delivery', value: 0.9 },
      { metric: 'Overall risk score', value: 0.72 },
      { metric: 'Stockout rate', value: 0.03 },
    ])
    expect(fetch).toHaveBeenCalledWith('http://localhost:8000/api/kpis/overview')
  })

  it('returns only core metrics when inventory stockout is missing', async () => {
    vi.stubGlobal(
      'fetch',
      mockFetchJson({
        metrics: {
          fill_rate: 1,
          on_time_delivery_rate: 1,
          overall_risk_score: 0.5,
        },
      }),
    )
    await expect(fetchMetrics()).resolves.toEqual([
      { metric: 'Fill rate', value: 1 },
      { metric: 'On-time delivery', value: 1 },
      { metric: 'Overall risk score', value: 0.5 },
    ])
  })

  it('throws when response is not ok', async () => {
    vi.stubGlobal('fetch', mockFetchJson({}, false, 503))
    await expect(fetchMetrics()).rejects.toThrow('Metrics failed: 503')
  })

  it('throws when API body reports error', async () => {
    vi.stubGlobal('fetch', mockFetchJson({ status: 'error', message: 'db down' }))
    await expect(fetchMetrics()).rejects.toThrow('db down')
  })
})

describe('fetchSiteSummary', () => {
  afterEach(() => {
    vi.unstubAllGlobals()
  })

  it('returns site summary on success', async () => {
    vi.stubGlobal(
      'fetch',
      mockFetchJson({
        status: 'ok',
        site: {
          site_id: 'SITE-A',
          site_name: 'Alpha',
          site_region: 'North',
          site_type: 'Depot',
          mission_priority: 5,
        },
        inventory: {
          stockout_count: 0,
          below_reorder_count: 0,
          below_safety_stock_count: 0,
        },
        shipments: {
          total_shipments: 0,
          delayed_shipments: 0,
          delayed_shipment_rate: 0,
          average_delay_days: 0,
        },
        maintenance: {
          open_maintenance_events: 0,
          average_backlog_days: 0,
          total_days_non_mission_capable: 0,
        },
        inventory_positions: [],
      }),
    )
    const result = await fetchSiteSummary('SITE-A')
    expect(result.site.site_id).toBe('SITE-A')
    expect(result.inventory_positions).toEqual([])
    expect(fetch).toHaveBeenCalledWith('http://localhost:8000/api/sites/SITE-A/summary')
  })

  it('throws when response is not ok', async () => {
    vi.stubGlobal('fetch', mockFetchJson({}, false, 503))
    await expect(fetchSiteSummary('SITE-A')).rejects.toThrow('Site summary failed: 503')
  })

  it('throws when API body reports error', async () => {
    vi.stubGlobal('fetch', mockFetchJson({ status: 'error', message: 'Site not found' }))
    await expect(fetchSiteSummary('SITE-A')).rejects.toThrow('Site not found')
  })
})

describe('fetchPartSummary', () => {
  afterEach(() => {
    vi.unstubAllGlobals()
  })

  it('returns part summary with nullable supplier', async () => {
    vi.stubGlobal(
      'fetch',
      mockFetchJson({
        status: 'ok',
        part: {
          part_id: 'PART-1',
          part_name: 'Bolt',
          part_family: 'Hardware',
          criticality: 'High',
        },
        supplier: null,
        inventory: {
          stockout_count: 1,
          below_reorder_count: 1,
          below_safety_stock_count: 0,
        },
        shipments: {
          total_shipments: 3,
          delayed_shipments: 1,
          delayed_shipment_rate: 0.3333,
          average_delay_days: 2,
        },
        sites_impacted: [],
      }),
    )
    const result = await fetchPartSummary('PART-1')
    expect(result.supplier).toBeNull()
    expect(result.part.part_id).toBe('PART-1')
    expect(fetch).toHaveBeenCalledWith('http://localhost:8000/api/parts/PART-1/summary')
  })

  it('throws when response is not ok', async () => {
    vi.stubGlobal('fetch', mockFetchJson({}, false, 404))
    await expect(fetchPartSummary('PART-1')).rejects.toThrow('Part summary failed: 404')
  })

  it('throws when API body reports error', async () => {
    vi.stubGlobal('fetch', mockFetchJson({ status: 'error', message: 'Part not found' }))
    await expect(fetchPartSummary('PART-1')).rejects.toThrow('Part not found')
  })
})

describe('fetchSupplierSummary', () => {
  afterEach(() => {
    vi.unstubAllGlobals()
  })

  it('returns supplier summary on success', async () => {
    vi.stubGlobal(
      'fetch',
      mockFetchJson({
        status: 'ok',
        supplier: { supplier_id: 'ACME', supplier_name: 'Acme Corp' },
        parts_supplied: [],
        sites_supported: [],
        orders: { total_orders: 5, open_orders: 1 },
        shipments: {
          total_shipments: 10,
          delayed_shipments: 2,
          delayed_shipment_rate: 0.2,
          average_delay_days: 4,
        },
      }),
    )
    const result = await fetchSupplierSummary('ACME')
    expect(result.supplier.supplier_id).toBe('ACME')
    expect(fetch).toHaveBeenCalledWith('http://localhost:8000/api/suppliers/ACME/summary')
  })

  it('throws when response is not ok', async () => {
    vi.stubGlobal('fetch', mockFetchJson({}, false, 500))
    await expect(fetchSupplierSummary('ACME')).rejects.toThrow('Supplier summary failed: 500')
  })

  it('throws when API body reports error', async () => {
    vi.stubGlobal('fetch', mockFetchJson({ status: 'error', message: 'Supplier not found' }))
    await expect(fetchSupplierSummary('ACME')).rejects.toThrow('Supplier not found')
  })
})
