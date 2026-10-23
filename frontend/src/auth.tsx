import { createContext, useContext, useEffect, useState, type ReactNode } from 'react'
import { TOKEN_KEY } from './api'

export type User = { id: number; first_name: string; last_name: string; name: string; email: string }

export type RegisterInput = {
  first_name: string
  last_name: string
  email: string
  password: string
  confirm_password: string
}

type AuthState = {
  user: User | null
  ready: boolean
  login: (email: string, password: string) => Promise<void>
  register: (input: RegisterInput) => Promise<void>
  logout: () => void
  // Self-service password reset
  requestPasswordReset: (email: string) => Promise<string>
  checkResetLink: (token: string) => Promise<boolean>
  resetPassword: (token: string, password: string, confirm_password: string) => Promise<void>
}

const AuthContext = createContext<AuthState | null>(null)

async function postJson<T>(url: string, body: unknown): Promise<T> {
  const res = await fetch(url, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  })
  const data = await res.json().catch(() => ({}))
  if (!res.ok) throw new Error(typeof data.detail === 'string' ? data.detail : 'Something went wrong. Please try again.')
  return data as T
}

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null)
  const [ready, setReady] = useState(!localStorage.getItem(TOKEN_KEY))

  // Restore the session from a saved token on page load.
  useEffect(() => {
    const token = localStorage.getItem(TOKEN_KEY)
    if (!token) return
    fetch('/api/auth/me', { headers: { Authorization: `Bearer ${token}` } })
      .then(res => (res.ok ? res.json() : Promise.reject()))
      .then(setUser)
      .catch(() => localStorage.removeItem(TOKEN_KEY))
      .finally(() => setReady(true))
  }, [])

  function startSession({ token, user }: { token: string; user: User }) {
    localStorage.setItem(TOKEN_KEY, token)
    setUser(user)
  }

  const value: AuthState = {
    user,
    ready,
    login: async (email, password) => startSession(await postJson('/api/auth/login', { email, password })),
    register: async input => startSession(await postJson('/api/auth/register', input)),
    logout: () => {
      localStorage.removeItem(TOKEN_KEY)
      setUser(null)
    },
    requestPasswordReset: async email =>
      (await postJson<{ message: string }>('/api/auth/forgot-password', { email })).message,
    checkResetLink: async token => (await postJson<{ valid: boolean }>('/api/auth/reset-password/check', { token })).valid,
    // A successful reset logs the shopper in with the new password.
    resetPassword: async (token, password, confirm_password) =>
      startSession(await postJson('/api/auth/reset-password', { token, password, confirm_password })),
  }

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}

// eslint-disable-next-line react-refresh/only-export-components
export function useAuth(): AuthState {
  const ctx = useContext(AuthContext)
  if (!ctx) throw new Error('useAuth must be used inside AuthProvider')
  return ctx
}
