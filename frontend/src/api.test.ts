import { afterEach, describe, expect, it, vi } from 'vitest'
import {
  fetchPartsReadinessImpact,
  fetchSitesRiskRanking,
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
