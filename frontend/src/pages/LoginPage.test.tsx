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

vi.mock('../auth/AuthContext', () => ({
  useAuth: vi.fn(),
}))

vi.mock('../api', () => ({
  loginUser: vi.fn(),
}))

import { useAuth } from '../auth/AuthContext'
import { loginUser } from '../api'
import LoginPage from './LoginPage'

describe('LoginPage', () => {
  const refreshUser = vi.fn()

  beforeEach(() => {
    navigate.mockReset()
    refreshUser.mockReset()
    refreshUser.mockResolvedValue({
      id: 1,
      name: 'Jane',
      email: 'jane@example.com',
      mfa_verified: false,
      mfa_enabled: false,
    })
    vi.mocked(useAuth).mockReturnValue({
      user: null,
      loading: false,
      refreshUser,
      clearUser: vi.fn(),
    })
    vi.mocked(loginUser).mockResolvedValue({ message: 'Login successful' })
  })

  afterEach(() => {
    cleanup()
  })

  it('renders the login form', () => {
    render(
      <MemoryRouter>
        <LoginPage />
      </MemoryRouter>,
    )

    expect(screen.getByRole('heading', { name: /ReadinessIQ/i })).toBeInTheDocument()
    expect(screen.getByText(/Sign in to your account/i)).toBeInTheDocument()
    expect(screen.getByLabelText(/Email/i)).toBeInTheDocument()
    expect(screen.getByLabelText(/Password/i)).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /Sign in/i })).toBeInTheDocument()
    expect(screen.getByRole('link', { name: /Create one/i })).toHaveAttribute('href', '/register')
  })

  it('submits credentials and navigates to overview when MFA is not enabled', async () => {
    const user = userEvent.setup()

    render(
      <MemoryRouter>
        <LoginPage />
      </MemoryRouter>,
    )

    await user.type(screen.getByLabelText(/Email/i), 'jane@example.com')
    await user.type(screen.getByLabelText(/Password/i), 'secret123')
    await user.click(screen.getByRole('button', { name: /Sign in/i }))

    await waitFor(() => {
      expect(loginUser).toHaveBeenCalledWith({
        email: 'jane@example.com',
        password: 'secret123',
      })
    })
    expect(refreshUser).toHaveBeenCalled()
    expect(navigate).toHaveBeenCalledWith('/')
  })

  it('submits credentials and navigates to MFA when verification is required', async () => {
    refreshUser.mockResolvedValueOnce({
      id: 1,
      name: 'Jane',
      email: 'jane@example.com',
      mfa_verified: false,
      mfa_enabled: true,
    })
    const user = userEvent.setup()

    render(
      <MemoryRouter>
        <LoginPage />
      </MemoryRouter>,
    )

    await user.type(screen.getByLabelText(/Email/i), 'jane@example.com')
    await user.type(screen.getByLabelText(/Password/i), 'secret123')
    await user.click(screen.getByRole('button', { name: /Sign in/i }))

    await waitFor(() => {
      expect(loginUser).toHaveBeenCalled()
    })
    expect(navigate).toHaveBeenCalledWith('/mfa')
  })

  it('submits credentials and navigates to overview when MFA is already verified', async () => {
    refreshUser.mockResolvedValueOnce({
      id: 1,
      name: 'Jane',
      email: 'jane@example.com',
      mfa_verified: true,
      mfa_enabled: true,
    })
    const user = userEvent.setup()

    render(
      <MemoryRouter>
        <LoginPage />
      </MemoryRouter>,
    )

    await user.type(screen.getByLabelText(/Email/i), 'jane@example.com')
    await user.type(screen.getByLabelText(/Password/i), 'secret123')
    await user.click(screen.getByRole('button', { name: /Sign in/i }))

    await waitFor(() => {
      expect(loginUser).toHaveBeenCalled()
    })
    expect(navigate).toHaveBeenCalledWith('/')
  })

  it('shows an error when login fails', async () => {
    vi.mocked(loginUser).mockRejectedValueOnce(new Error('Invalid credentials'))
    const user = userEvent.setup()

    render(
      <MemoryRouter>
        <LoginPage />
      </MemoryRouter>,
    )

    await user.type(screen.getByLabelText(/Email/i), 'jane@example.com')
    await user.type(screen.getByLabelText(/Password/i), 'wrong')
    await user.click(screen.getByRole('button', { name: /Sign in/i }))

    expect(await screen.findByRole('alert')).toHaveTextContent('Invalid credentials')
    expect(navigate).not.toHaveBeenCalled()
  })
})
