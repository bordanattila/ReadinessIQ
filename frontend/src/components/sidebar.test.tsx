import { render, screen } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { describe, expect, it } from 'vitest'
import Sidebar from './sidebar'

describe('Sidebar', () => {
  it('renders logo and primary nav links', () => {
    render(
      <MemoryRouter>
        <Sidebar />
      </MemoryRouter>,
    )
    expect(screen.getByAltText('ReadinessIQ')).toBeInTheDocument()
    expect(screen.getByRole('link', { name: 'Overview' })).toHaveAttribute('href', '/')
    expect(screen.getByRole('link', { name: 'Sites' })).toBeInTheDocument()
    expect(screen.getByRole('link', { name: 'Parts' })).toBeInTheDocument()
    expect(screen.getByRole('link', { name: 'Suppliers' })).toBeInTheDocument()
  })
})
