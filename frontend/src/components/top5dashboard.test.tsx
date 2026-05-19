import { render, screen, waitFor } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import type { PartReadinessRow, SiteRiskRow, SupplierPerformanceRow } from '../api'
import Top5Dashboard from './top5dashboard'

vi.mock('../api', () => ({
  fetchSitesRiskRanking: vi.fn(),
  fetchPartsReadinessImpact: vi.fn(),
  fetchSuppliersPerformance: vi.fn(),
}))

import {
  fetchPartsReadinessImpact,
  fetchSitesRiskRanking,
  fetchSuppliersPerformance,
} from '../api'

function makeSite(over: Partial<SiteRiskRow> = {}): SiteRiskRow {
  return {
    site_id: 's0',
    site_name: 'Base',
    site_region: 'US',
    site_type: 'depot',
    mission_priority: 3,
    stockout_count: 0,
    below_reorder_count: 0,
    delayed_shipments: 0,
    open_maintenance_events: 0,
    avg_backlog_days: 0,
    readiness_risk_score: 50,
    ...over,
  }
}

function makePart(over: Partial<PartReadinessRow> = {}): PartReadinessRow {
  return {
    part_id: 'p0',
    part_name: 'Part',
    part_family: 'fam',
    criticality: 'Medium',
    sites_impacted: 1,
    stockout_count: 0,
    below_reorder_count: 0,
    total_quantity_available: 5,
    open_maintenance_events: 0,
    readiness_risk_score: 40,
    ...over,
  }
}

function makeSupplier(over: Partial<SupplierPerformanceRow> = {}): SupplierPerformanceRow {
  return {
    supplier_id: 'v0',
    supplier_name: 'Vendor',
    total_orders: 1,
    open_orders: 0,
    total_shipments: 1,
    delayed_shipments: 0,
    average_delay_days: 0,
    on_time_delivery_rate: 0.9,
    sites_supported: 1,
    parts_supported: 1,
    average_days_non_mission_capable: 0,
    performance_risk_score: 30,
    risk_drivers: [],
    ...over,
  }
}

describe('Top5Dashboard', () => {
  beforeEach(() => {
    vi.mocked(fetchSitesRiskRanking).mockResolvedValue(
      Array.from({ length: 6 }, (_, i) =>
        makeSite({
          site_id: `s${i}`,
          site_name: `Site ${i}`,
          readiness_risk_score: 90 - i,
        }),
      ),
    )
    vi.mocked(fetchPartsReadinessImpact).mockResolvedValue(
      Array.from({ length: 6 }, (_, i) =>
        makePart({
          part_id: `p${i}`,
          part_name: `Part ${i}`,
          readiness_risk_score: 88 - i,
        }),
      ),
    )
    vi.mocked(fetchSuppliersPerformance).mockResolvedValue(
      Array.from({ length: 6 }, (_, i) =>
        makeSupplier({
          supplier_id: `v${i}`,
          supplier_name: `Supplier ${i}`,
          on_time_delivery_rate: 0.95 - i * 0.01,
          delayed_shipments: i,
          performance_risk_score: 86 - i,
        }),
      ),
    )
  })

  it('loads rankings and shows top site, part, and supplier names', async () => {
    render(
      <MemoryRouter>
        <Top5Dashboard />
      </MemoryRouter>,
    )
    expect(screen.getAllByText('Loading…').length).toBe(3)

    await waitFor(() => {
      expect(screen.getByText('Site 0')).toBeInTheDocument()
    })
    expect(screen.getByText('Part 0')).toBeInTheDocument()
    expect(screen.getByText('Supplier 0')).toBeInTheDocument()
    expect(screen.queryByText('Loading…')).not.toBeInTheDocument()
  })

  it('surfaces the same error on all cards when requests fail', async () => {
    vi.mocked(fetchSitesRiskRanking).mockRejectedValue(new Error('service unavailable'))
    vi.mocked(fetchPartsReadinessImpact).mockRejectedValue(new Error('service unavailable'))
    vi.mocked(fetchSuppliersPerformance).mockRejectedValue(new Error('service unavailable'))

    render(
      <MemoryRouter>
        <Top5Dashboard />
      </MemoryRouter>,
    )

    await waitFor(() => {
      expect(screen.getAllByText('service unavailable')).toHaveLength(3)
    })
  })
})
