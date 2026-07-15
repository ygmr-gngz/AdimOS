import { BrandConfig } from './types'

export const DEFAULT_BRAND: BrandConfig = {
  primary_color:    '#0D1B3E',   // koyu lacivert zemin
  secondary_color:  '#2B7FE0',   // canlı mavi vurgu (eski: altın #C9A96E)
  background_color: '#08121E',   // neredeyse siyah lacivert (eski: krem #FAF7F0)
  font_heading: 'Playfair Display',
  font_body:    'Lato',
  handle:       '@adimmusavir',
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

// Konu anlatımı beyaz tema paleti — tüm lesson sahneleri buradan türetir
export const LESSON_PALETTE = {
  BG:       '#FFFFFF',
  BG_ALT:   '#F8FAFC',
  BG_CARD:  '#F1F5F9',
  NAVY:     '#0B2A4A',
  NAVY_DIM: 'rgba(11,42,74,0.08)',
  GOLD:     '#C9A96E',
  GOLD_DIM: 'rgba(201,169,110,0.12)',
  BLUE:     '#2B7FE0',
  DARK:     '#0B1E3C',
  MID:      '#475569',
  DIM:      '#94A3B8',
  BORDER:   '#E2E8F0',
  GREEN:    '#22C55E',
  GREEN_BG: 'rgba(34,197,94,0.10)',
  RED:      '#EF4444',
  RED_BG:   'rgba(239,68,68,0.10)',
  TEAL:     '#0D9488',
  TEAL_BG:  'rgba(13,148,136,0.10)',
  AMBER:    '#F59E0B',
  AMBER_BG: 'rgba(245,158,11,0.10)',
  PURPLE:   '#7C3AED',
} as const

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
