/**
 * Kart ailesi paylaşılan ikonları — SVG, 24×24 viewBox, 2px çizgi,
 * currentColor. Emoji yasak (bkz. GÖREV genel kurallar).
 */

export function IconWarning() {
  return (
    <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor"
      strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M12 3l10 17.5H2L12 3z" />
      <path d="M12 9.5v5" />
      <circle cx="12" cy="17.3" r="0.6" fill="currentColor" stroke="none" />
    </svg>
  )
}

export function IconCheck() {
  return (
    <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor"
      strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <circle cx="12" cy="12" r="9" />
      <path d="M8 12.5l2.7 2.7L16 9.5" />
    </svg>
  )
}

export function IconArrowRight() {
  return (
    <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor"
      strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M5 12h14" />
      <path d="M13 6l6 6-6 6" />
    </svg>
  )
}
