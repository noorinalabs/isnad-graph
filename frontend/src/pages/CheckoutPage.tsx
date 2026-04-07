import { Link, useLocation } from 'react-router-dom'

export default function CheckoutPage() {
  const location = useLocation()
  const state = location.state as { tier?: string; interval?: string } | null

  return (
    <div
      style={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        minHeight: '100vh',
        background: 'var(--color-background)',
        padding: 'var(--spacing-6)',
      }}
    >
      <div
        style={{
          maxWidth: 480,
          width: '100%',
          textAlign: 'center',
          padding: 'var(--spacing-10)',
          background: 'var(--color-card)',
          border: 'var(--border-width-thin) solid var(--color-border)',
          borderRadius: 'var(--radius-xl)',
          boxShadow: 'var(--shadow-xl)',
        }}
      >
        <div
          style={{
            width: 56,
            height: 56,
            borderRadius: '50%',
            background: 'var(--color-primary)',
            color: 'var(--color-primary-foreground)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            margin: '0 auto var(--spacing-6)',
          }}
        >
          <svg
            width="28"
            height="28"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="2"
            strokeLinecap="round"
            strokeLinejoin="round"
          >
            <rect x="1" y="4" width="22" height="16" rx="2" ry="2" />
            <line x1="1" y1="10" x2="23" y2="10" />
          </svg>
        </div>

        <h1
          style={{
            fontFamily: 'var(--font-heading)',
            fontSize: 'var(--text-2xl)',
            fontWeight: 700,
            color: 'var(--color-foreground)',
            marginBottom: 'var(--spacing-3)',
          }}
        >
          Payment coming soon
        </h1>

        <p
          style={{
            fontSize: 'var(--text-base)',
            color: 'var(--color-muted-foreground)',
            lineHeight: 1.6,
            marginBottom: 'var(--spacing-4)',
          }}
        >
          {state?.tier
            ? `You selected the ${state.tier.charAt(0).toUpperCase() + state.tier.slice(1)} plan (${state.interval ?? 'monthly'}). `
            : ''}
          We are currently setting up payment processing. Check back soon to complete your
          subscription.
        </p>

        <p
          style={{
            fontSize: 'var(--text-sm)',
            color: 'var(--color-muted-foreground)',
            marginBottom: 'var(--spacing-8)',
          }}
        >
          In the meantime, your free trial access continues.
        </p>

        <div style={{ display: 'flex', gap: 'var(--spacing-3)', justifyContent: 'center' }}>
          <Link
            to="/pricing"
            style={{
              padding: 'var(--spacing-2_5) var(--spacing-5)',
              borderRadius: 'var(--radius-md)',
              border: 'var(--border-width-thin) solid var(--color-border)',
              fontFamily: 'var(--font-body)',
              fontSize: 'var(--text-sm)',
              fontWeight: 500,
              color: 'var(--color-foreground)',
              textDecoration: 'none',
              background: 'var(--color-card)',
            }}
          >
            Back to pricing
          </Link>
          <Link
            to="/"
            style={{
              padding: 'var(--spacing-2_5) var(--spacing-5)',
              borderRadius: 'var(--radius-md)',
              fontFamily: 'var(--font-body)',
              fontSize: 'var(--text-sm)',
              fontWeight: 600,
              color: 'var(--color-primary-foreground)',
              background: 'var(--color-primary)',
              textDecoration: 'none',
            }}
          >
            Continue exploring
          </Link>
        </div>
      </div>
    </div>
  )
}
