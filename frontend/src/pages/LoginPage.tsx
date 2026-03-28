import { useState, useCallback } from 'react'
import { Navigate } from 'react-router-dom'
import { useAuth } from '../hooks/useAuth'
import { API_BASE } from '../config'
import styles from './LoginPage.module.css'

interface OAuthProvider {
  id: string
  label: string
  icon: string
}

const OAUTH_PROVIDERS: OAuthProvider[] = [
  { id: 'google', label: 'Continue with Google', icon: 'G' },
  { id: 'apple', label: 'Continue with Apple', icon: '\uF8FF' },
  { id: 'facebook', label: 'Continue with Facebook', icon: 'f' },
  { id: 'github', label: 'Continue with GitHub', icon: '\u2387' },
]

export default function LoginPage() {
  const { user, loading: authLoading } = useAuth()
  const [loadingProvider, setLoadingProvider] = useState<string | null>(null)
  const [error, setError] = useState<string | null>(null)

  const handleOAuthLogin = useCallback(async (provider: string) => {
    setError(null)
    setLoadingProvider(provider)

    try {
      const res = await fetch(`${API_BASE}/auth/login/${encodeURIComponent(provider)}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
      })

      if (!res.ok) {
        const body = await res.json().catch(() => null)
        throw new Error(body?.detail ?? `Login failed (${res.status})`)
      }

      const data: { authorization_url: string } = await res.json()

      // Store provider and state in sessionStorage so the callback can correlate
      sessionStorage.setItem('oauth_provider', provider)
      try {
        const url = new URL(data.authorization_url)
        const state = url.searchParams.get('state')
        if (state) {
          sessionStorage.setItem('oauth_state', state)
        }
      } catch {
        // URL parsing failed — proceed without storing state
      }

      window.location.href = data.authorization_url
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An unexpected error occurred')
      setLoadingProvider(null)
    }
  }, [])

  // Redirect authenticated users away from login
  if (authLoading) {
    return (
      <div className={styles.loginContainer}>
        <div className={styles.loginCard}>
          <div className={styles.header}>
            <span className={styles.spinner} role="status" aria-label="Loading" />
          </div>
        </div>
      </div>
    )
  }

  if (user) {
    return <Navigate to="/" replace />
  }

  return (
    <div className={styles.loginContainer}>
      <div className={styles.loginCard}>
        <div className={styles.header}>
          <h1>Isnad Graph</h1>
          <p>Hadith Analysis Platform</p>
        </div>

        {error && (
          <div className={styles.errorBanner} role="alert">
            {error}
          </div>
        )}

        <div className={styles.oauthSection}>
          {OAUTH_PROVIDERS.map((provider) => (
            <button
              key={provider.id}
              type="button"
              className={styles.oauthBtn}
              disabled={loadingProvider !== null}
              onClick={() => handleOAuthLogin(provider.id)}
              aria-label={provider.label}
            >
              {loadingProvider === provider.id ? (
                <span className={styles.spinner} role="status" aria-label="Loading" />
              ) : (
                <span className={styles.oauthIcon} aria-hidden="true">
                  {provider.icon}
                </span>
              )}
              {provider.label}
            </button>
          ))}
        </div>

        <div className={styles.divider}>or</div>

        <div className={styles.emailSection}>
          <div className={styles.comingSoon}>
            <strong>Email &amp; Password</strong>
            Sign up with email is coming soon.
          </div>
        </div>
      </div>
    </div>
  )
}
