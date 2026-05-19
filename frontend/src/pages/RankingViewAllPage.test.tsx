import { render, screen, waitFor } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { describe, expect, it, vi } from 'vitest'
import type { SiteRiskRow } from '../api'
import RankingViewAllPage from './RankingViewAllPage'

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

const site: SiteRiskRow = {
  site_id: 's1',
  site_name: 'Alpha Base',
  site_region: 'US-East',
  site_type: 'depot',
  mission_priority: 4,
  stockout_count: 1,
  below_reorder_count: 2,
  delayed_shipments: 0,
  open_maintenance_events: 0,
  avg_backlog_days: 3.5,
  readiness_risk_score: 72,
}

describe('RankingViewAllPage', () => {
  it('loads sites and shows full-table title and mapped row', async () => {
    vi.mocked(fetchSitesRiskRanking).mockResolvedValue([site])
    vi.mocked(fetchPartsReadinessImpact).mockResolvedValue([])
    vi.mocked(fetchSuppliersPerformance).mockResolvedValue([])

    render(
      <MemoryRouter>
        <RankingViewAllPage category="sites" />
      </MemoryRouter>,
    )

    await waitFor(() => {
      expect(screen.getByRole('heading', { name: /Sites — risk ranking/i })).toBeInTheDocument()
    })
    expect(screen.getByText('Alpha Base')).toBeInTheDocument()
    expect(screen.getByText('1 sites')).toBeInTheDocument()
    expect(screen.getByRole('columnheader', { name: /Site ID/i })).toBeInTheDocument()
  })
})
