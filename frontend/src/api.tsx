const BASE_URL = import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000'

const AUTH_FETCH_INIT: RequestInit = { credentials: 'include' }

function assertOk(body: { status?: string; message?: string }) {
  if (body.status === 'error') {
    throw new Error(typeof body.message === 'string' ? body.message : 'API error')
  }
}

async function parseApiError(response: Response): Promise<string> {
  const body = (await response.json().catch(() => ({}))) as {
    detail?: string | Array<{ msg?: string }>
  }
  if (typeof body.detail === 'string') {
    return body.detail
  }
  if (Array.isArray(body.detail)) {
    const messages = body.detail
      .map((entry) => entry.msg)
      .filter((msg): msg is string => typeof msg === 'string')
    if (messages.length > 0) {
      return messages.join(', ')
    }
  }
  return `Request failed: ${response.status}`
}

export interface AuthMessageResponse {
  message: string
}

export interface RegisterUserPayload {
  name: string
  email: string
  password: string
}

export interface LoginUserPayload {
  email: string
  password: string
}

export interface CurrentUser {
  id: number
  name: string
  email: string
}

export async function registerUser(payload: RegisterUserPayload): Promise<AuthMessageResponse> {
  const response = await fetch(`${BASE_URL}/api/register_user/`, {
    ...AUTH_FETCH_INIT,
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  })
  if (!response.ok) {
    throw new Error(await parseApiError(response))
  }
  return (await response.json()) as AuthMessageResponse
}

export async function loginUser(payload: LoginUserPayload): Promise<AuthMessageResponse> {
  const response = await fetch(`${BASE_URL}/api/login/`, {
    ...AUTH_FETCH_INIT,
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  })
  if (!response.ok) {
    throw new Error(await parseApiError(response))
  }
  return (await response.json()) as AuthMessageResponse
}

export async function logoutUser(): Promise<AuthMessageResponse> {
  const response = await fetch(`${BASE_URL}/api/logout/`, {
    ...AUTH_FETCH_INIT,
    method: 'POST',
  })
  if (!response.ok) {
    throw new Error(await parseApiError(response))
  }
  return (await response.json()) as AuthMessageResponse
}

