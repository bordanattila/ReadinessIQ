import { useState } from 'react'
import { NavLink, useNavigate } from 'react-router-dom'
import { useAuth } from '../auth/AuthContext'
import { logoutUser } from '../api'
import logo from '../assets/readinessiq_logo.png'
import styles from './sidebar.module.css'

export default function Sidebar() {
  const navigate = useNavigate()
  const { user, clearUser } = useAuth()
  const [loggingOut, setLoggingOut] = useState(false)
  const [logoutError, setLogoutError] = useState<string | null>(null)

  async function handleLogout() {
    setLoggingOut(true)
    setLogoutError(null)
    try {
      await logoutUser()
      clearUser()
      navigate('/')
    } catch (error) {
      setLogoutError(error instanceof Error ? error.message : 'Logout failed')
    } finally {
      setLoggingOut(false)
    }
  }

  return (
    <div className={styles.sidebar}>
      <img src={logo} alt="ReadinessIQ" />
      <nav aria-label="Primary">
        <ul>
          <li>
            <NavLink to="/" end>
              Overview
            </NavLink>
          </li>
          <li>
            <NavLink to="/sites">Sites</NavLink>
          </li>
          <li>
            <NavLink to="/parts">Parts</NavLink>
          </li>
          <li>
            <NavLink to="/suppliers">Suppliers</NavLink>
          </li>
        </ul>
      </nav>

      <div className={styles.authSection}>
        {user ? (
          <>
            <p className={styles.userName}>{user.name}</p>
            {!user.mfa_enabled ? (
              <nav aria-label="Security">
                <ul>
                  <li>
                    <NavLink to="/mfa">Set up MFA</NavLink>
                  </li>
                </ul>
              </nav>
            ) : null}
            <button
              type="button"
              className={styles.logoutButton}
              onClick={handleLogout}
              disabled={loggingOut}
            >
              {loggingOut ? 'Signing out…' : 'Log out'}
            </button>
            {logoutError ? (
              <p className={styles.logoutError} role="alert">
                {logoutError}
              </p>
            ) : null}
          </>
        ) : (
          <nav aria-label="Account">
            <ul>
              <li>
                <NavLink to="/login">Login</NavLink>
              </li>
              <li>
                <NavLink to="/register">Register</NavLink>
              </li>
            </ul>
          </nav>
        )}
      </div>
    </div>
  )
}
