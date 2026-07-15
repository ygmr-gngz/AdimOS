import React from 'react'
import { AbsoluteFill, Audio, spring, useCurrentFrame, useVideoConfig } from 'remotion'
import { LESSON_PALETTE as L } from '../brand'
import { LessonWatermark, TopNavyBar, BottomGoldBar, BrandHandle, BrandCornerLogo } from '../components/LessonBrand'
import { Scene, BrandConfig } from '../types'

interface Props { scene: Scene; brand: BrandConfig }

export const LessonConceptScene: React.FC<Props> = ({ scene, brand }) => {
  const frame = useCurrentFrame()
  const { fps } = useVideoConfig()
  const bullets = scene.bullet_points ?? []

  const spr = (delay: number, damp = 16, stiff = 140) =>
    spring({ frame: frame - delay, fps, config: { damping: damp, stiffness: stiff, mass: 1 } })

  return (
    <AbsoluteFill style={{ background: L.BG, fontFamily: 'Lato' }}>
      <LessonWatermark />
      <TopNavyBar />
      <BottomGoldBar />
      <BrandHandle handle={brand.handle} />
      <BrandCornerLogo logoUrl={brand.logo_url} handle={brand.handle} corner="top-right" />

      <AbsoluteFill style={{
        display: 'flex', flexDirection: 'column',
        alignItems: 'center', justifyContent: 'center',
        padding: '80px 140px',
      }}>
        {/* İkon + konsept adı — üst */}
        <div style={{
          display: 'flex', flexDirection: 'column', alignItems: 'center',
          marginBottom: 40,
          opacity: spr(0), transform: `translateY(${(1 - spr(0)) * 20}px)`,
        }}>
          {scene.icon && (
            <span style={{ fontSize: 64, marginBottom: 18, lineHeight: 1 }}>
              {scene.icon}
            </span>
          )}
          <h2 style={{
            fontSize: 54, fontWeight: 900, color: L.NAVY,
            fontFamily: brand.font_heading ?? 'Playfair Display',
            margin: 0, textAlign: 'center', lineHeight: 1.15,
          }}>
            {scene.title}
          </h2>
        </div>

        {/* Tanım kutusu */}
        {scene.definition && (
          <div style={{
            opacity: spr(8), transform: `translateY(${(1 - spr(8)) * 16}px)`,
            background: L.NAVY_DIM, border: `2px solid ${L.GOLD}`,
            borderRadius: 16, padding: '22px 40px',
            marginBottom: 36, width: '100%', maxWidth: 900,
          }}>
            <p style={{
              fontSize: 24, color: L.DARK, lineHeight: 1.6,
              margin: 0, textAlign: 'center', fontStyle: 'italic',
            }}>
              {scene.definition}
            </p>
          </div>
        )}

        {/* Madde listesi */}
        {bullets.length > 0 && (
          <div style={{
            display: 'flex', flexDirection: 'column', gap: 14,
            width: '100%', maxWidth: 900,
          }}>
            {bullets.map((b, i) => {
              const bIn = spr(16 + i * 6)
              return (
                <div key={i} style={{
                  display: 'flex', alignItems: 'flex-start', gap: 16,
                  opacity: bIn, transform: `translateX(${(1 - bIn) * 24}px)`,
                }}>
                  <div style={{
                    width: 8, height: 8, borderRadius: 4, background: L.GOLD,
                    flexShrink: 0, marginTop: 10,
                  }} />
                  <p style={{
                    fontSize: 22, color: L.MID, lineHeight: 1.55,
                    margin: 0, fontWeight: 500,
                  }}>
                    {b}
                  </p>
                </div>
              )
            })}
          </div>
        )}
      </AbsoluteFill>

      {scene.tts_url && <Audio src={scene.tts_url} />}
    </AbsoluteFill>
  )
}
