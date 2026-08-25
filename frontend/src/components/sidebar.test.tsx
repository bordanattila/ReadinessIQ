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

vi.mock('../auth/useAuth', () => ({
  useAuth: vi.fn(),
}))

vi.mock('../api', () => ({
  logoutUser: vi.fn(),
}))

import { useAuth } from '../auth/useAuth'
import { logoutUser } from '../api'
import Sidebar from './sidebar'

describe('Sidebar', () => {
  beforeEach(() => {
    navigate.mockReset()
    vi.mocked(logoutUser).mockResolvedValue({ message: 'Logged out successfully' })
  })

  afterEach(() => {
    cleanup()
    vi.mocked(useAuth).mockReset()
  })

  it('renders login and register links when signed out', () => {
    vi.mocked(useAuth).mockReturnValue({
      user: null,
      loading: false,
      refreshUser: vi.fn(),
      clearUser: vi.fn(),
    })

    render(
      <MemoryRouter>
        <Sidebar />
      </MemoryRouter>,
    )

    expect(screen.getByRole('link', { name: 'Login' })).toBeInTheDocument()
    expect(screen.getByRole('link', { name: 'Register' })).toBeInTheDocument()
    expect(screen.queryByRole('button', { name: /Log out/i })).not.toBeInTheDocument()
  })

  it('renders the user name and logout button when signed in', () => {
    vi.mocked(useAuth).mockReturnValue({
      user: { id: 1, name: 'Jane Doe', email: 'jane@example.com', mfa_verified: true, mfa_enabled: false },
      loading: false,
      refreshUser: vi.fn(),
      clearUser: vi.fn(),
    })

    render(
      <MemoryRouter>
        <Sidebar />
      </MemoryRouter>,
    )

    expect(screen.getByText('Jane Doe')).toBeInTheDocument()
    expect(screen.getByRole('link', { name: 'Set up MFA' })).toHaveAttribute('href', '/mfa')
    expect(screen.getByRole('button', { name: /Log out/i })).toBeInTheDocument()
    expect(screen.queryByRole('link', { name: 'Login' })).not.toBeInTheDocument()
  })

  it('hides the MFA setup link after MFA is enabled', () => {
    vi.mocked(useAuth).mockReturnValue({
      user: { id: 1, name: 'Jane Doe', email: 'jane@example.com', mfa_verified: true, mfa_enabled: true },
      loading: false,
      refreshUser: vi.fn(),
      clearUser: vi.fn(),
    })

    render(
      <MemoryRouter>
        <Sidebar />
      </MemoryRouter>,
    )

    expect(screen.queryByRole('link', { name: 'Set up MFA' })).not.toBeInTheDocument()
  })

  it('logs out, clears auth state, and returns to overview', async () => {
    const clearUser = vi.fn()
    vi.mocked(useAuth).mockReturnValue({
      user: { id: 1, name: 'Jane Doe', email: 'jane@example.com', mfa_verified: true, mfa_enabled: false },
      loading: false,
      refreshUser: vi.fn(),
      clearUser,
    })

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
    expect(clearUser).toHaveBeenCalled()
    expect(navigate).toHaveBeenCalledWith('/')
  })
})
