import type { ReactElement } from 'react'
import { render, screen } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { describe, expect, it } from 'vitest'
import Top5Card, { type Top5Column } from './top5card'

function mount(ui: ReactElement) {
  return render(<MemoryRouter>{ui}</MemoryRouter>)
}

const textCols: Top5Column[] = [
  { key: 'name', header: 'Name', kind: 'text' },
  { key: 'score', header: 'Score', kind: 'badge', headerAlign: 'right' },
]

describe('Top5Card', () => {
  it('shows loading state', () => {
    mount(<Top5Card title="Test" icon="gear" columns={textCols} rows={[]} loading />)
    expect(screen.getByText('Loading…')).toBeInTheDocument()
  })

  it('shows error message', () => {
    mount(
      <Top5Card
        title="Test"
        icon="gear"
        columns={textCols}
        rows={[]}
        loading={false}
        error="Network failed"
      />,
    )
    expect(screen.getByText('Network failed')).toBeInTheDocument()
  })

  it('shows empty state when not loading', () => {
    mount(<Top5Card title="Test" icon="location" columns={textCols} rows={[]} loading={false} />)
    expect(screen.getByText('No data')).toBeInTheDocument()
  })

  it('renders rows, badge values, and view-all link', () => {
    mount(
      <Top5Card
        title="Sites"
        icon="location"
        columns={textCols}
        rows={[{ name: 'Alpha', score: 82 }]}
        viewAllHref="/sites"
        footer="Footer note"
        loading={false}
      />,
    )
    expect(screen.getByRole('heading', { name: 'Sites' })).toBeInTheDocument()
    expect(screen.getByRole('link', { name: 'View all' })).toHaveAttribute('href', '/sites')
    expect(screen.getByText('Alpha')).toBeInTheDocument()
    expect(screen.getByText('82.0')).toBeInTheDocument()
    expect(screen.getByText('Footer note')).toBeInTheDocument()
  })

  it('renders link cells with encoded ids', () => {
    const cols: Top5Column[] = [
      { key: 'label', header: 'Label', kind: 'link', idKey: 'id', path: '/sites' },
    ]
    mount(<Top5Card title="Links" icon="building" columns={cols} rows={[{ id: 'a/b', label: 'Edge' }]} />)
    const link = screen.getByRole('link', { name: 'Edge' })
    expect(link).toHaveAttribute('href', '/sites/a%2Fb')
  })

  it('renders criticality with text', () => {
    const cols: Top5Column[] = [{ key: 'crit', header: 'Crit', kind: 'criticality' }]
    mount(<Top5Card title="Parts" icon="gear" columns={cols} rows={[{ crit: 'Mission critical' }]} />)
    expect(screen.getByText('Mission critical')).toBeInTheDocument()
  })

  it('renders mission priority label', () => {
    const cols: Top5Column[] = [{ key: 'mp', header: 'MP', kind: 'missionPriority' }]
    mount(<Top5Card title="Sites" icon="location" columns={cols} rows={[{ mp: 5 }]} />)
    expect(screen.getByText('High')).toBeInTheDocument()
  })
})
