import { type FormEvent, useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { registerUser } from '../api'
import styles from './AuthPage.module.css'

export default function RegisterPage() {
  const navigate = useNavigate()
  const [name, setName] = useState('')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [success, setSuccess] = useState<string | null>(null)

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    setLoading(true)
    setError(null)
    setSuccess(null)

    try {
      const response = await registerUser({ name, email, password })
      setSuccess(response.message)
      navigate('/login')
    } catch (submitError) {
      setError(
        submitError instanceof Error ? submitError.message : 'Registration failed',
      )
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className={styles.page}>
      <div className={styles.card}>
        <Link to="/" className={styles.backLink}>
          ← Back to overview
        </Link>
        <h1 className={styles.brand}>
          Readiness<span className={styles.brandAccent}>IQ</span>
        </h1>
        <p className={styles.subtitle}>Create your account</p>

        <form className={styles.form} onSubmit={handleSubmit}>
          <div className={styles.field}>
            <label className={styles.label} htmlFor="register-name">
              Name
            </label>
            <input
              id="register-name"
              className={styles.input}
              type="text"
              autoComplete="name"
              required
              value={name}
              onChange={(event) => setName(event.target.value)}
            />
          </div>

          <div className={styles.field}>
            <label className={styles.label} htmlFor="register-email">
              Email
            </label>
            <input
              id="register-email"
              className={styles.input}
              type="email"
              autoComplete="email"
              required
              value={email}
              onChange={(event) => setEmail(event.target.value)}
            />
          </div>

          <div className={styles.field}>
            <label className={styles.label} htmlFor="register-password">
              Password
            </label>
            <input
              id="register-password"
              className={styles.input}
              type="password"
              autoComplete="new-password"
              required
              value={password}
              onChange={(event) => setPassword(event.target.value)}
            />
          </div>

          {error ? (
            <p className={styles.error} role="alert">
              {error}
            </p>
          ) : null}

          {success ? (
            <p className={styles.success} role="status">
              {success}
            </p>
          ) : null}

          <button className={styles.button} type="submit" disabled={loading}>
            {loading ? 'Creating account…' : 'Create account'}
          </button>
        </form>

        <p className={styles.footer}>
          Already have an account? <Link to="/login">Sign in</Link>
        </p>
      </div>
    </div>
  )
}
