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
  registerUser: vi.fn(),
}))

import { useAuth } from '../auth/AuthContext'
import { registerUser } from '../api'
import RegisterPage from './RegisterPage'

describe('RegisterPage', () => {
  const refreshUser = vi.fn()

  beforeEach(() => {
    navigate.mockReset()
    refreshUser.mockReset()
    refreshUser.mockResolvedValue({
      id: 1,
      name: 'Jane Doe',
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
    vi.mocked(registerUser).mockResolvedValue({
      message: 'User registered successfully',
    })
  })

  afterEach(() => {
    cleanup()
  })

  it('renders the registration form', () => {
    render(
      <MemoryRouter>
        <RegisterPage />
      </MemoryRouter>,
    )

    expect(screen.getByRole('heading', { name: /ReadinessIQ/i })).toBeInTheDocument()
    expect(screen.getByText(/Create your account/i)).toBeInTheDocument()
    expect(screen.getByLabelText(/^Name$/i)).toBeInTheDocument()
    expect(screen.getByLabelText(/Email/i)).toBeInTheDocument()
    expect(screen.getByLabelText(/^Password$/i)).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /Create account/i })).toBeInTheDocument()
    expect(screen.getByRole('link', { name: /Sign in/i })).toHaveAttribute('href', '/login')
  })

  it('submits registration data and redirects to overview', async () => {
    const user = userEvent.setup()

    render(
      <MemoryRouter>
        <RegisterPage />
      </MemoryRouter>,
    )

    await user.type(screen.getByLabelText(/^Name$/i), 'Jane Doe')
    await user.type(screen.getByLabelText(/Email/i), 'jane@example.com')
    await user.type(screen.getByLabelText(/^Password$/i), 'secret123')
    await user.click(screen.getByRole('button', { name: /Create account/i }))

    await waitFor(() => {
      expect(registerUser).toHaveBeenCalledWith({
        name: 'Jane Doe',
        email: 'jane@example.com',
        password: 'secret123',
      })
    })

    expect(refreshUser).toHaveBeenCalled()
    expect(navigate).toHaveBeenCalledWith('/')
  })

  it('shows an error when registration fails', async () => {
    vi.mocked(registerUser).mockRejectedValueOnce(new Error('Email already exists'))
    const user = userEvent.setup()

    render(
      <MemoryRouter>
        <RegisterPage />
      </MemoryRouter>,
    )

    await user.type(screen.getByLabelText(/^Name$/i), 'Jane Doe')
    await user.type(screen.getByLabelText(/Email/i), 'jane@example.com')
    await user.type(screen.getByLabelText(/^Password$/i), 'secret123')
    await user.click(screen.getByRole('button', { name: /Create account/i }))

    expect(await screen.findByRole('alert')).toHaveTextContent('Email already exists')
    expect(navigate).not.toHaveBeenCalled()
  })
})
