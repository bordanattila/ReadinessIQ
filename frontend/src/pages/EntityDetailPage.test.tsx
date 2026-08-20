import { cleanup, render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { createMemoryRouter, RouterProvider } from 'react-router-dom'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import { afterEach, describe, expect, it, vi } from 'vitest'

vi.mock('../api', () => ({
  fetchSiteSummary: vi.fn(),
  fetchPartSummary: vi.fn(),
  fetchSupplierSummary: vi.fn(),
}))

import { fetchPartSummary, fetchSiteSummary, fetchSupplierSummary } from '../api'
import EntityDetailPage from './EntityDetailPage'

afterEach(() => {
  cleanup()
  vi.clearAllMocks()
})

describe('EntityDetailPage', () => {
  it('loads site summary and renders detail sections', async () => {
    vi.mocked(fetchSiteSummary).mockResolvedValueOnce({
      site: {
        site_id: 'SITE-A',
        site_name: 'Alpha Depot',
        site_region: 'North',
        site_type: 'Depot',
        mission_priority: 5,
      },
      inventory: {
        stockout_count: 5,
        below_reorder_count: 8,
        below_safety_stock_count: 5,
      },
      shipments: {
        total_shipments: 6,
        delayed_shipments: 6,
        delayed_shipment_rate: 1,
        average_delay_days: 3,
      },
      maintenance: {
        open_maintenance_events: 3,
        average_backlog_days: 30,
        total_days_non_mission_capable: 60,
      },
      inventory_positions: [
        {
          inventory_id: 1,
          part_id: 'PART-A001',
          part_name: 'Alpha Bolt',
          part_family: 'Hardware',
          criticality: 'High',
          quantity_on_hand: 2,
          quantity_allocated: 2,
          quantity_available: 0,
          reorder_point: 10,
          safety_stock: 8,
          stockout_flag: true,
          below_reorder_point: true,
          below_safety_stock: true,
          days_of_supply: 1.5,
          snapshot_date: '2026-01-15',
        },
        {
          inventory_id: 2,
          part_id: 'PART-B002',
          part_name: 'Bravo Seal',
          part_family: 'Seals',
          criticality: 'Medium',
          quantity_on_hand: 20,
          quantity_allocated: 5,
          quantity_available: 15,
          reorder_point: 10,
          safety_stock: 8,
          stockout_flag: false,
          below_reorder_point: false,
          below_safety_stock: false,
          days_of_supply: 12,
          snapshot_date: '2026-01-15',
        },
      ],
    })

    render(
      <MemoryRouter initialEntries={['/sites/SITE-A']}>
        <Routes>
          <Route path="/sites/:siteId" element={<EntityDetailPage category="sites" />} />
        </Routes>
      </MemoryRouter>,
    )

    await waitFor(() => {
      expect(screen.getByRole('heading', { name: 'Alpha Depot' })).toBeInTheDocument()
    })
    expect(screen.getByText('SITE-A')).toBeInTheDocument()
    expect(screen.getByRole('heading', { name: 'Inventory positions' })).toBeInTheDocument()
    expect(fetchSiteSummary).toHaveBeenCalledWith('SITE-A')
  })

  it('loads part summary and renders sites impacted table', async () => {
    vi.mocked(fetchPartSummary).mockResolvedValueOnce({
      part: {
        part_id: 'PART-A001',
        part_name: 'Alpha Bolt',
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
        total_shipments: 0,
        delayed_shipments: 0,
        delayed_shipment_rate: 0,
        average_delay_days: 0,
      },
      sites_impacted: [
        {
          site_id: 'SITE-A',
          site_name: 'Alpha Depot',
          site_region: 'North',
          site_type: 'Depot',
          mission_priority: 5,
        },
      ],
    })

    render(
      <MemoryRouter initialEntries={['/parts/PART-A001']}>
        <Routes>
          <Route path="/parts/:partId" element={<EntityDetailPage category="parts" />} />
        </Routes>
      </MemoryRouter>,
    )

    await waitFor(() => {
      expect(screen.getByRole('heading', { name: 'Alpha Bolt' })).toBeInTheDocument()
    })
    expect(screen.getByRole('heading', { name: 'Sites impacted' })).toBeInTheDocument()
    expect(fetchPartSummary).toHaveBeenCalledWith('PART-A001')
  })

  it('loads supplier summary and renders parts and sites tables', async () => {
    vi.mocked(fetchSupplierSummary).mockResolvedValueOnce({
      supplier: { supplier_id: 'ACME', supplier_name: 'Acme Corp' },
      orders: { total_orders: 5, open_orders: 1 },
      shipments: {
        total_shipments: 10,
        delayed_shipments: 2,
        delayed_shipment_rate: 0.2,
        average_delay_days: 4,
      },
      parts_supplied: [
        {
          part_id: 'PART-A001',
          part_name: 'Alpha Bolt',
          part_family: 'Hardware',
          criticality: 'High',
        },
      ],
      sites_supported: [
        {
          site_id: 'SITE-A',
          site_name: 'Alpha Depot',
          site_region: 'North',
          site_type: 'Depot',
          mission_priority: 5,
        },
      ],
    })

    render(
      <MemoryRouter initialEntries={['/suppliers/ACME']}>
        <Routes>
          <Route
            path="/suppliers/:supplierId"
            element={<EntityDetailPage category="suppliers" />}
          />
        </Routes>
      </MemoryRouter>,
    )

    await waitFor(() => {
      expect(screen.getByRole('heading', { name: 'Acme Corp' })).toBeInTheDocument()
    })
    expect(screen.getByRole('heading', { name: 'Parts supplied' })).toBeInTheDocument()
    expect(screen.getByRole('heading', { name: 'Sites supported' })).toBeInTheDocument()
    expect(fetchSupplierSummary).toHaveBeenCalledWith('ACME')
  })

  it('shows error when route param is missing', async () => {
    render(
      <MemoryRouter initialEntries={['/sites']}>
        <Routes>
          <Route path="/sites" element={<EntityDetailPage category="sites" />} />
        </Routes>
      </MemoryRouter>,
    )

    expect(screen.getByRole('alert')).toHaveTextContent('Missing entity id')
    expect(fetchSiteSummary).not.toHaveBeenCalled()
  })

  it('renders part detail after navigating from supplier detail via in-table link', async () => {
    const user = userEvent.setup()
    vi.mocked(fetchSupplierSummary).mockResolvedValueOnce({
      supplier: { supplier_id: 'LSEG', supplier_name: 'LSEG Corp' },
      orders: { total_orders: 5, open_orders: 1 },
      shipments: {
        total_shipments: 10,
        delayed_shipments: 2,
        delayed_shipment_rate: 0.2,
        average_delay_days: 4,
      },
      parts_supplied: [
        {
          part_id: 'PART-0117',
          part_name: 'Seal Kit 117',
          part_family: 'Seals',
          criticality: 'High',
        },
      ],
      sites_supported: [],
    })
    vi.mocked(fetchPartSummary).mockResolvedValueOnce({
      part: {
        part_id: 'PART-0117',
        part_name: 'Seal Kit 117',
        part_family: 'Seals',
        criticality: 'High',
      },
      supplier: { supplier_id: 'LSEG', supplier_name: 'LSEG Corp' },
      inventory: {
        stockout_count: 0,
        below_reorder_count: 1,
        below_safety_stock_count: 0,
      },
      shipments: {
        total_shipments: 4,
        delayed_shipments: 1,
        delayed_shipment_rate: 0.25,
        average_delay_days: 2,
      },
      sites_impacted: [],
    })

    const router = createMemoryRouter(
      [
        {
          path: '/suppliers/:supplierId',
          element: <EntityDetailPage category="suppliers" />,
        },
        {
          path: '/parts/:partId',
          element: <EntityDetailPage category="parts" />,
        },
      ],
      { initialEntries: ['/suppliers/LSEG'] },
    )

    render(<RouterProvider router={router} />)

    await waitFor(() => {
      expect(screen.getByRole('heading', { name: 'LSEG Corp' })).toBeInTheDocument()
    })

    await user.click(screen.getByRole('link', { name: 'PART-0117' }))

    await waitFor(() => {
      expect(screen.getByRole('heading', { name: 'Seal Kit 117' })).toBeInTheDocument()
    })
    expect(screen.getByText('PART-0117')).toBeInTheDocument()
    expect(screen.getByRole('heading', { name: 'Sites impacted' })).toBeInTheDocument()
    expect(fetchPartSummary).toHaveBeenCalledWith('PART-0117')
  })

  it('shows fetch error from the API layer', async () => {
    vi.mocked(fetchSiteSummary).mockRejectedValueOnce(new Error('Site summary failed: 404'))

    render(
      <MemoryRouter initialEntries={['/sites/MISSING']}>
        <Routes>
          <Route path="/sites/:siteId" element={<EntityDetailPage category="sites" />} />
        </Routes>
      </MemoryRouter>,
    )

    await waitFor(() => {
      expect(screen.getByRole('alert')).toHaveTextContent('Site summary failed: 404')
    })
  })

  it('filters inventory positions via table search', async () => {
    const user = userEvent.setup()
    vi.mocked(fetchSiteSummary).mockResolvedValueOnce({
      site: {
        site_id: 'SITE-A',
        site_name: 'Alpha Depot',
        site_region: 'North',
        site_type: 'Depot',
        mission_priority: 5,
      },
      inventory: {
        stockout_count: 1,
        below_reorder_count: 1,
        below_safety_stock_count: 1,
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
      inventory_positions: [
        {
          inventory_id: 1,
          part_id: 'PART-A001',
          part_name: 'Alpha Bolt',
          part_family: 'Hardware',
          criticality: 'High',
          quantity_on_hand: 2,
          quantity_allocated: 2,
          quantity_available: 0,
          reorder_point: 10,
          safety_stock: 8,
          stockout_flag: true,
          below_reorder_point: true,
          below_safety_stock: true,
          days_of_supply: 1.5,
          snapshot_date: '2026-01-15',
        },
        {
          inventory_id: 2,
          part_id: 'PART-B002',
          part_name: 'Bravo Seal',
          part_family: 'Seals',
          criticality: 'Medium',
          quantity_on_hand: 20,
          quantity_allocated: 5,
          quantity_available: 15,
          reorder_point: 10,
          safety_stock: 8,
          stockout_flag: false,
          below_reorder_point: false,
          below_safety_stock: false,
          days_of_supply: 12,
          snapshot_date: '2026-01-15',
        },
      ],
    })

    render(
      <MemoryRouter initialEntries={['/sites/SITE-A']}>
        <Routes>
          <Route path="/sites/:siteId" element={<EntityDetailPage category="sites" />} />
        </Routes>
      </MemoryRouter>,
    )

    await waitFor(() => {
      expect(screen.getByRole('cell', { name: 'Bravo Seal' })).toBeInTheDocument()
    })

    await user.type(screen.getByLabelText('Search Inventory positions'), 'bravo')
    expect(screen.queryByRole('cell', { name: 'Alpha Bolt' })).not.toBeInTheDocument()
    expect(screen.getByRole('cell', { name: 'Bravo Seal' })).toBeInTheDocument()
  })
})
