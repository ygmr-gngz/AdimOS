import { BrandConfig } from './types'

export const DEFAULT_BRAND: BrandConfig = {
  primary_color:    '#0D1B3E',   // koyu lacivert zemin
  secondary_color:  '#2B7FE0',   // canlı mavi vurgu (eski: altın #C9A96E)
  background_color: '#08121E',   // neredeyse siyah lacivert (eski: krem #FAF7F0)
  font_heading: 'Playfair Display',
  font_body:    'Lato',
}

// Marka paleti — tüm sahneler bu sabitlerden türetir
export const PALETTE = {
  // Zeminler
  BG_DARK:  '#08121E',  // en koyu arka plan
  BG_MID:   '#0D2040',  // orta arka plan
  BG_CARD:  '#112038',  // kart/panel arka planı

  // Vurgular
  ACCENT:   '#2B7FE0',  // ana mavi vurgu
  ACCENT_LT:'#5BA3F5',  // açık mavi (başlıklar, vurgu text)
  ACCENT_DIM:'#1A4A9088', // düşük opaklık mavi glow

  // Metin
  TEXT_BRIGHT: '#FFFFFF',
  TEXT_MID:    'rgba(255,255,255,0.72)',
  TEXT_DIM:    'rgba(255,255,255,0.42)',

  // Anlam renkleri (sahnelerde yanlış/doğru gösterimi)
  CORRECT: '#22C55E',   // yeşil — doğru cevap
  WRONG:   '#EF4444',   // kırmızı — yanlış cevap
  NEUTRAL: '#64748B',   // gri — nötr
}

export const FPS = 30

export const DIMENSIONS = {
  '16:9': { width: 1920, height: 1080 },
  '9:16': { width: 1080, height: 1920 },
}

export const TEXT = {
  heading: (brand: BrandConfig) => ({
    fontFamily: brand.font_heading,
    color: PALETTE.TEXT_BRIGHT,
    fontWeight: 700,
  }),
  body: (brand: BrandConfig) => ({
    fontFamily: brand.font_body,
    color: PALETTE.TEXT_MID,
  }),
  accent: (_brand: BrandConfig) => ({
    fontFamily: 'Lato',
    color: PALETTE.ACCENT,
    fontWeight: 700,
  }),
}
