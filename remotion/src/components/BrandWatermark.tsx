/**
 * BrandWatermark — Tüm composition'larda kullanılan marka filigranı.
 * Kaynak önceliği: staticFile > logoUrl (Supabase) > metin filigranı
 * position:absolute, inset:0, pointerEvents:none — içerikle çakışmaz.
 */
import { Img, staticFile } from 'remotion'
import { LESSON_PALETTE } from '../brand'

const STATIC_LOGO = staticFile('brand/adim-musavir-logo.png')

interface BrandWatermarkProps {
  theme?:    'light' | 'dark'
  opacity?:  number
  rotate?:   number
  fontSize?: number
  logoUrl?:  string  // Supabase URL (öncelikli), yoksa staticFile
}

export function BrandWatermark({
  theme      = 'light',
  opacity,
  rotate     = -12,
  fontSize   = 220,
  logoUrl,
}: BrandWatermarkProps) {
  const defaultOpacity = theme === 'light' ? 0.07 : 0.09
  const color          = theme === 'light' ? LESSON_PALETTE.NAVY : '#FFFFFF'
  const eff            = opacity ?? defaultOpacity

  // Önce Supabase URL, yoksa staticFile (bundle'da varsa)
  const imgSrc = logoUrl ?? STATIC_LOGO

  const imgStyle = {
    height: '50%',
    maxWidth: '60%',
    objectFit: 'contain' as const,
    opacity: eff,
    transform: `rotate(${rotate}deg)`,
    userSelect: 'none' as const,
    // Şeffaf PNG artık gerçek alfa kanalına sahip (RGBA, doğrulandı) ama koyu
    // zeminde düz opaklık "üste yapıştırılmış" görünüyordu — karışım modu
    // filigranı zemine gömüyor.
    mixBlendMode: 'soft-light' as const,
    filter: 'grayscale(1)',
  }

  return (
    <div style={{
      position: 'absolute', inset: 0,
      display: 'flex', alignItems: 'center', justifyContent: 'center',
      pointerEvents: 'none', overflow: 'hidden', zIndex: 0,
    }}>
      {imgSrc ? (
        <Img src={imgSrc} style={imgStyle} />
      ) : (
        /* Metin filigranı — hiç logo yok iken */
        <div style={{
          display: 'flex', flexDirection: 'column', alignItems: 'center',
          transform: `rotate(${rotate}deg)`,
          userSelect: 'none',
          gap: 0,
        }}>
          <span style={{
            fontSize, fontWeight: 900, letterSpacing: '0.12em',
            textTransform: 'uppercase' as const, color, opacity: eff,
            whiteSpace: 'nowrap' as const, fontFamily: 'Lato', lineHeight: 0.88,
          }}>
            ADIM
          </span>
          <span style={{
            fontSize: Math.round(fontSize * 0.28), fontWeight: 700,
            letterSpacing: '0.50em', textTransform: 'uppercase' as const,
            color, opacity: eff * 0.75, whiteSpace: 'nowrap' as const,
            fontFamily: 'Lato', marginTop: 4,
          }}>
            MÜŞAVİRLİK
          </span>
        </div>
      )}
    </div>
  )
}
