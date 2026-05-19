import type { PartReadinessRow, SiteRiskRow, SupplierPerformanceRow } from '../api'
import type { Top5Column } from './top5ColumnTypes'

/** Columns shown on the dashboard Top 5 cards */
export const SITE_COLUMNS_TOP5: Top5Column[] = [
  { key: 'site_name', header: 'Site', kind: 'link', idKey: 'site_id', path: '/sites' },
  { key: 'site_region', header: 'Region', kind: 'text' },
  { key: 'mission_priority', header: 'Mission Priority', kind: 'missionPriority' },
  {
    key: 'readiness_risk_score',
    header: 'Risk Score',
    kind: 'badge',
    headerAlign: 'right',
  },
]

export const PART_COLUMNS_TOP5: Top5Column[] = [
  { key: 'part_id', header: 'NSN / Part ID', kind: 'link', idKey: 'part_id', path: '/parts' },
  { key: 'part_name', header: 'Part Name', kind: 'text' },
  { key: 'criticality', header: 'Criticality', kind: 'criticality' },
  {
    key: 'readiness_risk_score',
    header: 'Risk Score',
    kind: 'badge',
    headerAlign: 'right',
  },
]

export const SUPPLIER_COLUMNS_TOP5: Top5Column[] = [
  {
    key: 'supplier_name',
    header: 'Supplier',
    kind: 'link',
    idKey: 'supplier_id',
    path: '/suppliers',
  },
  { key: 'on_time_display', header: 'On-Time Rate', kind: 'text' },
  { key: 'delayed_shipments', header: 'Delayed Shipments', kind: 'text' },
  {
    key: 'performance_risk_score',
    header: 'Risk Score',
    kind: 'badge',
    headerAlign: 'right',
  },
]

/** Full site ranking table (all API fields). */
export const SITE_COLUMNS_FULL: Top5Column[] = [
  { key: 'site_id', header: 'Site ID', kind: 'text' },
  { key: 'site_name', header: 'Site', kind: 'link', idKey: 'site_id', path: '/sites' },
  { key: 'site_region', header: 'Region', kind: 'text' },
  { key: 'site_type', header: 'Type', kind: 'text' },
  { key: 'mission_priority', header: 'Mission Priority', kind: 'missionPriority' },
  { key: 'stockout_count', header: 'Stockouts', kind: 'text', headerAlign: 'right' },
  { key: 'below_reorder_count', header: 'Below reorder', kind: 'text', headerAlign: 'right' },
  { key: 'delayed_shipments', header: 'Delayed shipments', kind: 'text', headerAlign: 'right' },
  {
    key: 'open_maintenance_events',
    header: 'Open maintenance',
    kind: 'text',
    headerAlign: 'right',
  },
  { key: 'avg_backlog_days', header: 'Avg backlog (days)', kind: 'text', headerAlign: 'right' },
  {
    key: 'readiness_risk_score',
    header: 'Risk score',
    kind: 'badge',
    headerAlign: 'right',
  },
]

export const PART_COLUMNS_FULL: Top5Column[] = [
  { key: 'part_id', header: 'NSN / Part ID', kind: 'link', idKey: 'part_id', path: '/parts' },
  { key: 'part_name', header: 'Part name', kind: 'text' },
  { key: 'part_family', header: 'Family', kind: 'text' },
  { key: 'criticality', header: 'Criticality', kind: 'criticality' },
  { key: 'sites_impacted', header: 'Sites impacted', kind: 'text', headerAlign: 'right' },
  { key: 'stockout_count', header: 'Stockouts', kind: 'text', headerAlign: 'right' },
  { key: 'below_reorder_count', header: 'Below reorder', kind: 'text', headerAlign: 'right' },
  {
    key: 'total_quantity_available',
    header: 'Qty available',
    kind: 'text',
    headerAlign: 'right',
  },
  {
    key: 'open_maintenance_events',
    header: 'Open maintenance',
    kind: 'text',
    headerAlign: 'right',
  },
  {
    key: 'readiness_risk_score',
    header: 'Risk score',
    kind: 'badge',
    headerAlign: 'right',
  },
]

