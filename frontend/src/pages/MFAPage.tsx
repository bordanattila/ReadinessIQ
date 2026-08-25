import { type FormEvent, useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { QRCodeSVG } from 'qrcode.react'
import { useAuth } from '../auth/AuthContext'
import { fetchMfaSetup, logoutUser, verifyMfa } from '../api'
import styles from './AuthPage.module.css'

export default function MFAPage() {
  const navigate = useNavigate()
  const { user, loading, refreshUser, clearUser } = useAuth()
  const [mfaCode, setMfaCode] = useState('')
  const [otpauthUrl, setOtpauthUrl] = useState<string | null>(null)
  const [mfaSecret, setMfaSecret] = useState<string | null>(null)
  const [setupLoading, setSetupLoading] = useState(false)
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const enrolling = user !== null && !user.mfa_enabled

  useEffect(() => {
    if (loading) {
      return
    }
    if (!user) {
      navigate('/login', { replace: true })
    }
  }, [loading, user, navigate])

  useEffect(() => {
    if (loading || !user || user.mfa_enabled) {
      return
    }

    let cancelled = false
    setSetupLoading(true)
    setError(null)

    void fetchMfaSetup()
      .then((setup) => {
        if (!cancelled) {
          setOtpauthUrl(setup.otpauth_url)
          setMfaSecret(setup.secret)
        }
      })
      .catch((setupError) => {
        if (!cancelled) {
          setError(
            setupError instanceof Error ? setupError.message : 'Could not start MFA setup',
          )
        }
      })
      .finally(() => {
        if (!cancelled) {
          setSetupLoading(false)
        }
      })

    return () => {
      cancelled = true
    }
  }, [loading, user])

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    setSubmitting(true)
    setError(null)

    try {
      await verifyMfa(mfaCode)
      await refreshUser()
      navigate('/')
    } catch (submitError) {
      setError(
        submitError instanceof Error ? submitError.message : 'MFA verification failed',
      )
    } finally {
      setSubmitting(false)
    }
  }

  async function handleSignOut() {
    setSubmitting(true)
    setError(null)
    try {
      await logoutUser()
      clearUser()
      navigate('/login')
    } catch (cancelError) {
      setError(cancelError instanceof Error ? cancelError.message : 'Could not sign out')
    } finally {
      setSubmitting(false)
    }
  }

  if (loading || !user) {
    return (
      <div className={styles.page}>
        <p className={styles.subtitle}>Checking your session…</p>
      </div>
    )
  }

  if (user.mfa_enabled && user.mfa_verified) {
    return (
      <div className={styles.page}>
        <div className={styles.card}>
          <h1 className={styles.brand}>
            Readiness<span className={styles.brandAccent}>IQ</span>
          </h1>
          <p className={styles.subtitle}>MFA is already set up for this session.</p>
          <button
            type="button"
            className={styles.dashboardLink}
            onClick={() => navigate('/')}
          >
            Go to dashboard
          </button>
        </div>
      </div>
    )
  }

  return (
    <div className={styles.page}>
      <div className={styles.card}>
        {enrolling ? (
          <button
            type="button"
            className={styles.backLink}
            onClick={() => navigate('/')}
          >
            ← Back to dashboard
          </button>
        ) : null}
        <h1 className={styles.brand}>
          Readiness<span className={styles.brandAccent}>IQ</span>
        </h1>
        <p className={styles.subtitle}>
          {enrolling
            ? 'Register your MFA device'
            : 'Enter the code from your authenticator app'}
        </p>

        {enrolling && setupLoading ? (
          <p className={styles.subtitle}>Preparing your MFA setup…</p>
        ) : null}

        {enrolling && otpauthUrl ? (
          <div className={styles.qrWrap}>
            <QRCodeSVG value={otpauthUrl} size={180} />
            <p className={styles.qrHelp}>
              Scan this QR code with Google Authenticator, Authy, or another TOTP app.
            </p>
          </div>
        ) : null}

        {enrolling && mfaSecret ? (
          <div className={styles.secretWrap}>
            <p className={styles.qrHelp}>
              Or enter this secret manually in your authenticator app:
            </p>
            <code className={styles.secret}>{mfaSecret}</code>
          </div>
        ) : null}

        <form className={styles.form} onSubmit={handleSubmit}>
          <div className={styles.field}>
            <label className={styles.label} htmlFor="mfa-code">
              Authentication code
            </label>
            <input
              id="mfa-code"
              className={styles.input}
              type="text"
              inputMode="numeric"
              autoComplete="one-time-code"
              required
              value={mfaCode}
              onChange={(event) => setMfaCode(event.target.value)}
            />
          </div>

          {error ? (
            <p className={styles.error} role="alert">
              {error}
            </p>
          ) : null}

          <button className={styles.button} type="submit" disabled={submitting || setupLoading}>
            {submitting ? 'Verifying…' : 'Verify'}
          </button>
          {enrolling ? (
            <button
              className={styles.secondaryButton}
              type="button"
              onClick={() => navigate('/')}
              disabled={submitting}
            >
              Skip for now
            </button>
          ) : (
            <button
              className={styles.secondaryButton}
              type="button"
              onClick={() => void handleSignOut()}
              disabled={submitting}
            >
              Sign out
            </button>
          )}
        </form>
      </div>
    </div>
  )
}
