import type { ReactElement } from 'react'
import { cleanup, render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter } from 'react-router-dom'
import { afterEach, describe, expect, it } from 'vitest'
import DetailedView from './detailedView'

function mount(ui: ReactElement) {
  return render(<MemoryRouter>{ui}</MemoryRouter>)
}

afterEach(() => {
  cleanup()
})

describe('DetailedView', () => {
  it('renders header, metrics, and table sections', () => {
    mount(
      <DetailedView
        icon="location"
        title="Alpha Depot"
        subtitle="Depot · North"
        entityId="SITE-A"
        backHref="/sites"
        sections={[
          {
            kind: 'metrics',
            title: 'Inventory',
            metrics: [
              { label: 'Stockouts', value: '5' },
              { label: 'Positions', value: '8' },
            ],
          },
          {
            kind: 'table',
            title: 'Sites impacted',
            columns: [
              { key: 'site_name', header: 'Site', kind: 'text' },
            ],
            rows: [{ site_name: 'Alpha Depot' }],
          },
        ]}
      />,
    )

    expect(screen.getByRole('heading', { name: 'Alpha Depot' })).toBeInTheDocument()
    expect(screen.getByText('Depot · North')).toBeInTheDocument()
    expect(screen.getByText('SITE-A')).toBeInTheDocument()
    expect(screen.getByRole('link', { name: /Back to list/i })).toHaveAttribute('href', '/sites')
    expect(screen.getByRole('heading', { name: 'Inventory' })).toBeInTheDocument()
    expect(screen.getByText('5')).toBeInTheDocument()
    expect(screen.getByRole('columnheader', { name: 'Site' })).toBeInTheDocument()
    expect(screen.getByRole('cell', { name: 'Alpha Depot' })).toBeInTheDocument()
    expect(screen.getByLabelText('Search Sites impacted')).toBeInTheDocument()
  })

  it('filters table rows via search', async () => {
    const user = userEvent.setup()
    mount(
      <DetailedView
        icon="gear"
        title="Part detail"
        backHref="/parts"
        sections={[
          {
            kind: 'table',
            title: 'Sites impacted',
            columns: [
              { key: 'site_name', header: 'Site', kind: 'text' },
              { key: 'site_region', header: 'Region', kind: 'text' },
            ],
            rows: [
              { site_name: 'Alpha Depot', site_region: 'North' },
              { site_name: 'Bravo Hub', site_region: 'South' },
            ],
          },
        ]}
      />,
    )

    expect(screen.getByText('2 of 2 rows')).toBeInTheDocument()

    await user.type(screen.getByLabelText('Search Sites impacted'), 'bravo')
    expect(screen.queryByRole('cell', { name: 'Alpha Depot' })).not.toBeInTheDocument()
    expect(screen.getByRole('cell', { name: 'Bravo Hub' })).toBeInTheDocument()
    expect(screen.getByText('1 of 2 rows')).toBeInTheDocument()

    await user.click(screen.getByRole('button', { name: 'Clear search' }))
    expect(screen.getByRole('cell', { name: 'Alpha Depot' })).toBeInTheDocument()
    expect(screen.getByRole('cell', { name: 'Bravo Hub' })).toBeInTheDocument()
  })

  it('shows empty message when search matches no rows', async () => {
    const user = userEvent.setup()
    mount(
      <DetailedView
        icon="gear"
        title="Part detail"
        backHref="/parts"
        sections={[
          {
            kind: 'table',
            title: 'Sites impacted',
            columns: [{ key: 'site_name', header: 'Site', kind: 'text' }],
            rows: [{ site_name: 'Alpha Depot' }],
          },
        ]}
      />,
    )

    await user.type(screen.getByLabelText('Search Sites impacted'), 'zzz')
    expect(screen.getByText('No rows match your search.')).toBeInTheDocument()
    expect(screen.queryByRole('cell', { name: 'Alpha Depot' })).not.toBeInTheDocument()
  })

  it('shows loading and error states', () => {
    const { rerender } = mount(
      <DetailedView
        icon="gear"
        title="Loading"
        backHref="/parts"
        sections={[]}
        loading
      />,
    )
    expect(screen.getByText('Loading…')).toBeInTheDocument()

    rerender(
      <MemoryRouter>
        <DetailedView
          icon="gear"
          title="Failed"
          backHref="/parts"
          sections={[]}
          error="Part not found"
        />
      </MemoryRouter>,
    )
    expect(screen.getByRole('alert')).toHaveTextContent('Part not found')
  })
})
