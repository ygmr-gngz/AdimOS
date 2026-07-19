/**
 * SocialFooter — Alt sosyal medya çubuğu.
 * Tüm sahnelerin altına eklenebilir, position: absolute.
 * Instagram + YouTube handle'larını gösterir.
 */
import { BrandConfig } from '../types'
import { LESSON_PALETTE as L } from '../brand'

interface SocialFooterProps {
  brand:   BrandConfig
  theme?:  'light' | 'dark'
  opacity?: number
}

const ICON_INSTAGRAM = (color: string) => (
  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" style={{ flexShrink: 0 }}>
    <rect x="2" y="2" width="20" height="20" rx="5" stroke={color} strokeWidth="2" />
    <circle cx="12" cy="12" r="4" stroke={color} strokeWidth="2" />
    <circle cx="17.5" cy="6.5" r="1" fill={color} />
  </svg>
)

const ICON_YOUTUBE = (color: string) => (
  <svg width="18" height="14" viewBox="0 0 24 18" fill="none" style={{ flexShrink: 0 }}>
    <rect x="1" y="1" width="22" height="16" rx="4" stroke={color} strokeWidth="2" />
    <polygon points="10,6 10,12 16,9" fill={color} />
  </svg>
)

export function SocialFooter({ brand, theme = 'light', opacity = 1 }: SocialFooterProps) {
  const handle    = brand.handle ?? '@adimmusavir'
  const ytHandle  = 'youtube.com/' + handle
  const textColor = theme === 'light' ? L.MID  : 'rgba(255,255,255,0.65)'
  const divider   = theme === 'light' ? L.BORDER : 'rgba(255,255,255,0.15)'
  const bg        = theme === 'light'
    ? 'rgba(248,250,252,0.92)'
    : 'rgba(8,18,30,0.80)'

  return (
    <div style={{
      position: 'absolute', bottom: 0, left: 0, right: 0,
      height: 40,
      background: bg,
      borderTop: `1px solid ${divider}`,
      display: 'flex', alignItems: 'center',
      padding: '0 32px', gap: 28,
      zIndex: 50,
      opacity,
    }}>
      {/* Instagram */}
      <div style={{ display: 'flex', alignItems: 'center', gap: 7 }}>
        {ICON_INSTAGRAM(textColor)}
        <span style={{
          fontSize: 13, fontFamily: 'Lato', fontWeight: 600,
          color: textColor, letterSpacing: '0.02em',
        }}>
          {handle}
        </span>
      </div>

      <div style={{ width: 1, height: 18, background: divider }} />

      {/* YouTube */}
      <div style={{ display: 'flex', alignItems: 'center', gap: 7 }}>
        {ICON_YOUTUBE(textColor)}
        <span style={{
          fontSize: 13, fontFamily: 'Lato', fontWeight: 600,
          color: textColor, letterSpacing: '0.02em',
        }}>
          {ytHandle}
        </span>
      </div>

      {/* Sağ: ders/başlık varsa */}
      <div style={{ marginLeft: 'auto' }}>
        <span style={{
          fontSize: 11, fontFamily: 'Lato', fontWeight: 700,
          color: textColor, opacity: 0.6, letterSpacing: '0.08em',
          textTransform: 'uppercase' as const,
        }}>
          ADIM MÜŞAVİRLİK
        </span>
      </div>
    </div>
  )
}
