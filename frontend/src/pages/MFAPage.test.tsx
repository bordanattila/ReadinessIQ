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
  fetchMfaSetup: vi.fn(),
  verifyMfa: vi.fn(),
  logoutUser: vi.fn(),
}))

import { useAuth } from '../auth/AuthContext'
import { fetchMfaSetup, logoutUser, verifyMfa } from '../api'
import MFAPage from './MFAPage'

describe('MFAPage', () => {
  const refreshUser = vi.fn()

  beforeEach(() => {
    navigate.mockReset()
    refreshUser.mockReset()
    refreshUser.mockResolvedValue(undefined)
    vi.mocked(fetchMfaSetup).mockResolvedValue({
      otpauth_url: 'otpauth://totp/ReadinessIQ:test@test.com?secret=ABC&issuer=ReadinessIQ',
      secret: 'ABC',
    })
    vi.mocked(verifyMfa).mockResolvedValue({ message: 'MFA verified successfully' })
    vi.mocked(logoutUser).mockResolvedValue({ message: 'Logged out successfully' })
  })

  afterEach(() => {
    cleanup()
    vi.mocked(useAuth).mockReset()
  })

  it('redirects unauthenticated users to login', () => {
    vi.mocked(useAuth).mockReturnValue({
      user: null,
      loading: false,
      refreshUser,
      clearUser: vi.fn(),
    })

    render(
      <MemoryRouter>
        <MFAPage />
      </MemoryRouter>,
    )

    expect(navigate).toHaveBeenCalledWith('/login', { replace: true })
  })

  it('loads MFA setup and verifies an enrollment code', async () => {
    vi.mocked(useAuth).mockReturnValue({
      user: {
        id: 1,
        name: 'Jane',
        email: 'jane@example.com',
        mfa_verified: false,
        mfa_enabled: false,
      },
      loading: false,
      refreshUser,
      clearUser: vi.fn(),
    })

    const user = userEvent.setup()

    render(
      <MemoryRouter>
        <MFAPage />
      </MemoryRouter>,
    )

    expect(await screen.findByText(/Register your MFA device/i)).toBeInTheDocument()
    expect(fetchMfaSetup).toHaveBeenCalled()
    expect(screen.getByText('ABC')).toBeInTheDocument()

    await user.type(screen.getByLabelText(/Authentication code/i), '123456')
    await user.click(screen.getByRole('button', { name: /Verify/i }))

    await waitFor(() => {
      expect(verifyMfa).toHaveBeenCalledWith('123456')
    })
    expect(refreshUser).toHaveBeenCalled()
    expect(navigate).toHaveBeenCalledWith('/')
  })

  it('skips enrollment and returns to the dashboard', async () => {
    vi.mocked(useAuth).mockReturnValue({
      user: {
        id: 1,
        name: 'Jane',
        email: 'jane@example.com',
        mfa_verified: true,
        mfa_enabled: false,
      },
      loading: false,
      refreshUser,
      clearUser: vi.fn(),
    })

    const user = userEvent.setup()

    render(
      <MemoryRouter>
        <MFAPage />
      </MemoryRouter>,
    )

    await user.click(screen.getByRole('button', { name: /Skip for now/i }))
    expect(navigate).toHaveBeenCalledWith('/')
    expect(logoutUser).not.toHaveBeenCalled()
  })

  it('shows a verification prompt for MFA-enabled users', () => {
    vi.mocked(useAuth).mockReturnValue({
      user: {
        id: 1,
        name: 'Jane',
        email: 'jane@example.com',
        mfa_verified: false,
        mfa_enabled: true,
      },
      loading: false,
      refreshUser,
      clearUser: vi.fn(),
    })

    render(
      <MemoryRouter>
        <MFAPage />
      </MemoryRouter>,
    )

    expect(
      screen.getByText(/Enter the code from your authenticator app/i),
    ).toBeInTheDocument()
    expect(fetchMfaSetup).not.toHaveBeenCalled()
  })
})
