import React from 'react'
import { AbsoluteFill, Audio, spring, useCurrentFrame, useVideoConfig } from 'remotion'
import { LESSON_PALETTE as L } from '../brand'
import { LessonWatermark, TopNavyBar, BottomGoldBar, BrandHandle } from '../components/LessonBrand'
import { Scene, BrandConfig } from '../types'

interface Props { scene: Scene; brand: BrandConfig }

export const LessonTitleScene: React.FC<Props> = ({ scene, brand }) => {
  const frame = useCurrentFrame()
  const { fps } = useVideoConfig()

  const spr = (delay: number, damp = 14, stiff = 130) =>
    spring({ frame: frame - delay, fps, config: { damping: damp, stiffness: stiff, mass: 1 } })

  const badgeIn   = spr(0)
  const iconIn    = spr(6)
  const titleIn   = spr(12)
  const dividerIn = spr(22)
  const subtitleIn = spr(28)

  return (
    <AbsoluteFill style={{ background: L.BG, fontFamily: 'Lato' }}>
      <LessonWatermark />
      <TopNavyBar />
      <BottomGoldBar />
      <BrandHandle handle={brand.handle} />

      {/* Ana içerik — dikey orta */}
      <AbsoluteFill style={{
        display: 'flex', flexDirection: 'column',
        alignItems: 'center', justifyContent: 'center',
        padding: '80px 120px',
      }}>
        {/* Kategori badge */}
        <div style={{
          opacity: badgeIn, transform: `translateY(${(1 - badgeIn) * 20}px)`,
          marginBottom: 28,
        }}>
          <div style={{
            background: L.GOLD_DIM, border: `1px solid ${L.GOLD}`,
            borderRadius: 20, padding: '6px 20px',
            fontSize: 14, fontWeight: 800, color: L.NAVY,
            letterSpacing: 2, textTransform: 'uppercase',
          }}>
            {scene.subtitle ?? 'KONU ANLATIMI'}
          </div>
        </div>

        {/* Emoji ikon */}
        {scene.icon && (
          <div style={{
            opacity: iconIn, transform: `scale(${0.6 + 0.4 * iconIn})`,
            fontSize: 72, marginBottom: 24,
            lineHeight: 1,
          }}>
            {scene.icon}
          </div>
        )}

        {/* Ana başlık */}
        <h1 style={{
          opacity: titleIn, transform: `translateY(${(1 - titleIn) * 24}px)`,
          fontSize: 72, fontWeight: 900, color: L.NAVY,
          fontFamily: brand.font_heading ?? 'Playfair Display',
          textAlign: 'center', lineHeight: 1.1, margin: '0 0 28px',
          maxWidth: 900,
        }}>
          {scene.title ?? 'Başlık'}
        </h1>

        {/* Altın ayraç çizgi */}
        <div style={{
          width: `${800 * dividerIn}px`, height: 3,
          background: `linear-gradient(90deg, transparent, ${L.GOLD}, transparent)`,
          marginBottom: 28, transition: 'width 0.3s',
        }} />

        {/* Key point / alt yazı */}
        {scene.key_point && (
          <p style={{
            opacity: subtitleIn, transform: `translateY(${(1 - subtitleIn) * 16}px)`,
            fontSize: 26, color: L.MID, textAlign: 'center',
            lineHeight: 1.5, maxWidth: 760, margin: 0,
          }}>
            {scene.key_point}
          </p>
        )}
      </AbsoluteFill>

      {/* TTS ses */}
      {scene.tts_url && <Audio src={scene.tts_url} />}
    </AbsoluteFill>
  )
}
