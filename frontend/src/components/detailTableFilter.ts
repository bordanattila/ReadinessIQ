import type { Top5Column } from './top5ColumnTypes'

function missionPriorityLabel(n: number): string {
  if (n >= 5) return 'High'
  if (n >= 4) return 'Medium'
  if (n >= 3) return 'Medium'
  if (n >= 2) return 'Medium-Low'
  return 'Low'
}

/** Plain-text value used for global table search. */
export function getDetailCellText(col: Top5Column, row: Record<string, unknown>): string {
  switch (col.kind) {
    case 'text': {
      const v = row[col.key]
      return v != null ? String(v) : ''
    }
    case 'link': {
      const label = row[col.key] != null ? String(row[col.key]) : ''
      const id = row[col.idKey] != null ? String(row[col.idKey]) : ''
      return [label, id].filter(Boolean).join(' ')
    }
    case 'badge': {
      const raw = row[col.key]
      const score = typeof raw === 'number' ? raw : Number(raw)
      return Number.isFinite(score) ? score.toFixed(1) : ''
    }
    case 'criticality':
      return row[col.key] != null ? String(row[col.key]) : ''
    case 'missionPriority': {
      const raw = row[col.key]
      const n = typeof raw === 'number' ? raw : Number(raw)
      const safe = Number.isFinite(n) ? n : 0
      return `${safe} ${missionPriorityLabel(safe)}`
    }
    default:
      return ''
  }
}

function normalizeQuery(value: string): string {
  return value.trim().toLowerCase()
}

export function filterDetailTableRows(
  columns: Top5Column[],
  rows: Record<string, unknown>[],
  search: string,
): Record<string, unknown>[] {
  const query = normalizeQuery(search)
  if (!query) return rows

  return rows.filter((row) => {
    const haystack = columns
      .map((col) => getDetailCellText(col, row))
      .join(' ')
      .toLowerCase()
    return haystack.includes(query)
  })
}

export function hasActiveDetailTableSearch(search: string): boolean {
  return normalizeQuery(search).length > 0
}
