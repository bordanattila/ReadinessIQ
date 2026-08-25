import { cleanup, render, screen } from '@testing-library/react'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import { afterEach, describe, expect, it, vi } from 'vitest'

vi.mock('../auth/AuthContext', () => ({
  useAuth: vi.fn(),
}))

import { useAuth } from '../auth/AuthContext'
import AuthGate from './AuthGate'

function TestApp() {
  return (
    <Routes>
      <Route path="/" element={<AuthGate />}>
        <Route index element={<p>Protected dashboard</p>} />
      </Route>
      <Route path="/login" element={<p>Login page</p>} />
      <Route path="/register" element={<p>Register page</p>} />
    </Routes>
  )
}

describe('AuthGate', () => {
  afterEach(() => {
    cleanup()
    vi.mocked(useAuth).mockReset()
  })

  it('shows a loading message while checking the session', () => {
    vi.mocked(useAuth).mockReturnValue({
      user: null,
      loading: true,
      refreshUser: vi.fn(),
      clearUser: vi.fn(),
    })

    render(
      <MemoryRouter>
        <TestApp />
      </MemoryRouter>,
    )

    expect(screen.getByText(/Checking your session/i)).toBeInTheDocument()
    expect(screen.queryByText('Protected dashboard')).not.toBeInTheDocument()
  })

  it('shows a sign-in prompt when unauthenticated', () => {
    vi.mocked(useAuth).mockReturnValue({
      user: null,
      loading: false,
      refreshUser: vi.fn(),
      clearUser: vi.fn(),
    })

    render(
      <MemoryRouter>
        <TestApp />
      </MemoryRouter>,
    )

    expect(screen.getByRole('heading', { name: /Sign in required/i })).toBeInTheDocument()
    expect(screen.getByRole('link', { name: /Log in/i })).toHaveAttribute('href', '/login')
    expect(screen.getByRole('link', { name: /Register/i })).toHaveAttribute('href', '/register')
    expect(screen.queryByText('Protected dashboard')).not.toBeInTheDocument()
  })

  it('allows dashboard access when MFA is not enabled', () => {
    vi.mocked(useAuth).mockReturnValue({
      user: {
        id: 1,
        name: 'Jane',
        email: 'jane@example.com',
        mfa_verified: false,
        mfa_enabled: false,
      },
      loading: false,
      refreshUser: vi.fn(),
      clearUser: vi.fn(),
    })

    render(
      <MemoryRouter>
        <TestApp />
      </MemoryRouter>,
    )

    expect(screen.getByText('Protected dashboard')).toBeInTheDocument()
  })

  it('redirects to MFA when verification is required', () => {
    vi.mocked(useAuth).mockReturnValue({
      user: {
        id: 1,
        name: 'Jane',
        email: 'jane@example.com',
        mfa_verified: false,
        mfa_enabled: true,
      },
      loading: false,
      refreshUser: vi.fn(),
      clearUser: vi.fn(),
    })

    render(
      <MemoryRouter initialEntries={['/']}>
        <Routes>
          <Route path="/" element={<AuthGate />}>
            <Route index element={<p>Protected dashboard</p>} />
          </Route>
          <Route path="/mfa" element={<p>MFA page</p>} />
        </Routes>
      </MemoryRouter>,
    )

    expect(screen.getByText('MFA page')).toBeInTheDocument()
    expect(screen.queryByText('Protected dashboard')).not.toBeInTheDocument()
  })

  it('renders protected content when authenticated', () => {
    vi.mocked(useAuth).mockReturnValue({
      user: {
        id: 1,
        name: 'Jane',
        email: 'jane@example.com',
        mfa_verified: true,
        mfa_enabled: true,
      },
      loading: false,
      refreshUser: vi.fn(),
      clearUser: vi.fn(),
    })

    render(
      <MemoryRouter>
        <TestApp />
      </MemoryRouter>,
    )

    expect(screen.getByText('Protected dashboard')).toBeInTheDocument()
    expect(screen.queryByText(/Sign in required/i)).not.toBeInTheDocument()
  })
})
