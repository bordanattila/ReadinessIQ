import type {
  PartSummary,
  SiteSummary,
  SupplierSummary,
} from '../api'
import type { Top5Column } from './top5ColumnTypes'
import type { DetailSection } from './detailedView'

const SITE_LINK_COLS: Top5Column[] = [
  { key: 'site_name', header: 'Site', kind: 'link', idKey: 'site_id', path: '/sites' },
  { key: 'site_region', header: 'Region', kind: 'text' },
  { key: 'site_type', header: 'Type', kind: 'text' },
  { key: 'mission_priority', header: 'Mission priority', kind: 'missionPriority' },
]

const PART_LINK_COLS: Top5Column[] = [
  { key: 'part_id', header: 'Part ID', kind: 'link', idKey: 'part_id', path: '/parts' },
  { key: 'part_name', header: 'Part name', kind: 'text' },
  { key: 'part_family', header: 'Family', kind: 'text' },
  { key: 'criticality', header: 'Criticality', kind: 'criticality' },
]

const SITE_INVENTORY_POSITION_COLS: Top5Column[] = [
  { key: 'part_id', header: 'Part ID', kind: 'link', idKey: 'part_id', path: '/parts' },
  { key: 'part_name', header: 'Part name', kind: 'text' },
  { key: 'quantity_on_hand', header: 'On hand', kind: 'text', headerAlign: 'left' },
  { key: 'quantity_allocated', header: 'Allocated', kind: 'text', headerAlign: 'left' },
  { key: 'quantity_available', header: 'Available', kind: 'text', headerAlign: 'left' },
  { key: 'reorder_point', header: 'Reorder point', kind: 'text', headerAlign: 'left' },
  { key: 'safety_stock', header: 'Safety stock', kind: 'text', headerAlign: 'left' },
  { key: 'days_of_supply', header: 'Days supply', kind: 'text', headerAlign: 'left' },
  { key: 'stockout_flag', header: 'Stockout', kind: 'text', headerAlign: 'left' },
  { key: 'below_reorder_point', header: 'Below reorder point', kind: 'text', headerAlign: 'left' },
  { key: 'below_safety_stock', header: 'Below safety stock', kind: 'text', headerAlign: 'left' },
]

function formatBoolFlag(value: boolean): string {
  return value ? 'Yes' : 'No'
}

function siteInventoryPositionRows(
  rows: SiteSummary['inventory_positions'],
): Record<string, unknown>[] {
  return rows.map((row) => ({
    ...row,
    days_of_supply: formatNum(row.days_of_supply, 1),
    stockout_flag: formatBoolFlag(row.stockout_flag),
    below_reorder_point: formatBoolFlag(row.below_reorder_point),
    below_safety_stock: formatBoolFlag(row.below_safety_stock),
  }))
}

function formatRate(rate: number): string {
  return `${(rate * 100).toFixed(1)}%`
}

function formatNum(n: number, digits = 0): string {
  return Number.isFinite(n) ? n.toFixed(digits) : '—'
}

export function buildSiteDetailView(data: SiteSummary): {
  title: string
  subtitle: string
  entityId: string
  sections: DetailSection[]
} {
  const { site, inventory, shipments, maintenance, inventory_positions } = data
  return {
    title: site.site_name,
    subtitle: `${site.site_type} · ${site.site_region}`,
    entityId: site.site_id,
    sections: [
      {
        kind: 'metrics',
        title: 'Inventory',
        metrics: [
          { label: 'Stockouts', value: String(inventory.stockout_count) },
          { label: 'Below reorder', value: String(inventory.below_reorder_count) },
          { label: 'Below safety stock', value: String(inventory.below_safety_stock_count) },
        ],
      },
      {
        kind: 'metrics',
        title: 'Shipments',
        metrics: [
          { label: 'Total shipments', value: String(shipments.total_shipments) },
          { label: 'Delayed', value: String(shipments.delayed_shipments) },
          { label: 'Delayed rate', value: formatRate(shipments.delayed_shipment_rate) },
          { label: 'Avg delay (days)', value: formatNum(shipments.average_delay_days, 1) },
        ],
      },
      {
        kind: 'metrics',
        title: 'Maintenance',
        metrics: [
          { label: 'Open events', value: String(maintenance.open_maintenance_events) },
          { label: 'Avg backlog (days)', value: formatNum(maintenance.average_backlog_days, 1) },
          {
            label: 'Total NMCS days',
            value: String(maintenance.total_days_non_mission_capable),
          },
        ],
      },
      {
        kind: 'table',
        title: 'Inventory positions',
        columns: SITE_INVENTORY_POSITION_COLS,
        rows: siteInventoryPositionRows(inventory_positions),
        emptyMessage: 'No inventory positions at this site.',
      },
    ],
  }
}

