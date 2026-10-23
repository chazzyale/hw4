import { useState, type ChangeEvent, type FormEvent } from 'react'
import { Link, Navigate, useNavigate } from 'react-router-dom'
import { useAuth } from '../auth'

const MIN_PASSWORD = 8

export default function Register() {
  const { user, register } = useAuth()
  const navigate = useNavigate()
  const [form, setForm] = useState({ firstName: '', lastName: '', email: '', password: '', confirm: '' })
  const [error, setError] = useState<string | null>(null)
  const [submitting, setSubmitting] = useState(false)

  if (user && !submitting) return <Navigate to="/" replace />

  const update = (field: keyof typeof form) => (e: ChangeEvent<HTMLInputElement>) => {
    setForm(f => ({ ...f, [field]: e.target.value }))
    setError(null)
  }

  const mismatch = form.confirm.length > 0 && form.password !== form.confirm

  async function submit(e: FormEvent) {
    e.preventDefault()
    if (form.password.length < MIN_PASSWORD) return setError(`Password must be at least ${MIN_PASSWORD} characters.`)
    if (form.password !== form.confirm) return setError('Passwords do not match.')
    setSubmitting(true)
    try {
      await register({
        first_name: form.firstName,
        last_name: form.lastName,
        email: form.email,
        password: form.password,
        confirm_password: form.confirm,
      })
      navigate('/')
    } catch (err) {
      setError((err as Error).message)
      setSubmitting(false)
    }
  }

  return (
    <section className="auth-page">
      <form className="auth-card" onSubmit={submit}>
        <p className="eyebrow">Join the Bulldog community</p>
        <h1>Create account</h1>
        <div className="form-row">
          <label>
            First name
            <input required autoComplete="given-name" value={form.firstName} onChange={update('firstName')} />
          </label>
          <label>
            Last name
            <input required autoComplete="family-name" value={form.lastName} onChange={update('lastName')} />
          </label>
        </div>
        <label>
          Email
          <input type="email" required autoComplete="email" value={form.email} onChange={update('email')} />
        </label>
        <label>
          Password
          <input
            type="password"
            required
            minLength={MIN_PASSWORD}
            autoComplete="new-password"
            value={form.password}
            onChange={update('password')}
          />
          <span className="field-hint">At least {MIN_PASSWORD} characters</span>
        </label>
        <label>
          Confirm password
          <input
            type="password"
            required
            autoComplete="new-password"
            aria-invalid={mismatch}
            value={form.confirm}
            onChange={update('confirm')}
          />
          {mismatch && <span className="field-error">Passwords do not match</span>}
        </label>
        {error && <p className="form-error" role="alert">{error}</p>}
        <button type="submit" className="btn btn-primary btn-block" disabled={submitting || mismatch}>
          {submitting ? 'Creating account...' : 'Create account'}
        </button>
        <p className="auth-switch">
          Already have an account? <Link to="/login">Log in</Link>
        </p>
      </form>
    </section>
  )
}
