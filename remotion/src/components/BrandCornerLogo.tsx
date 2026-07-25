/**
 * BrandCornerLogo — Üst köşede tam renkli marka logosu.
 * staticFile("brand/adim-musavir-logo.png") kullanır.
 * Logo yoksa metin etiketi gösterilir (fallback).
 * position: absolute, zIndex: 100.
 */
import { Img, staticFile } from 'remotion'
import { BrandConfig } from '../types'
import { LESSON_PALETTE as L } from '../brand'

const STATIC_LOGO = staticFile('brand/adim-musavir-logo.png')

interface BrandCornerLogoProps {
  brand?:   BrandConfig
  corner?:  'top-right' | 'top-left'
  size?:    number   // px, varsayılan 140
  padding?: number   // kenar boşluğu, varsayılan 20
  logoUrl?: string   // Supabase URL (override)
}

export function BrandCornerLogo({
  brand,
  corner   = 'top-right',
  size     = 140,
  padding  = 20,
  logoUrl,
}: BrandCornerLogoProps) {
  const pos = corner === 'top-right'
    ? { top: padding, right: padding }
    : { top: padding, left: padding }

  // Önce prop logoUrl, sonra brand.logo_url (Supabase), son çare staticFile
  const src = logoUrl ?? brand?.logo_url ?? STATIC_LOGO

  return (
    <div style={{
      position: 'absolute', ...pos,
      width: size, height: size,
      zIndex: 100,
      display: 'flex', alignItems: 'center', justifyContent: 'center',
    }}>
      <Img
        src={src}
        style={{ width: size, height: size, objectFit: 'contain' }}
      />
    </div>
  )
}
