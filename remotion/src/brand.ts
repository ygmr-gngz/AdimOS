import { BrandConfig } from './types'

export const DEFAULT_BRAND: BrandConfig = {
  primary_color: '#0B2A4A',
  secondary_color: '#C9A96E',
  background_color: '#FAF7F0',
  font_heading: 'Playfair Display',
  font_body: 'Lato',
}

export const FPS = 30

export const DIMENSIONS = {
  '16:9': { width: 1920, height: 1080 },
  '9:16': { width: 1080, height: 1920 },
}

export const TEXT = {
  heading: (brand: BrandConfig) => ({
    fontFamily: brand.font_heading,
    color: brand.primary_color,
    fontWeight: 700,
  }),
  body: (brand: BrandConfig) => ({
    fontFamily: brand.font_body,
    color: brand.primary_color,
  }),
  gold: (brand: BrandConfig) => ({
    fontFamily: brand.font_body,
    color: brand.secondary_color,
    fontWeight: 700,
  }),
}
