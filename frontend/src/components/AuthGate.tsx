import { Link, Navigate, Outlet } from 'react-router-dom'
import { requiresMfaVerification } from '../auth/routes'
import { useAuth } from '../auth/AuthContext'
import styles from './AuthGate.module.css'

export default function AuthGate() {
  const { user, loading } = useAuth()

  if (loading) {
    return <p className={styles.loading}>Checking your session…</p>
  }

  if (!user) {
    return (
      <div className={styles.gate}>
        <div className={styles.card}>
          <h2 className={styles.title}>Sign in required</h2>
          <p className={styles.message}>
            Log in or create an account to view readiness data, rankings, and site details.
          </p>
          <div className={styles.actions}>
            <Link to="/login" className={styles.primaryLink}>
              Log in
            </Link>
            <Link to="/register" className={styles.secondaryLink}>
              Register
            </Link>
          </div>
        </div>
      </div>
    )
  }

  if (requiresMfaVerification(user)) {
    return <Navigate to="/mfa" replace />
  }

  return <Outlet />
}
