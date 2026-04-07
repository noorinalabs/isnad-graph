import { Link } from 'react-router-dom'
import { useSubscription } from '../hooks/useSubscription'

export default function TrialBanner() {
  const { isTrial, daysRemaining, isLoading } = useSubscription()

  if (isLoading || !isTrial) return null

  const urgent = daysRemaining <= 2

  return (
    <div
      role="status"
      style={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        gap: 'var(--spacing-3)',
        padding: 'var(--spacing-2) var(--spacing-4)',
        background: urgent ? 'var(--color-destructive)' : 'var(--color-primary)',
        color: urgent ? 'white' : 'var(--color-primary-foreground)',
        fontSize: 'var(--text-sm)',
        fontFamily: 'var(--font-body)',
        fontWeight: 500,
      }}
    >
      <svg
        width="16"
        height="16"
        viewBox="0 0 24 24"
        fill="none"
        stroke="currentColor"
        strokeWidth="2"
        strokeLinecap="round"
        strokeLinejoin="round"
        aria-hidden="true"
      >
        <circle cx="12" cy="12" r="10" />
        <polyline points="12 6 12 12 16 14" />
      </svg>
      <span>
        {daysRemaining === 0
          ? 'Your free trial expires today.'
          : daysRemaining === 1
            ? '1 day remaining in your free trial.'
            : `${daysRemaining} days remaining in your free trial.`}
      </span>
      <Link
        to="/pricing"
        style={{
          color: 'inherit',
          fontWeight: 700,
          textDecoration: 'underline',
          textUnderlineOffset: '2px',
        }}
      >
        View plans
      </Link>
    </div>
  )
}
