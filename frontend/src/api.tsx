const BASE_URL = import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000'

function assertOk(body: { status?: string; message?: string }) {
  if (body.status === 'error') {
    throw new Error(typeof body.message === 'string' ? body.message : 'API error')
  }
}

export interface SiteRiskRow {
  site_id: string
  site_name: string
  site_region: string
  site_type: string
  mission_priority: number
  stockout_count: number
  below_reorder_count: number
  delayed_shipments: number
  open_maintenance_events: number
  avg_backlog_days: number
  readiness_risk_score: number
}

export async function fetchSitesRiskRanking(): Promise<SiteRiskRow[]> {
  const response = await fetch(`${BASE_URL}/api/sites/risk-ranking`)
  if (!response.ok) {
    throw new Error(`Sites risk ranking failed: ${response.status}`)
  }
  const body = (await response.json()) as { status?: string; message?: string; sites: SiteRiskRow[] }
  assertOk(body)
  return body.sites ?? []
}

export interface PartReadinessRow {
  part_id: string
  part_name: string
  part_family: string
  criticality: string
  sites_impacted: number
  stockout_count: number
  below_reorder_count: number
  total_quantity_available: number
  open_maintenance_events: number
  readiness_risk_score: number
}

export async function fetchPartsReadinessImpact(): Promise<PartReadinessRow[]> {
  const response = await fetch(`${BASE_URL}/api/parts/readiness-impact`)
  if (!response.ok) {
    throw new Error(`Parts readiness failed: ${response.status}`)
  }
  const body = (await response.json()) as { status?: string; message?: string; parts: PartReadinessRow[] }
  assertOk(body)
  return body.parts ?? []
}

export interface SupplierPerformanceRow {
  supplier_id: string
  supplier_name: string
  total_orders: number
  open_orders: number
  total_shipments: number
  delayed_shipments: number
  average_delay_days: number
  on_time_delivery_rate: number
  sites_supported: number
  parts_supported: number
  average_days_non_mission_capable: number
  performance_risk_score: number
  risk_drivers: string[]
}

export async function fetchSuppliersPerformance(): Promise<SupplierPerformanceRow[]> {
  const response = await fetch(`${BASE_URL}/api/suppliers/performance`)
  if (!response.ok) {
    throw new Error(`Suppliers performance failed: ${response.status}`)
  }
  const body = (await response.json()) as {
    status?: string
    message?: string
    suppliers: SupplierPerformanceRow[]
  }
  assertOk(body)
  return body.suppliers ?? []
}