export function buildPartDetailView(data: PartSummary): {
  title: string
  subtitle: string
  entityId: string
  sections: DetailSection[]
} {
  const { part, supplier, inventory, shipments, sites_impacted } = data
  const supplierMetrics = supplier
    ? [
        { label: 'Supplier ID', value: supplier.supplier_id },
        { label: 'Supplier name', value: supplier.supplier_name },
      ]
    : [{ label: 'Primary supplier', value: '—' }]

  return {
    title: part.part_name,
    subtitle: `${part.part_family} · ${part.criticality}`,
    entityId: part.part_id,
    sections: [
      { kind: 'metrics', title: 'Supplier', metrics: supplierMetrics },
      {
        kind: 'metrics',
        title: 'Inventory',
        metrics: [
          { label: 'Stockouts', value: String(inventory.stockout_count) },
          { label: 'Below reorder', value: String(inventory.below_reorder_count) },
          { label: 'Below safety stock', value: String(inventory.below_safety_stock_count) },
        ],
      },
      {
        kind: 'metrics',
        title: 'Shipments',
        metrics: [
          { label: 'Total shipments', value: String(shipments.total_shipments) },
          { label: 'Delayed', value: String(shipments.delayed_shipments) },
          { label: 'Delayed rate', value: formatRate(shipments.delayed_shipment_rate) },
          { label: 'Avg delay (days)', value: formatNum(shipments.average_delay_days, 1) },
        ],
      },
      {
        kind: 'table',
        title: 'Sites impacted',
        columns: SITE_LINK_COLS,
        rows: sites_impacted.map((s) => ({ ...s })),
        emptyMessage: 'No sites showing inventory distress for this part.',
      },
    ],
  }
}

export function buildSupplierDetailView(data: SupplierSummary): {
  title: string
  subtitle: string
  entityId: string
  sections: DetailSection[]
} {
  const { supplier, orders, shipments, parts_supplied, sites_supported } = data
  return {
    title: supplier.supplier_name,
    subtitle: 'Supplier performance summary',
    entityId: supplier.supplier_id,
    sections: [
      {
        kind: 'metrics',
        title: 'Orders',
        metrics: [
          { label: 'Total orders', value: String(orders.total_orders) },
          { label: 'Open orders', value: String(orders.open_orders) },
        ],
      },
      {
        kind: 'metrics',
        title: 'Shipments',
        metrics: [
          { label: 'Total shipments', value: String(shipments.total_shipments) },
          { label: 'Delayed', value: String(shipments.delayed_shipments) },
          { label: 'Delayed rate', value: formatRate(shipments.delayed_shipment_rate) },
          { label: 'Avg delay (days)', value: formatNum(shipments.average_delay_days, 1) },
        ],
      },
      {
        kind: 'table',
        title: 'Parts supplied',
        columns: PART_LINK_COLS,
        rows: parts_supplied.map((p) => ({ ...p })),
        emptyMessage: 'No parts linked to this supplier.',
      },
      {
        kind: 'table',
        title: 'Sites supported',
        columns: SITE_LINK_COLS,
        rows: sites_supported.map((s) => ({ ...s })),
        emptyMessage: 'No sites linked to this supplier.',
      },
    ],
  }
}
