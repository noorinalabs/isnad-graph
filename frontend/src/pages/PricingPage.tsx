import { useState } from 'react'
import { Link } from 'react-router-dom'
import { useSubscription } from '../hooks/useSubscription'

type BillingInterval = 'monthly' | 'annual'

interface Tier {
  id: string
  name: string
  monthlyPrice: number | null
  description: string
  features: string[]
  cta: string
  popular?: boolean
}

const tiers: Tier[] = [
  {
    id: 'trial',
    name: 'Trial',
    monthlyPrice: 0,
    description: 'Free for 7 days',
    features: [
      '100 searches per day',
      'Basic hadith browsing',
      'Single user',
    ],
    cta: 'Current plan',
  },
  {
    id: 'individual',
    name: 'Individual',
    monthlyPrice: 14.95,
    description: 'For independent researchers',
    features: [
      'Unlimited searches',
      'Graph visualization',
      'Export data (CSV, JSON)',
      'Saved searches',
      'Narrator network analysis',
      'Cross-collection parallels',
    ],
    cta: 'Get started',
    popular: true,
  },
  {
    id: 'team',
    name: 'Team',
    monthlyPrice: 19.95,
    description: 'Per user/month',
    features: [
      'Everything in Individual',
      'Shared workspace',
      'Collaborative annotations',
      'Team analytics dashboard',
      'Priority support',
    ],
    cta: 'Get started',
  },
  {
    id: 'enterprise',
    name: 'Enterprise',
    monthlyPrice: null,
    description: 'Custom pricing',
    features: [
      'Everything in Team',
      'SSO / SAML integration',
      'Dedicated support engineer',
      'Custom SLA',
      'Custom integrations',
      'On-premise deployment option',
    ],
    cta: 'Contact us',
  },
]

function formatPrice(price: number, interval: BillingInterval): string {
  if (price === 0) return 'Free'
  if (interval === 'annual') {
    const annual = price * 10 // 2 months free
    return `$${(annual / 12).toFixed(2)}`
  }
  return `$${price.toFixed(2)}`
}

function CheckIcon() {
  return (
    <svg
      width="16"
      height="16"
      viewBox="0 0 24 24"
      fill="none"
      stroke="var(--color-primary)"
      strokeWidth="2.5"
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden="true"
      style={{ flexShrink: 0, marginTop: 2 }}
    >
      <polyline points="20 6 9 17 4 12" />
    </svg>
  )
}

