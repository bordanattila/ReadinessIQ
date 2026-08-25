import { cleanup, render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter } from 'react-router-dom'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

const navigate = vi.fn()

vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual('react-router-dom')
  return {
    ...actual,
    useNavigate: () => navigate,
  }
})

vi.mock('../api', () => ({
  logoutUser: vi.fn(),
}))

import { logoutUser } from '../api'
import Sidebar from './sidebar'

describe('Sidebar', () => {
  beforeEach(() => {
    navigate.mockReset()
    vi.mocked(logoutUser).mockResolvedValue({ message: 'Logged out successfully' })
  })

  afterEach(() => {
    cleanup()
  })

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
    expect(screen.getByRole('button', { name: /Log out/i })).toBeInTheDocument()
  })

  it('logs out and navigates to login', async () => {
    const user = userEvent.setup()

    render(
      <MemoryRouter>
        <Sidebar />
      </MemoryRouter>,
    )

    await user.click(screen.getByRole('button', { name: /Log out/i }))

    await waitFor(() => {
      expect(logoutUser).toHaveBeenCalled()
    })
    expect(navigate).toHaveBeenCalledWith('/login')
  })
})
