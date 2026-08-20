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
  loginUser: vi.fn(),
}))

import { loginUser } from '../api'
import LoginPage from './LoginPage'

describe('LoginPage', () => {
  beforeEach(() => {
    navigate.mockReset()
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

  it('submits credentials and navigates to overview on success', async () => {
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
