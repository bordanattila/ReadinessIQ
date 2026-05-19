import type { ReactElement } from 'react'
import { render, screen, within } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { describe, expect, it } from 'vitest'
import type { Top5Column } from './top5ColumnTypes'
import ViewAll from './viewAll'

const cols: Top5Column[] = [
  { key: 'a', header: 'Column A', kind: 'text' },
  { key: 'b', header: 'Column B', kind: 'text', headerAlign: 'right' },
]

function mount(ui: ReactElement) {
  return render(<MemoryRouter>{ui}</MemoryRouter>)
}

describe('ViewAll', () => {
  it('renders title, subtitle, meta, back link, and footer', () => {
    mount(
      <ViewAll
        title="Sites — full list"
        subtitle="All rows from the API."
        icon="location"
        columns={cols}
        rows={[{ a: 'x', b: 'y' }]}
        footer="Footer note"
        meta="3 sites"
      />,
    )
    expect(screen.getByRole('heading', { name: 'Sites — full list' })).toBeInTheDocument()
    expect(screen.getByText('All rows from the API.')).toBeInTheDocument()
    expect(screen.getByText('3 sites')).toBeInTheDocument()
    expect(screen.getByRole('link', { name: /Overview/i })).toHaveAttribute('href', '/')
    expect(screen.getByText('Footer note')).toBeInTheDocument()
  })

  it('renders table headers and cell values', () => {
    mount(
      <ViewAll title="Table test" icon="gear" columns={cols} rows={[{ a: 'Alpha', b: '99' }]} />,
    )
    const article = screen.getByRole('heading', { name: 'Table test' }).closest('article')!
    expect(within(article).getByRole('columnheader', { name: 'Column A' })).toBeInTheDocument()
    expect(within(article).getByRole('columnheader', { name: 'Column B' })).toBeInTheDocument()
    expect(within(article).getByText('Alpha')).toBeInTheDocument()
    expect(within(article).getByText('99')).toBeInTheDocument()
  })

  it('shows loading and error states', () => {
    const { rerender } = mount(
      <ViewAll title="L" icon="building" columns={cols} rows={[]} loading />,
    )
    expect(screen.getByText('Loading…')).toBeInTheDocument()

    rerender(
      <MemoryRouter>
        <ViewAll title="L" icon="building" columns={cols} rows={[]} loading={false} error="Boom" />
      </MemoryRouter>,
    )
    expect(screen.getByText(/Boom/)).toBeInTheDocument()
  })

  it('shows empty message when there are no rows', () => {
    mount(<ViewAll title="Empty" icon="location" columns={cols} rows={[]} loading={false} />)
    expect(screen.getByText('No data')).toBeInTheDocument()
  })
})
