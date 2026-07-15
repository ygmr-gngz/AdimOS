/**
 * LessonBrand — Konu anlatımı sahneleri için paylaşılan görsel öğeler.
 * Tüm lesson sahneleri bu bileşenlerden türetir.
 */
import { LESSON_PALETTE as L } from '../brand'

/** Büyük filigran logo — ekranı kapsayan, %4 opaklık */
export function LessonWatermark({ opacity = 0.04 }: { opacity?: number }) {
  return (
    <div style={{
      position: 'absolute', inset: 0,
      display: 'flex', alignItems: 'center', justifyContent: 'center',
      pointerEvents: 'none', overflow: 'hidden', zIndex: 0,
    }}>
      <span style={{
        fontSize: 180, fontWeight: 900, letterSpacing: '0.10em',
        textTransform: 'uppercase' as const, color: L.NAVY,
        opacity, transform: 'rotate(-12deg)', whiteSpace: 'nowrap' as const,
        userSelect: 'none' as const, fontFamily: 'Lato',
      }}>
        ADIM MÜŞAVİRLİK
      </span>
    </div>
  )
}

/** Üst kenar — lacivert 6px şerit */
export function TopNavyBar() {
  return (
    <div style={{
      position: 'absolute', top: 0, left: 0, right: 0, height: 6,
      background: L.NAVY, zIndex: 10,
    }} />
  )
}

/** Alt kenar — altın gradient 4px şerit */
export function BottomGoldBar() {
  return (
    <div style={{
      position: 'absolute', bottom: 0, left: 0, right: 0, height: 4,
      background: `linear-gradient(90deg, transparent 0%, ${L.GOLD} 25%, ${L.GOLD} 75%, transparent 100%)`,
      opacity: 0.75, zIndex: 10,
    }} />
  )
}

/** Marka imzası — sağ alt köşe */
export function BrandHandle({ handle, opacity = 0.55 }: { handle?: string; opacity?: number }) {
  return (
    <div style={{
      position: 'absolute', bottom: 14, right: 32,
      opacity, zIndex: 10,
    }}>
      <span style={{
        fontSize: 13, fontWeight: 700, color: L.NAVY,
        fontFamily: 'Lato', letterSpacing: '0.05em',
      }}>
        {handle ?? '@adimmusavir'}
      </span>
    </div>
  )
}

/** Köşe logosu — logo_url varsa gerçek görsel, yoksa metin imzası */
export function BrandCornerLogo({
  logoUrl,
  handle = '@adimmusavir',
  corner = 'top-right',
}: {
  logoUrl?: string | null
  handle?: string
  corner?: 'top-right' | 'top-left' | 'bottom-right' | 'bottom-left'
}) {
  const isTop    = corner.startsWith('top')
  const isRight  = corner.endsWith('right')
  return (
    <div style={{
      position: 'absolute',
      top:    isTop    ? 18 : undefined,
      bottom: !isTop   ? 18 : undefined,
      right:  isRight  ? 28 : undefined,
      left:   !isRight ? 28 : undefined,
      zIndex: 20,
      display: 'flex', alignItems: 'center', gap: 8,
    }}>
      {logoUrl ? (
        <img
          src={logoUrl}
          alt="logo"
          style={{
            height: 36, width: 'auto',
            objectFit: 'contain', borderRadius: 4,
            filter: 'drop-shadow(0 1px 3px rgba(0,0,0,0.18))',
          }}
        />
      ) : (
        <div style={{
          background: L.NAVY, borderRadius: 8,
          padding: '5px 14px',
        }}>
          <span style={{
            fontSize: 13, fontWeight: 800, color: L.GOLD,
            fontFamily: 'Lato', letterSpacing: '0.06em',
            whiteSpace: 'nowrap' as const,
          }}>
            {handle}
          </span>
        </div>
      )}
    </div>
  )
}

/** Kategori kategorisi için renk → badge config */
export function categoryBadgeStyle(category?: string, customColor?: string) {
  const cat = (category ?? '').toUpperCase()
  const colorMap: Record<string, { bg: string; text: string; border: string }> = {
    'AKTİF':     { bg: 'rgba(34,197,94,0.12)',   text: '#15803D', border: 'rgba(34,197,94,0.35)'   },
    'PASİF':     { bg: 'rgba(239,68,68,0.10)',   text: '#B91C1C', border: 'rgba(239,68,68,0.30)'   },
    'GELİR':     { bg: 'rgba(13,148,136,0.10)',  text: '#0F766E', border: 'rgba(13,148,136,0.30)'  },
    'GİDER':     { bg: 'rgba(245,158,11,0.12)',  text: '#92400E', border: 'rgba(245,158,11,0.35)'  },
    'ÖZKAYNAK':  { bg: 'rgba(124,58,237,0.10)',  text: '#6D28D9', border: 'rgba(124,58,237,0.30)'  },
    'BORSA':     { bg: 'rgba(43,127,224,0.10)',  text: '#1D4ED8', border: 'rgba(43,127,224,0.30)'  },
  }
  const cfg = colorMap[cat] ?? (customColor
    ? { bg: customColor + '20', text: customColor, border: customColor + '50' }
    : { bg: 'rgba(201,169,110,0.12)', text: '#92400E', border: 'rgba(201,169,110,0.35)' }
  )
  return {
    background: cfg.bg, color: cfg.text,
    border: `1px solid ${cfg.border}`,
    borderRadius: 20, padding: '4px 14px',
    fontSize: 12, fontWeight: 800, fontFamily: 'Lato',
    letterSpacing: 1.5, textTransform: 'uppercase' as const,
    display: 'inline-block',
  }
}
