import { render, screen, waitFor } from '@testing-library/react'
import { describe, expect, it, vi } from 'vitest'
import RootCauseSummaryChart from './rootCauseSummaryChart'

vi.mock('../api', () => ({
  fetchRootCauseSummary: vi.fn(() =>
    Promise.resolve({
      total_risk_signals: 100,
      supplier_delay_signals: 21,
      reactive_site_order_signals: 14,
      inventory_policy_signals: 37,
      maintenance_demand_signals: 28,
    }),
  ),
}))

describe('RootCauseSummaryChart', () => {
  it('renders summary title and percentage shares (largest-first)', async () => {
    render(<RootCauseSummaryChart />)

    await waitFor(() => {
      expect(screen.getByRole('heading', { name: /Root Cause Summary/i })).toBeInTheDocument()
    })
    expect(screen.getByText(/Breakdown of readiness risk drivers/i)).toBeInTheDocument()
    expect(screen.getByText('Inventory Policy Risk')).toBeInTheDocument()
    expect(screen.getByText('37%')).toBeInTheDocument()
    expect(screen.getByText('Maintenance Demand')).toBeInTheDocument()
    expect(screen.getByText('28%')).toBeInTheDocument()
  })
})
