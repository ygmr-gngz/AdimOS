/**
 * BrandOverlay — Her composition'ın üzerine eklenen evrensel marka katmanı.
 *
 * İçerir:
 *  - BrandWatermark  : ortada büyük silik logo (opacity 0.07–0.12, z:0)
 *  - BrandCornerLogo : üst köşede tam renkli logo (120–160 px, z:100)
 *  - SocialFooter    : alt çubuk Instagram + YouTube (z:50)
 *
 * Kullanım:
 *   <AbsoluteFill>
 *     {sceneler...}
 *     <BrandOverlay brand={brand} theme="light" />
 *   </AbsoluteFill>
 */
import { BrandConfig } from '../types'
import { BrandWatermark } from './BrandWatermark'
import { BrandCornerLogo } from './BrandCornerLogo'
import { SocialFooter } from './SocialFooter'

interface BrandOverlayProps {
  brand:    BrandConfig
  theme?:   'light' | 'dark'
  /** Köşe logo boyutu (px). Varsayılan 140. */
  logoSize?: number
  /** Filigran opaklığı. Varsayılan tema başına 0.09/0.10. */
  watermarkOpacity?: number
  /** SocialFooter göster. Varsayılan true. */
  showFooter?: boolean
}

export function BrandOverlay({
  brand,
  theme              = 'light',
  logoSize           = 140,
  watermarkOpacity,
  showFooter         = true,
}: BrandOverlayProps) {
  const wOpacity = watermarkOpacity ?? (theme === 'light' ? 0.09 : 0.10)

  return (
    <>
      {/* 1. Filigran — içerik arkasında (z:0) */}
      <BrandWatermark theme={theme} opacity={wOpacity} />

      {/* 2. Köşe logosu — içerik üstünde (z:100) */}
      <BrandCornerLogo brand={brand} corner="top-right" size={logoSize} />

      {/* 3. Sosyal medya çubuğu — en altta (z:50) */}
      {showFooter && <SocialFooter brand={brand} theme={theme} />}
    </>
  )
}
