/**
 * Empty state illustrations for Isnad Graph.
 *
 * Larger SVG illustrations (80-120px) for empty/error/no-data states.
 * Use currentColor for automatic theme adaptation.
 */
import type { SVGProps } from 'react'

type IllustrationProps = SVGProps<SVGSVGElement> & { size?: number }

function Illustration({ size = 96, ...props }: IllustrationProps) {
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 96 96"
      fill="none"
      stroke="currentColor"
      strokeWidth="1.2"
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden="true"
      {...props}
    />
  )
}

/** No search results — magnifying glass over empty geometric pattern */
export function NoResultsIllustration(props: IllustrationProps) {
  return (
    <Illustration {...props}>
      {/* Background geometric pattern (faded) */}
      <g opacity="0.15">
        <rect x="16" y="16" width="24" height="24" transform="rotate(45 28 28)" />
        <rect x="48" y="16" width="24" height="24" transform="rotate(45 60 28)" />
        <rect x="16" y="48" width="24" height="24" transform="rotate(45 28 60)" />
        <rect x="48" y="48" width="24" height="24" transform="rotate(45 60 60)" />
      </g>
      {/* Magnifying glass */}
      <circle cx="40" cy="40" r="18" strokeWidth="2" />
      <path d="M53 53l16 16" strokeWidth="3" />
      {/* X inside lens */}
      <path d="M34 34l12 12M46 34l-12 12" strokeWidth="1.5" opacity="0.5" />
    </Illustration>
  )
}

/** Empty graph — disconnected nodes with no edges */
export function EmptyGraphIllustration(props: IllustrationProps) {
  return (
    <Illustration {...props}>
      {/* Scattered nodes */}
      <circle cx="20" cy="24" r="4" opacity="0.3" />
      <circle cx="48" cy="16" r="4" opacity="0.3" />
      <circle cx="76" cy="28" r="4" opacity="0.3" />
      <circle cx="28" cy="56" r="4" opacity="0.3" />
      <circle cx="60" cy="52" r="4" opacity="0.3" />
      <circle cx="44" cy="76" r="4" opacity="0.3" />
      <circle cx="72" cy="68" r="4" opacity="0.3" />
      {/* Dashed lines suggesting missing connections */}
      <path d="M24 26l20-8" strokeDasharray="3 4" opacity="0.15" />
      <path d="M52 18l20 8" strokeDasharray="3 4" opacity="0.15" />
      <path d="M32 56l24-4" strokeDasharray="3 4" opacity="0.15" />
      {/* Central question mark */}
      <text
        x="48"
        y="48"
        textAnchor="middle"
        dominantBaseline="central"
        fill="currentColor"
        stroke="none"
        fontSize="18"
        fontFamily="var(--font-heading)"
        opacity="0.25"
      >
        ?
      </text>
    </Illustration>
  )
}

/** No data — empty scroll/manuscript */
export function NoDataIllustration(props: IllustrationProps) {
  return (
    <Illustration {...props}>
      {/* Scroll body */}
      <rect x="20" y="14" width="56" height="62" rx="3" strokeWidth="1.5" />
      {/* Scroll top roll */}
      <ellipse cx="48" cy="14" rx="28" ry="4" strokeWidth="1.5" />
      {/* Scroll bottom roll */}
      <ellipse cx="48" cy="76" rx="28" ry="4" strokeWidth="1.5" />
      {/* Empty text lines (ghosted) */}
      <path d="M30 30h36" opacity="0.15" />
      <path d="M30 38h28" opacity="0.15" />
      <path d="M30 46h32" opacity="0.15" />
      <path d="M30 54h24" opacity="0.15" />
      <path d="M30 62h30" opacity="0.15" />
      {/* Decorative diamond in center */}
      <path d="M48 42l4 4-4 4-4-4z" fill="currentColor" opacity="0.12" stroke="none" />
    </Illustration>
  )
}

/**
 * Empty state container — wraps an illustration with a message.
 * Pure layout component, no styling opinions beyond centering.
 */
export function EmptyState({
  illustration,
  title,
  description,
}: {
  illustration: React.ReactNode
  title: string
  description?: string
}) {
  return (
    <div
      style={{
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
        gap: 'var(--spacing-4)',
        padding: 'var(--spacing-12) var(--spacing-6)',
        textAlign: 'center',
        color: 'var(--color-muted-foreground)',
      }}
    >
      {illustration}
      <h3
        style={{
          margin: 0,
          fontSize: 'var(--text-lg)',
          fontFamily: 'var(--font-heading)',
          fontWeight: 500,
          color: 'var(--color-foreground)',
        }}
      >
        {title}
      </h3>
      {description && (
        <p
          style={{
            margin: 0,
            fontSize: 'var(--text-sm)',
            maxWidth: 320,
            lineHeight: 'var(--leading-relaxed)',
          }}
        >
          {description}
        </p>
      )}
    </div>
  )
}
