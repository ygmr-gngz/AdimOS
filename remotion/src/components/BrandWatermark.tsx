/**
 * BrandWatermark — Tüm composition'larda kullanılan marka filigranı.
 * Açık (beyaz) ve koyu (lacivert) arka planlar için iki tema.
 * logoUrl varsa: ekran yüksekliğinin %50'si kadar logo gösterilir (objectFit: contain).
 * logoUrl yoksa: text tabanlı "ADIM / MÜŞAVİRLİK" yazı filigranı.
 * position:absolute, inset:0, pointerEvents:none — içerikle çakışmaz.
 */
import { Img } from 'remotion'
import { LESSON_PALETTE } from '../brand'

interface BrandWatermarkProps {
  theme?:   'light' | 'dark'
  opacity?: number
  rotate?:  number
  fontSize?: number
  logoUrl?: string
}

export function BrandWatermark({
  theme    = 'light',
  opacity,
  rotate   = -12,
  fontSize = 220,
  logoUrl,
}: BrandWatermarkProps) {
  const defaultOpacity = theme === 'light' ? 0.045 : 0.055
  const color          = theme === 'light' ? LESSON_PALETTE.NAVY : '#FFFFFF'
  const eff            = opacity ?? defaultOpacity

  return (
    <div style={{
      position: 'absolute', inset: 0,
      display: 'flex', alignItems: 'center', justifyContent: 'center',
      pointerEvents: 'none', overflow: 'hidden', zIndex: 0,
    }}>
      {logoUrl ? (
        /* Logo filigranı — ekran yüksekliğinin %50'si, objectFit: contain */
        <Img
          src={logoUrl}
          style={{
            height: '50%',
            maxWidth: '60%',
            objectFit: 'contain',
            opacity: eff,
            transform: `rotate(${rotate}deg)`,
            userSelect: 'none',
          }}
        />
      ) : (
        /* Metin filigranı (logo yoksa) */
        <div style={{
          display: 'flex', flexDirection: 'column', alignItems: 'center',
          transform: `rotate(${rotate}deg)`,
          userSelect: 'none',
          gap: 0,
        }}>
          <span style={{
            fontSize,
            fontWeight: 900,
            letterSpacing: '0.12em',
            textTransform: 'uppercase' as const,
            color,
            opacity: eff,
            whiteSpace: 'nowrap' as const,
            fontFamily: 'Lato',
            lineHeight: 0.88,
          }}>
            ADIM
          </span>
          <span style={{
            fontSize: Math.round(fontSize * 0.28),
            fontWeight: 700,
            letterSpacing: '0.50em',
            textTransform: 'uppercase' as const,
            color,
            opacity: eff * 0.75,
            whiteSpace: 'nowrap' as const,
            fontFamily: 'Lato',
            marginTop: 4,
          }}>
            MÜŞAVİRLİK
          </span>
        </div>
      )}
    </div>
  )
}