export default function PricingPage() {
  const [interval, setInterval] = useState<BillingInterval>('monthly')
  const { subscription } = useSubscription()

  return (
    <div
      style={{
        minHeight: '100vh',
        background: 'var(--color-background)',
        padding: 'var(--spacing-10) var(--spacing-6)',
      }}
    >
      <div style={{ maxWidth: 1200, margin: '0 auto' }}>
        {/* Header */}
        <div style={{ textAlign: 'center', marginBottom: 'var(--spacing-10)' }}>
          <Link
            to="/"
            style={{
              display: 'inline-block',
              marginBottom: 'var(--spacing-6)',
              fontFamily: 'var(--font-heading)',
              fontSize: 'var(--text-sm)',
              color: 'var(--color-primary)',
              textDecoration: 'none',
            }}
          >
            &larr; Back to Isnad Graph
          </Link>
          <h1
            style={{
              fontFamily: 'var(--font-heading)',
              fontSize: 'var(--text-3xl)',
              fontWeight: 700,
              color: 'var(--color-foreground)',
              marginBottom: 'var(--spacing-3)',
            }}
          >
            Choose your plan
          </h1>
          <p
            style={{
              fontSize: 'var(--text-lg)',
              color: 'var(--color-muted-foreground)',
              maxWidth: 600,
              margin: '0 auto var(--spacing-8)',
              lineHeight: 1.6,
            }}
          >
            Access the most comprehensive computational hadith analysis platform.
            Start free, upgrade when you need more.
          </p>

          {/* Billing toggle */}
          <div
            style={{
              display: 'inline-flex',
              alignItems: 'center',
              gap: 'var(--spacing-3)',
              padding: 'var(--spacing-1)',
              background: 'var(--color-accent)',
              borderRadius: 'var(--radius-full)',
            }}
          >
            <button
              onClick={() => setInterval('monthly')}
              style={{
                padding: 'var(--spacing-2) var(--spacing-5)',
                borderRadius: 'var(--radius-full)',
                border: 'none',
                fontFamily: 'var(--font-body)',
                fontSize: 'var(--text-sm)',
                fontWeight: 600,
                cursor: 'pointer',
                background:
                  interval === 'monthly' ? 'var(--color-card)' : 'transparent',
                color:
                  interval === 'monthly'
                    ? 'var(--color-foreground)'
                    : 'var(--color-muted-foreground)',
                boxShadow:
                  interval === 'monthly' ? 'var(--shadow-sm)' : 'none',
                transition: 'all var(--duration-fast) var(--ease-default)',
              }}
            >
              Monthly
            </button>
            <button
              onClick={() => setInterval('annual')}
              style={{
                padding: 'var(--spacing-2) var(--spacing-5)',
                borderRadius: 'var(--radius-full)',
                border: 'none',
                fontFamily: 'var(--font-body)',
                fontSize: 'var(--text-sm)',
                fontWeight: 600,
                cursor: 'pointer',
                background:
                  interval === 'annual' ? 'var(--color-card)' : 'transparent',
                color:
                  interval === 'annual'
                    ? 'var(--color-foreground)'
                    : 'var(--color-muted-foreground)',
                boxShadow:
                  interval === 'annual' ? 'var(--shadow-sm)' : 'none',
                transition: 'all var(--duration-fast) var(--ease-default)',
              }}
            >
              Annual
              <span
                style={{
                  marginLeft: 'var(--spacing-2)',
                  padding: 'var(--spacing-0_5) var(--spacing-2)',
                  fontSize: 'var(--text-xs)',
                  fontWeight: 700,
                  borderRadius: 'var(--radius-full)',
                  background: 'var(--color-primary)',
                  color: 'var(--color-primary-foreground)',
                }}
              >
                Save 17%
              </span>
            </button>
          </div>
        </div>

        {/* Tier cards */}
        <div
          style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fit, minmax(260px, 1fr))',
            gap: 'var(--spacing-6)',
            maxWidth: 1100,
            margin: '0 auto',
          }}
        >
          {tiers.map((tier) => {
            const isCurrent = subscription?.tier === tier.id
            const isEnterprise = tier.monthlyPrice === null

            return (
              <div
                key={tier.id}
                style={{
                  position: 'relative',
                  display: 'flex',
                  flexDirection: 'column',
                  padding: 'var(--spacing-8)',
                  background: 'var(--color-card)',
                  border: tier.popular
                    ? '2px solid var(--color-primary)'
                    : 'var(--border-width-thin) solid var(--color-border)',
                  borderRadius: 'var(--radius-xl)',
                  boxShadow: tier.popular ? 'var(--shadow-lg)' : 'var(--shadow-sm)',
                }}
              >
                {tier.popular && (
                  <div
                    style={{
                      position: 'absolute',
                      top: -12,
                      left: '50%',
                      transform: 'translateX(-50%)',
                      padding: 'var(--spacing-1) var(--spacing-4)',
                      fontSize: 'var(--text-xs)',
                      fontWeight: 700,
                      fontFamily: 'var(--font-heading)',
                      textTransform: 'uppercase',
                      letterSpacing: '0.05em',
                      borderRadius: 'var(--radius-full)',
                      background: 'var(--color-primary)',
                      color: 'var(--color-primary-foreground)',
                      whiteSpace: 'nowrap',
                    }}
                  >
                    Most popular
                  </div>
                )}

                <h2
                  style={{
                    fontFamily: 'var(--font-heading)',
                    fontSize: 'var(--text-xl)',
                    fontWeight: 700,
                    color: 'var(--color-foreground)',
                    marginBottom: 'var(--spacing-1)',
                  }}
                >
                  {tier.name}
                </h2>

                <p
                  style={{
                    fontSize: 'var(--text-sm)',
                    color: 'var(--color-muted-foreground)',
                    marginBottom: 'var(--spacing-6)',
                  }}
                >
                  {tier.description}
                </p>

                <div
                  style={{
                    marginBottom: 'var(--spacing-6)',
                  }}
                >
                  {isEnterprise ? (
                    <span
                      style={{
                        fontFamily: 'var(--font-heading)',
                        fontSize: 'var(--text-3xl)',
                        fontWeight: 700,
                        color: 'var(--color-foreground)',
                      }}
                    >
                      Custom
                    </span>
                  ) : (
                    <>
                      <span
                        style={{
                          fontFamily: 'var(--font-heading)',
                          fontSize: 'var(--text-3xl)',
                          fontWeight: 700,
                          color: 'var(--color-foreground)',
                        }}
                      >
                        {formatPrice(tier.monthlyPrice!, interval)}
                      </span>
                      {tier.monthlyPrice! > 0 && (
                        <span
                          style={{
                            fontSize: 'var(--text-sm)',
                            color: 'var(--color-muted-foreground)',
                            marginLeft: 'var(--spacing-1)',
                          }}
                        >
                          /mo{tier.id === 'team' ? '/user' : ''}
                        </span>
                      )}
                      {tier.monthlyPrice! > 0 && interval === 'annual' && (
                        <div
                          style={{
                            fontSize: 'var(--text-xs)',
                            color: 'var(--color-muted-foreground)',
                            marginTop: 'var(--spacing-1)',
                          }}
                        >
                          Billed annually (${(tier.monthlyPrice! * 10).toFixed(2)}/year)
                        </div>
                      )}
                    </>
                  )}
                </div>

                {/* CTA */}
                {isCurrent ? (
                  <div
                    style={{
                      padding: 'var(--spacing-3)',
                      borderRadius: 'var(--radius-md)',
                      border: '2px solid var(--color-primary)',
                      textAlign: 'center',
                      fontFamily: 'var(--font-body)',
                      fontSize: 'var(--text-sm)',
                      fontWeight: 600,
                      color: 'var(--color-primary)',
                      marginBottom: 'var(--spacing-6)',
                    }}
                  >
                    Current plan
                  </div>
                ) : isEnterprise ? (
                  <a
                    href="mailto:contact@noorinalabs.com?subject=Enterprise%20inquiry"
                    style={{
                      display: 'block',
                      padding: 'var(--spacing-3)',
                      borderRadius: 'var(--radius-md)',
                      background: 'var(--color-accent)',
                      textAlign: 'center',
                      fontFamily: 'var(--font-body)',
                      fontSize: 'var(--text-sm)',
                      fontWeight: 600,
                      color: 'var(--color-foreground)',
                      textDecoration: 'none',
                      marginBottom: 'var(--spacing-6)',
                      transition: 'opacity var(--duration-fast) var(--ease-default)',
                    }}
                  >
                    {tier.cta}
                  </a>
                ) : (
                  <Link
                    to="/billing/checkout"
                    state={{ tier: tier.id, interval }}
                    style={{
                      display: 'block',
                      padding: 'var(--spacing-3)',
                      borderRadius: 'var(--radius-md)',
                      background: tier.popular
                        ? 'var(--color-primary)'
                        : 'var(--color-accent)',
                      textAlign: 'center',
                      fontFamily: 'var(--font-body)',
                      fontSize: 'var(--text-sm)',
                      fontWeight: 600,
                      color: tier.popular
                        ? 'var(--color-primary-foreground)'
                        : 'var(--color-foreground)',
                      textDecoration: 'none',
                      marginBottom: 'var(--spacing-6)',
                      transition: 'opacity var(--duration-fast) var(--ease-default)',
                    }}
                  >
                    {tier.cta}
                  </Link>
                )}

                {/* Features */}
                <ul
                  style={{
                    listStyle: 'none',
                    padding: 0,
                    margin: 0,
                    flex: 1,
                    display: 'flex',
                    flexDirection: 'column',
                    gap: 'var(--spacing-3)',
                  }}
                >
                  {tier.features.map((feature) => (
                    <li
                      key={feature}
                      style={{
                        display: 'flex',
                        alignItems: 'flex-start',
                        gap: 'var(--spacing-2)',
                        fontSize: 'var(--text-sm)',
                        color: 'var(--color-foreground)',
                      }}
                    >
                      <CheckIcon />
                      {feature}
                    </li>
                  ))}
                </ul>
              </div>
            )
          })}
        </div>
      </div>
    </div>
  )
}
