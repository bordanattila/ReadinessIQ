import { describe, expect, it } from 'vitest'
import type { PartSummary, SiteSummary, SupplierSummary } from '../api'
import {
  buildPartDetailView,
  buildSiteDetailView,
  buildSupplierDetailView,
} from './detailSummaryViewModel'

const siteSummary: SiteSummary = {
  site: {
    site_id: 'SITE-A',
    site_name: 'Alpha Depot',
    site_region: 'North',
    site_type: 'Depot',
    mission_priority: 5,
  },
  inventory: {
    stockout_count: 2,
    below_reorder_count: 3,
    below_safety_stock_count: 1,
  },
  shipments: {
    total_shipments: 10,
    delayed_shipments: 4,
    delayed_shipment_rate: 0.4,
    average_delay_days: 2.5,
  },
  maintenance: {
    open_maintenance_events: 2,
    average_backlog_days: 15,
    total_days_non_mission_capable: 30,
  },
  inventory_positions: [
    {
      inventory_id: 1,
      part_id: 'PART-A001',
      part_name: 'Alpha Bolt',
      part_family: 'Hardware',
      criticality: 'High',
      quantity_on_hand: 5,
      quantity_allocated: 2,
      quantity_available: 3,
      reorder_point: 10,
      safety_stock: 8,
      stockout_flag: false,
      below_reorder_point: true,
      below_safety_stock: true,
      days_of_supply: 4.2,
      snapshot_date: '2026-01-15',
    },
  ],
}

const partSummary: PartSummary = {
  part: {
    part_id: 'PART-A001',
    part_name: 'Alpha Bolt',
    part_family: 'Hardware',
    criticality: 'High',
  },
  supplier: {
    supplier_id: 'ACME',
    supplier_name: 'Acme Corp',
  },
  inventory: {
    stockout_count: 1,
    below_reorder_count: 2,
    below_safety_stock_count: 0,
  },
  shipments: {
    total_shipments: 6,
    delayed_shipments: 3,
    delayed_shipment_rate: 0.5,
    average_delay_days: 3,
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
}

const supplierSummary: SupplierSummary = {
  supplier: {
    supplier_id: 'ACME',
    supplier_name: 'Acme Corp',
  },
  orders: {
    total_orders: 12,
    open_orders: 3,
  },
  shipments: {
    total_shipments: 20,
    delayed_shipments: 5,
    delayed_shipment_rate: 0.25,
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
}

describe('buildSiteDetailView', () => {
  it('maps site metadata and metric sections', () => {
    const view = buildSiteDetailView(siteSummary)

    expect(view.title).toBe('Alpha Depot')
    expect(view.subtitle).toBe('Depot · North')
    expect(view.entityId).toBe('SITE-A')
    expect(view.sections.map((s) => s.title)).toEqual([
      'Inventory',
      'Shipments',
      'Maintenance',
      'Inventory positions',
    ])
  })

  it('formats inventory position booleans and numbers for display', () => {
    const table = buildSiteDetailView(siteSummary).sections.find(
      (s) => s.kind === 'table' && s.title === 'Inventory positions',
    )
    expect(table?.kind).toBe('table')
    if (table?.kind !== 'table') return

    expect(table.rows[0]).toMatchObject({
      part_id: 'PART-A001',
      days_of_supply: '4.2',
      stockout_flag: 'No',
      below_reorder_point: 'Yes',
      below_safety_stock: 'Yes',
    })
  })
})

describe('buildPartDetailView', () => {
  it('maps part metadata and impacted sites table', () => {
    const view = buildPartDetailView(partSummary)

    expect(view.title).toBe('Alpha Bolt')
    expect(view.subtitle).toBe('Hardware · High')
    expect(view.entityId).toBe('PART-A001')

    const supplier = view.sections.find((s) => s.title === 'Supplier')
    expect(supplier?.kind).toBe('metrics')
    if (supplier?.kind === 'metrics') {
      expect(supplier.metrics).toEqual([
        { label: 'Supplier ID', value: 'ACME' },
        { label: 'Supplier name', value: 'Acme Corp' },
      ])
    }

    const sites = view.sections.find((s) => s.title === 'Sites impacted')
    expect(sites?.kind).toBe('table')
    if (sites?.kind === 'table') {
      expect(sites.rows).toHaveLength(1)
      expect(sites.rows[0].site_name).toBe('Alpha Depot')
    }
  })

  it('shows placeholder supplier metrics when supplier is null', () => {
    const view = buildPartDetailView({ ...partSummary, supplier: null })
    const supplier = view.sections.find((s) => s.title === 'Supplier')
    expect(supplier?.kind).toBe('metrics')
    if (supplier?.kind === 'metrics') {
      expect(supplier.metrics).toEqual([{ label: 'Primary supplier', value: '—' }])
    }
  })
})

describe('buildSupplierDetailView', () => {
  it('maps supplier metadata and related tables', () => {
    const view = buildSupplierDetailView(supplierSummary)

    expect(view.title).toBe('Acme Corp')
    expect(view.subtitle).toBe('Supplier performance summary')
    expect(view.entityId).toBe('ACME')
    expect(view.sections.map((s) => s.title)).toEqual([
      'Orders',
      'Shipments',
      'Parts supplied',
      'Sites supported',
    ])

    const parts = view.sections.find((s) => s.title === 'Parts supplied')
    expect(parts?.kind).toBe('table')
    if (parts?.kind === 'table') {
      expect(parts.rows[0].part_id).toBe('PART-A001')
    }
  })
})
