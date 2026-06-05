import { describe, expect, it } from 'vitest'
import {
  filterDetailTableRows,
  getDetailCellText,
  hasActiveDetailTableSearch,
} from './detailTableFilter'
import type { Top5Column } from './top5ColumnTypes'

const columns: Top5Column[] = [
  { key: 'part_id', header: 'Part ID', kind: 'link', idKey: 'part_id', path: '/parts' },
  { key: 'part_name', header: 'Part name', kind: 'text' },
  { key: 'stockout_flag', header: 'Stockout', kind: 'text' },
]

const rows = [
  { part_id: 'PART-A001', part_name: 'Alpha Bolt', stockout_flag: 'Yes' },
  { part_id: 'PART-B002', part_name: 'Bravo Seal', stockout_flag: 'No' },
]

describe('getDetailCellText', () => {
  it('includes link label and id', () => {
    expect(getDetailCellText(columns[0], rows[0])).toBe('PART-A001 PART-A001')
  })
})

describe('filterDetailTableRows', () => {
  it('returns all rows when search is empty', () => {
    expect(filterDetailTableRows(columns, rows, '')).toHaveLength(2)
  })

  it('filters by global search across columns', () => {
    const result = filterDetailTableRows(columns, rows, 'bravo')
    expect(result).toHaveLength(1)
    expect(result[0].part_id).toBe('PART-B002')
  })

  it('matches values in any column', () => {
    const result = filterDetailTableRows(columns, rows, 'yes')
    expect(result).toHaveLength(1)
    expect(result[0].part_id).toBe('PART-A001')
  })
})

describe('hasActiveDetailTableSearch', () => {
  it('is false for blank search', () => {
    expect(hasActiveDetailTableSearch('')).toBe(false)
    expect(hasActiveDetailTableSearch('   ')).toBe(false)
  })

  it('is true when search has content', () => {
    expect(hasActiveDetailTableSearch('bolt')).toBe(true)
  })
})

describe('getDetailCellText special column kinds', () => {
  it('formats badge scores', () => {
    const col = { key: 'score', header: 'Score', kind: 'badge' as const }
    expect(getDetailCellText(col, { score: 82.4 })).toBe('82.4')
  })

  it('includes mission priority label', () => {
    const col = { key: 'mission_priority', header: 'MP', kind: 'missionPriority' as const }
    expect(getDetailCellText(col, { mission_priority: 5 })).toBe('5 High')
  })
})
