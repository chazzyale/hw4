import { useEffect, useState, type FormEvent } from 'react'
import { Link, useNavigate, useSearchParams } from 'react-router-dom'
import { useAuth } from '../auth'

const MIN_PASSWORD = 8

// Step 1: "Forgot your password?" Enter your email and we send a one-time reset link.
export function ForgotPassword() {
  const { requestPasswordReset } = useAuth()
  const [email, setEmail] = useState('')
  const [sent, setSent] = useState<string | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [submitting, setSubmitting] = useState(false)

  async function submit(e: FormEvent) {
    e.preventDefault()
    setError(null)
    setSubmitting(true)
    try {
      setSent(await requestPasswordReset(email))
    } catch (err) {
      setError((err as Error).message)
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <section className="auth-page">
      <form className="auth-card" onSubmit={submit}>
        <p className="eyebrow">Account help</p>
        <h1>Reset your password</h1>
        {sent ? (
          <>
            <p className="form-success" role="status">{sent}</p>
            <p className="auth-switch">Didn&rsquo;t get it? Check your spam folder, or try again in a few minutes.</p>
          </>
        ) : (
          <>
            <p className="muted">Enter the email on your account and we&rsquo;ll send you a link to choose a new password.</p>
            <label>
              Email
              <input
                type="email"
                required
                autoComplete="email"
                value={email}
                onChange={e => {
                  setEmail(e.target.value)
                  setError(null)
                }}
              />
            </label>
            {error && <p className="form-error" role="alert">{error}</p>}
            <button type="submit" className="btn btn-primary btn-block" disabled={submitting}>
              {submitting ? 'Sending...' : 'Send reset link'}
            </button>
          </>
        )}
        <p className="auth-switch">
          Remembered it? <Link to="/login">Back to log in</Link>
        </p>
      </form>
    </section>
  )
}

// Step 2: the link from the email opens this page (/reset-password?token=...) to choose a new password.
export function ResetPassword() {
  const { checkResetLink, resetPassword } = useAuth()
  const navigate = useNavigate()
  const [params] = useSearchParams()
  const token = params.get('token') ?? ''
  const [linkValid, setLinkValid] = useState<boolean | null>(token ? null : false)
  const [password, setPassword] = useState('')
  const [confirm, setConfirm] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [submitting, setSubmitting] = useState(false)

  useEffect(() => {
    if (!token) return
    checkResetLink(token).then(setLinkValid).catch(() => setLinkValid(false))
    // Check the link once when the page opens.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [token])

  const mismatch = confirm.length > 0 && password !== confirm

  async function submit(e: FormEvent) {
    e.preventDefault()
    if (password.length < MIN_PASSWORD) return setError(`Password must be at least ${MIN_PASSWORD} characters.`)
    if (password !== confirm) return setError('Passwords do not match.')
    setSubmitting(true)
    try {
      await resetPassword(token, password, confirm)
      navigate('/', { replace: true })
    } catch (err) {
      setError((err as Error).message)
      setSubmitting(false)
    }
  }

  return (
    <section className="auth-page">
      <form className="auth-card" onSubmit={submit}>
        <p className="eyebrow">Account help</p>
        <h1>Choose a new password</h1>
        {linkValid === null ? (
          <p className="muted">Checking your reset link...</p>
        ) : !linkValid ? (
          <>
            <p className="form-error" role="alert">This reset link is invalid or has expired. Links work once and last 30 minutes.</p>
            <Link to="/forgot-password" className="btn btn-primary btn-block">Request a new link</Link>
          </>
        ) : (
          <>
            <label>
              New password
              <input
                type="password"
                required
                minLength={MIN_PASSWORD}
                autoComplete="new-password"
                value={password}
                onChange={e => {
                  setPassword(e.target.value)
                  setError(null)
                }}
              />
              <span className="field-hint">At least {MIN_PASSWORD} characters</span>
            </label>
            <label>
              Confirm new password
              <input
                type="password"
                required
                autoComplete="new-password"
                aria-invalid={mismatch}
                value={confirm}
                onChange={e => {
                  setConfirm(e.target.value)
                  setError(null)
                }}
              />
              {mismatch && <span className="field-error">Passwords do not match</span>}
            </label>
            {error && <p className="form-error" role="alert">{error}</p>}
            <button type="submit" className="btn btn-primary btn-block" disabled={submitting || mismatch}>
              {submitting ? 'Saving...' : 'Save new password'}
            </button>
          </>
        )}
        <p className="auth-switch">
          <Link to="/login">Back to log in</Link>
        </p>
      </form>
    </section>
  )
}
