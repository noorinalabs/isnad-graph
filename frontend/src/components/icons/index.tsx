/**
 * Qalam-aesthetic icon set for Isnad Graph.
 *
 * All icons:
 *  - 24x24 viewBox, stroke-based with currentColor
 *  - Work in light and dark mode
 *  - Inline-friendly (no external references)
 *  - Include Islamic geometric accents where appropriate
 */
import type { SVGProps } from 'react'

type IconProps = SVGProps<SVGSVGElement> & { size?: number }

function Icon({ size = 16, ...props }: IconProps) {
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="1.5"
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden="true"
      {...props}
    />
  )
}

/** Narrators — scholar/person with turban silhouette accent */
export function NarratorsIcon(props: IconProps) {
  return (
    <Icon {...props}>
      {/* Head */}
      <circle cx="12" cy="7" r="4" />
      {/* Shoulders */}
      <path d="M5 21v-2a7 7 0 0 1 14 0v2" />
      {/* Small diamond accent at collar — Islamic geometric motif */}
      <path d="M12 15l1.2 1.2L12 17.4l-1.2-1.2z" fill="currentColor" stroke="none" />
    </Icon>
  )
}

/** Hadiths — open manuscript/scroll */
export function HadithsIcon(props: IconProps) {
  return (
    <Icon {...props}>
      {/* Open book body */}
      <path d="M2 4s2-1 5-1 5 1 5 1v16s-2-1-5-1-5 1-5 1z" />
      <path d="M12 4s2-1 5-1 5 1 5 1v16s-2-1-5-1-5 1-5 1z" />
      {/* Spine */}
      <path d="M12 4v16" />
      {/* Text lines on left page */}
      <path d="M5 8h3" strokeWidth="1" opacity="0.5" />
      <path d="M5 11h3" strokeWidth="1" opacity="0.5" />
    </Icon>
  )
}

/** Collections — library/bookshelf with geometric shelf brackets */
export function CollectionsIcon(props: IconProps) {
  return (
    <Icon {...props}>
      {/* Shelf */}
      <path d="M3 21h18" />
      <path d="M3 13h18" />
      {/* Books on top shelf */}
      <rect x="5" y="5" width="3" height="8" rx="0.5" />
      <rect x="9" y="3" width="2.5" height="10" rx="0.5" />
      <rect x="12.5" y="6" width="3" height="7" rx="0.5" />
      <rect x="16.5" y="4" width="2.5" height="9" rx="0.5" />
      {/* Books on bottom shelf */}
      <rect x="5" y="14" width="4" height="7" rx="0.5" />
      <rect x="10" y="15" width="3" height="6" rx="0.5" />
      <rect x="14" y="14" width="3" height="7" rx="0.5" />
      {/* Geometric bracket accents */}
      <path d="M3 13l1-1 1 1" strokeWidth="1" opacity="0.5" />
      <path d="M19 13l1-1 1 1" strokeWidth="1" opacity="0.5" />
    </Icon>
  )
}

/** Search — magnifying glass with 4-fold star in lens */
export function SearchIcon(props: IconProps) {
  return (
    <Icon {...props}>
      {/* Lens */}
      <circle cx="11" cy="11" r="7" />
      {/* Handle */}
      <path d="M21 21l-4.35-4.35" />
      {/* 4-pointed star motif inside lens */}
      <path
        d="M11 7l1 2.5L14.5 11l-2.5 1L11 14.5l-1-2.5L7.5 11l2.5-1z"
        fill="currentColor"
        stroke="none"
        opacity="0.35"
      />
    </Icon>
  )
}

/** Timeline — horizontal timeline with crescent markers */
export function TimelineIcon(props: IconProps) {
  return (
    <Icon {...props}>
      {/* Horizontal line */}
      <path d="M3 12h18" />
      {/* Timeline nodes */}
      <circle cx="6" cy="12" r="1.5" fill="currentColor" stroke="none" />
      <circle cx="12" cy="12" r="1.5" fill="currentColor" stroke="none" />
      <circle cx="18" cy="12" r="1.5" fill="currentColor" stroke="none" />
      {/* Crescent accent above center node */}
      <path d="M10.5 7a2.5 2.5 0 0 1 3 0" />
      <path d="M11 7.2a1.8 1.8 0 0 0 2 0" />
      {/* Tick marks */}
      <path d="M6 9v-2" strokeWidth="1" opacity="0.4" />
      <path d="M18 9v-2" strokeWidth="1" opacity="0.4" />
    </Icon>
  )
}

/** Compare — split/diff with geometric separator */
export function CompareIcon(props: IconProps) {
  return (
    <Icon {...props}>
      {/* Left panel */}
      <rect x="2" y="3" width="8" height="18" rx="1" />
      {/* Right panel */}
      <rect x="14" y="3" width="8" height="18" rx="1" />
      {/* Connecting arrows */}
      <path d="M10 8h4" />
      <path d="M14 8l-1.5-1.5M14 8l-1.5 1.5" />
      <path d="M14 16h-4" />
      <path d="M10 16l1.5-1.5M10 16l1.5 1.5" />
      {/* Diamond separator accent */}
      <path d="M12 11l1 1-1 1-1-1z" fill="currentColor" stroke="none" opacity="0.5" />
    </Icon>
  )
}

/** Graph Explorer — network constellation with nodes and edges */
export function GraphExplorerIcon(props: IconProps) {
  return (
    <Icon {...props}>
      {/* Central node */}
      <circle cx="12" cy="12" r="2.5" />
      {/* Outer nodes */}
      <circle cx="5" cy="6" r="1.5" />
      <circle cx="19" cy="6" r="1.5" />
      <circle cx="5" cy="18" r="1.5" />
      <circle cx="19" cy="18" r="1.5" />
      {/* Edges connecting to center */}
      <path d="M6.3 7.2L9.7 10.2" />
      <path d="M17.7 7.2L14.3 10.2" />
      <path d="M6.3 16.8L9.7 13.8" />
      <path d="M17.7 16.8L14.3 13.8" />
      {/* Cross-edges for network feel */}
      <path d="M6.5 6h11" strokeDasharray="2 2" strokeWidth="1" opacity="0.3" />
    </Icon>
  )
}

/** Admin — gear with octagonal geometric accent */
export function AdminIcon(props: IconProps) {
  return (
    <Icon {...props}>
      {/* Gear outer — octagonal shape for Islamic geometric feel */}
      <path d="M12 2l2.2 1.3 2.5-.3 1.3 2.2 2.5.3.3 2.5 2.2 1.3L22 12l1.3 2.2-.3 2.5-2.2 1.3-.3 2.5-2.5.3-1.3 2.2-2.5-.3L12 22l-2.2-1.3-2.5.3-1.3-2.2-2.5-.3-.3-2.5L1 14.7 2 12 .7 9.3l.3-2.5 2.2-1.3.3-2.5 2.5-.3L7.3 2.7l2.5.3z" strokeWidth="1.2" />
      {/* Inner circle */}
      <circle cx="12" cy="12" r="3" />
    </Icon>
  )
}

/** Sign out — door with arrow */
export function SignOutIcon(props: IconProps) {
  return (
    <Icon {...props}>
      <path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4" />
      <polyline points="16 17 21 12 16 7" />
      <line x1="21" y1="12" x2="9" y2="12" />
    </Icon>
  )
}