export const SUPPLIER_COLUMNS_FULL: Top5Column[] = [
  { key: 'supplier_id', header: 'Supplier ID', kind: 'text' },
  {
    key: 'supplier_name',
    header: 'Supplier',
    kind: 'link',
    idKey: 'supplier_id',
    path: '/suppliers',
  },
  { key: 'total_orders', header: 'Total orders', kind: 'text', headerAlign: 'right' },
  { key: 'open_orders', header: 'Open orders', kind: 'text', headerAlign: 'right' },
  { key: 'total_shipments', header: 'Shipments', kind: 'text', headerAlign: 'right' },
  { key: 'delayed_shipments', header: 'Delayed', kind: 'text', headerAlign: 'right' },
  {
    key: 'average_delay_days',
    header: 'Avg delay (days)',
    kind: 'text',
    headerAlign: 'right',
  },
  { key: 'on_time_display', header: 'On-time rate', kind: 'text', headerAlign: 'right' },
  { key: 'sites_supported', header: 'Sites', kind: 'text', headerAlign: 'right' },
  { key: 'parts_supported', header: 'Parts', kind: 'text', headerAlign: 'right' },
  {
    key: 'average_days_non_mission_capable',
    header: 'Avg NMCS days',
    kind: 'text',
    headerAlign: 'right',
  },
  {
    key: 'performance_risk_score',
    header: 'Risk score',
    kind: 'badge',
    headerAlign: 'right',
  },
  { key: 'risk_drivers_display', header: 'Risk drivers', kind: 'text' },
]

export function siteRowToRecord(s: SiteRiskRow): Record<string, unknown> {
  return {
    site_id: s.site_id,
    site_name: s.site_name,
    site_region: s.site_region,
    site_type: s.site_type,
    mission_priority: s.mission_priority,
    stockout_count: s.stockout_count,
    below_reorder_count: s.below_reorder_count,
    delayed_shipments: s.delayed_shipments,
    open_maintenance_events: s.open_maintenance_events,
    avg_backlog_days: Number.isFinite(s.avg_backlog_days) ? s.avg_backlog_days.toFixed(1) : '0.0',
    readiness_risk_score: s.readiness_risk_score,
  }
}

export function partRowToRecord(p: PartReadinessRow): Record<string, unknown> {
  return {
    part_id: p.part_id,
    part_name: p.part_name,
    part_family: p.part_family,
    criticality: p.criticality,
    sites_impacted: p.sites_impacted,
    stockout_count: p.stockout_count,
    below_reorder_count: p.below_reorder_count,
    total_quantity_available: p.total_quantity_available,
    open_maintenance_events: p.open_maintenance_events,
    readiness_risk_score: p.readiness_risk_score,
  }
}

export function supplierRowToRecord(s: SupplierPerformanceRow): Record<string, unknown> {
  return {
    supplier_id: s.supplier_id,
    supplier_name: s.supplier_name,
    total_orders: s.total_orders,
    open_orders: s.open_orders,
    total_shipments: s.total_shipments,
    delayed_shipments: s.delayed_shipments,
    average_delay_days: Number.isFinite(s.average_delay_days) ? s.average_delay_days.toFixed(1) : '0.0',
    on_time_display: `${(s.on_time_delivery_rate * 100).toFixed(1)}%`,
    sites_supported: s.sites_supported,
    parts_supported: s.parts_supported,
    average_days_non_mission_capable: Number.isFinite(s.average_days_non_mission_capable)
      ? s.average_days_non_mission_capable.toFixed(1)
      : '0.0',
    performance_risk_score: s.performance_risk_score,
    risk_drivers_display: s.risk_drivers?.length ? s.risk_drivers.join(', ') : '—',
  }
}

export function topSitesFromApi(rows: SiteRiskRow[]): Record<string, unknown>[] {
  return rows.slice(0, 5).map((s) => ({
    site_id: s.site_id,
    site_name: s.site_name,
    site_region: s.site_region,
    mission_priority: s.mission_priority,
    readiness_risk_score: s.readiness_risk_score,
  }))
}

export function topPartsFromApi(rows: PartReadinessRow[]): Record<string, unknown>[] {
  return rows.slice(0, 5).map((p) => ({
    part_id: p.part_id,
    part_name: p.part_name,
    criticality: p.criticality,
    readiness_risk_score: p.readiness_risk_score,
  }))
}

export function topSuppliersFromApi(rows: SupplierPerformanceRow[]): Record<string, unknown>[] {
  return rows.slice(0, 5).map((s) => ({
    supplier_id: s.supplier_id,
    supplier_name: s.supplier_name,
    on_time_display: `${(s.on_time_delivery_rate * 100).toFixed(1)}%`,
    delayed_shipments: s.delayed_shipments,
    performance_risk_score: s.performance_risk_score,
  }))
}