export async function fetchCurrentUser(): Promise<CurrentUser> {
  const response = await fetch(`${BASE_URL}/api/me/`, AUTH_FETCH_INIT)
  if (!response.ok) {
    throw new Error(await parseApiError(response))
  }
  return (await response.json()) as CurrentUser
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

export interface RootCauseSummaryRow {
  total_risk_signals: number
  supplier_delay_signals: number
  reactive_site_order_signals: number
  inventory_policy_signals: number
  maintenance_demand_signals: number
}

export async function fetchRootCauseSummary(): Promise<RootCauseSummaryRow> {
  const response = await fetch(`${BASE_URL}/api/root-cause/readiness-risk`)
  if (!response.ok) {
    throw new Error(`Root cause summary failed: ${response.status}`)
  }
  const body = (await response.json()) as { status?: string; message?: string; summary: RootCauseSummaryRow }
  assertOk(body)
  return body.summary
}

/** Normalized KPI row for dashboard cards (values are typically 0–1 rates from the API). */
export interface MetricsRow {
  metric: string
  value: number
}

/** Raw `/api/kpis/overview` payload shape returned by the backend. */
export interface KpiOverviewMetrics {
  fill_rate: number
  on_time_delivery_rate: number
  overall_risk_score: number
}

export async function fetchMetrics(): Promise<MetricsRow[]> {
  const response = await fetch(`${BASE_URL}/api/kpis/overview`)
  if (!response.ok) {
    throw new Error(`Metrics failed: ${response.status}`)
  }
  const body = (await response.json()) as {
    status?: string
    message?: string
    metrics?: KpiOverviewMetrics
    inventory?: { stockout_rate?: number }
  }
  assertOk(body)

  const rows: MetricsRow[] = []
  const m = body.metrics
  if (m) {
    rows.push({ metric: 'Fill rate', value: m.fill_rate })
    rows.push({ metric: 'On-time delivery', value: m.on_time_delivery_rate })
    rows.push({ metric: 'Overall risk score', value: m.overall_risk_score })
  }
  const stockout = body.inventory?.stockout_rate
  if (typeof stockout === 'number' && Number.isFinite(stockout)) {
    rows.push({ metric: 'Stockout rate', value: stockout })
  }
  return rows
}

export interface InventorySummaryBlock {
  stockout_count: number
  below_reorder_count: number
  below_safety_stock_count: number
}

export interface ShipmentSummaryBlock {
  total_shipments: number
  delayed_shipments: number
  delayed_shipment_rate: number
  average_delay_days: number
}

export interface MaintenanceSummaryBlock {
  open_maintenance_events: number
  average_backlog_days: number
  total_days_non_mission_capable: number
}

export interface SiteSummaryEntity {
  site_id: string
  site_name: string
  site_region: string
  site_type: string
  mission_priority: number
}

export interface SiteInventoryPositionRow {
  inventory_id: number
  part_id: string
  part_name: string
  part_family: string
  criticality: string
  quantity_on_hand: number
  quantity_allocated: number
  quantity_available: number
  reorder_point: number
  safety_stock: number
  stockout_flag: boolean
  below_reorder_point: boolean
  below_safety_stock: boolean
  days_of_supply: number
  snapshot_date: string
}

export interface SiteSummary {
  site: SiteSummaryEntity
  inventory: InventorySummaryBlock
  shipments: ShipmentSummaryBlock
  maintenance: MaintenanceSummaryBlock
  inventory_positions: SiteInventoryPositionRow[]
}

export async function fetchSiteSummary(siteId: string): Promise<SiteSummary> {
  const response = await fetch(
    `${BASE_URL}/api/sites/${encodeURIComponent(siteId)}/summary`,
  )
  if (!response.ok) {
    throw new Error(`Site summary failed: ${response.status}`)
  }
  const body = (await response.json()) as {
    status?: string
    message?: string
    site: SiteSummaryEntity
    inventory: InventorySummaryBlock
    shipments: ShipmentSummaryBlock
    maintenance: MaintenanceSummaryBlock
    inventory_positions: SiteInventoryPositionRow[]
  }
  assertOk(body)
  return {
    site: body.site,
    inventory: body.inventory,
    shipments: body.shipments,
    maintenance: body.maintenance,
    inventory_positions: body.inventory_positions ?? [],
  }
}

export interface PartSummaryEntity {
  part_id: string
  part_name: string
  part_family: string
  criticality: string
}

export interface PartSupplierRef {
  supplier_id: string
  supplier_name: string
}

export interface PartSummary {
  part: PartSummaryEntity
  supplier: PartSupplierRef | null
  inventory: InventorySummaryBlock
  shipments: ShipmentSummaryBlock
  sites_impacted: SiteSummaryEntity[]
}

export async function fetchPartSummary(partId: string): Promise<PartSummary> {
  const response = await fetch(
    `${BASE_URL}/api/parts/${encodeURIComponent(partId)}/summary`,
  )
  if (!response.ok) {
    throw new Error(`Part summary failed: ${response.status}`)
  }
  const body = (await response.json()) as {
    status?: string
    message?: string
    part: PartSummaryEntity
    supplier: PartSupplierRef | null
    inventory: InventorySummaryBlock
    shipments: ShipmentSummaryBlock
    sites_impacted: SiteSummaryEntity[]
  }
  assertOk(body)
  return {
    part: body.part,
    supplier: body.supplier ?? null,
    inventory: body.inventory,
    shipments: body.shipments,
    sites_impacted: body.sites_impacted ?? [],
  }
}

export interface SupplierSummaryEntity {
  supplier_id: string
  supplier_name: string
}

export interface OrdersSummaryBlock {
  total_orders: number
  open_orders: number
}

export interface SupplierSummary {
  supplier: SupplierSummaryEntity
  parts_supplied: PartSummaryEntity[]
  sites_supported: SiteSummaryEntity[]
  orders: OrdersSummaryBlock
  shipments: ShipmentSummaryBlock
}

export async function fetchSupplierSummary(supplierId: string): Promise<SupplierSummary> {
  const response = await fetch(
    `${BASE_URL}/api/suppliers/${encodeURIComponent(supplierId)}/summary`,
  )
  if (!response.ok) {
    throw new Error(`Supplier summary failed: ${response.status}`)
  }
  const body = (await response.json()) as {
    status?: string
    message?: string
    supplier: SupplierSummaryEntity
    parts_supplied: PartSummaryEntity[]
    sites_supported: SiteSummaryEntity[]
    orders: OrdersSummaryBlock
    shipments: ShipmentSummaryBlock
  }
  assertOk(body)
  return {
    supplier: body.supplier,
    parts_supplied: body.parts_supplied ?? [],
    sites_supported: body.sites_supported ?? [],
    orders: body.orders,
    shipments: body.shipments,
  }
}