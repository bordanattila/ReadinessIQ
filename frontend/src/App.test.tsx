import { cleanup, render, screen, waitFor } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { afterEach, describe, expect, it, vi } from 'vitest'

vi.mock('./api', () => ({
  fetchSitesRiskRanking: vi.fn(() => Promise.resolve([])),
  fetchPartsReadinessImpact: vi.fn(() => Promise.resolve([])),
  fetchSuppliersPerformance: vi.fn(() => Promise.resolve([])),
  fetchMetrics: vi.fn(() =>
    Promise.resolve([
      { metric: 'Fill rate', value: 0.92 },
      { metric: 'On-time delivery', value: 0.88 },
      { metric: 'Overall risk score', value: 0.75 },
    ]),
  ),
  fetchRootCauseSummary: vi.fn(() =>
    Promise.resolve({
      total_risk_signals: 10,
      supplier_delay_signals: 2,
      reactive_site_order_signals: 3,
      inventory_policy_signals: 4,
      maintenance_demand_signals: 1,
    }),
  ),
  fetchCurrentUser: vi.fn(() =>
    Promise.resolve({
      id: 1,
      name: 'Jane',
      email: 'jane@example.com',
      mfa_verified: true,
      mfa_enabled: false,
    }),
  ),
}))

import App from './App'
import { AuthProvider } from './auth/AuthContext'
import { fetchCurrentUser, fetchSitesRiskRanking } from './api'

const minimalSite = {
  site_id: 's1',
  site_name: 'Route Test Site',
  site_region: 'US',
  site_type: 'depot',
  mission_priority: 3,
  stockout_count: 0,
  below_reorder_count: 0,
  delayed_shipments: 0,
  open_maintenance_events: 0,
  avg_backlog_days: 0,
  readiness_risk_score: 50,
}

function renderApp(initialEntries: string[] = ['/']) {
  return render(
    <MemoryRouter initialEntries={initialEntries}>
      <AuthProvider>
        <App />
      </AuthProvider>
    </MemoryRouter>,
  )
}

describe('App', () => {
  afterEach(() => {
    cleanup()
    vi.mocked(fetchCurrentUser).mockImplementation(() =>
      Promise.resolve({
        id: 1,
        name: 'Jane',
        email: 'jane@example.com',
        mfa_verified: true,
        mfa_enabled: false,
      }),
    )
  })

  it('renders product title and dashboard section when authenticated', async () => {
    renderApp()
    expect(
      screen.getByRole('heading', { level: 1, name: /ReadinessIQ/i }),
    ).toBeInTheDocument()
    expect(
      screen.getByText(/Defense Logistics Readiness and Supply Visibility Platform/i),
    ).toBeInTheDocument()
    await waitFor(() => {
      expect(screen.getByRole('region', { name: /Top risk rankings/i })).toBeInTheDocument()
    })
  })

  it('renders the sites view-all route with the ViewAll template', async () => {
    vi.mocked(fetchSitesRiskRanking).mockResolvedValueOnce([minimalSite])
    renderApp(['/sites'])
    await waitFor(() => {
      expect(screen.getByRole('heading', { name: /Sites — risk ranking/i })).toBeInTheDocument()
    })
    await waitFor(() => {
      expect(screen.getByText('Route Test Site')).toBeInTheDocument()
    })
    expect(screen.getByRole('link', { name: '← Overview' })).toHaveAttribute('href', '/')
  })

  it('shows the sign-in gate when unauthenticated', async () => {
    vi.mocked(fetchCurrentUser).mockRejectedValueOnce(new Error('Not authenticated'))
    renderApp()

    expect(
      await screen.findByRole('heading', { name: /Sign in required/i }),
    ).toBeInTheDocument()
    expect(screen.queryByRole('region', { name: /Top risk rankings/i })).not.toBeInTheDocument()
  })

  it('renders the login route outside the dashboard shell', () => {
    renderApp(['/login'])
    expect(screen.getByText(/Sign in to your account/i)).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /Sign in/i })).toBeInTheDocument()
    expect(
      screen.queryByText(/Defense Logistics Readiness and Supply Visibility Platform/i),
    ).not.toBeInTheDocument()
  })
})
