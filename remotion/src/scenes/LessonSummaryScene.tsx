import React from 'react'
import { AbsoluteFill, Audio, spring, useCurrentFrame, useVideoConfig } from 'remotion'
import { LESSON_PALETTE as L } from '../brand'
import { LessonWatermark, TopNavyBar, BottomGoldBar, BrandHandle } from '../components/LessonBrand'
import { Scene, BrandConfig } from '../types'

interface Props { scene: Scene; brand: BrandConfig }

export const LessonSummaryScene: React.FC<Props> = ({ scene, brand }) => {
  const frame = useCurrentFrame()
  const { fps } = useVideoConfig()
  const bullets = scene.bullet_points ?? []

  const spr = (delay: number) =>
    spring({ frame: frame - delay, fps, config: { damping: 16, stiffness: 130, mass: 1 } })

  return (
    <AbsoluteFill style={{ background: L.BG_ALT, fontFamily: 'Lato' }}>
      {/* Üst panel — lacivert şerit */}
      <div style={{
        position: 'absolute', top: 0, left: 0, right: 0, height: 220,
        background: L.NAVY, zIndex: 0,
      }} />
      <LessonWatermark opacity={0.03} />
      <TopNavyBar />
      <BottomGoldBar />
      <BrandHandle handle={brand.handle} />

      {/* Üst başlık alanı */}
      <div style={{
        position: 'absolute', top: 0, left: 0, right: 0, height: 220,
        display: 'flex', flexDirection: 'column',
        alignItems: 'center', justifyContent: 'center',
        zIndex: 5,
      }}>
        <div style={{
          opacity: spr(0),
          display: 'flex', alignItems: 'center', gap: 12, marginBottom: 10,
        }}>
          <span style={{ fontSize: 32 }}>📋</span>
          <span style={{
            fontSize: 13, fontWeight: 800, color: L.GOLD,
            letterSpacing: 2, textTransform: 'uppercase',
          }}>
            ÖZET
          </span>
        </div>
        <h2 style={{
          opacity: spr(4), transform: `translateY(${(1 - spr(4)) * 12}px)`,
          fontSize: 42, fontWeight: 900, color: '#FFFFFF',
          fontFamily: brand.font_heading ?? 'Playfair Display',
          margin: 0, textAlign: 'center',
        }}>
          {scene.title ?? 'Bu Bölümde Öğrendiklerimiz'}
        </h2>
      </div>

      {/* Kart alanı */}
      <AbsoluteFill style={{
        display: 'flex', flexDirection: 'column',
        padding: '240px 100px 70px',
        gap: 16, zIndex: 5,
      }}>
        {bullets.map((b, i) => {
          const bIn = spr(8 + i * 6)
          return (
            <div key={i} style={{
              display: 'flex', alignItems: 'center', gap: 20,
              background: '#FFFFFF', border: `1.5px solid ${L.BORDER}`,
              borderRadius: 14, padding: '18px 28px',
              opacity: bIn, transform: `translateX(${(1 - bIn) * 30}px)`,
              boxShadow: '0 2px 12px rgba(11,42,74,0.06)',
            }}>
              {/* Numara rozeti */}
              <div style={{
                width: 36, height: 36, borderRadius: 18,
                background: L.GOLD_DIM, border: `2px solid ${L.GOLD}`,
                display: 'flex', alignItems: 'center', justifyContent: 'center',
                flexShrink: 0,
              }}>
                <span style={{ fontSize: 14, fontWeight: 900, color: L.NAVY }}>
                  {i + 1}
                </span>
              </div>
              <p style={{
                fontSize: 20, color: L.DARK, margin: 0,
                lineHeight: 1.5, fontWeight: 500, flex: 1,
              }}>
                {b}
              </p>
            </div>
          )
        })}

        {/* Key point */}
        {scene.key_point && (
          <div style={{
            opacity: spr(8 + bullets.length * 6 + 4),
            transform: `translateY(${(1 - spr(8 + bullets.length * 6 + 4)) * 12}px)`,
            marginTop: 8,
            background: L.GOLD_DIM, border: `2px solid ${L.GOLD}`,
            borderRadius: 14, padding: '16px 28px',
            display: 'flex', alignItems: 'center', gap: 12,
          }}>
            <span style={{ fontSize: 22 }}>⭐</span>
            <p style={{ fontSize: 19, color: L.NAVY, margin: 0, fontWeight: 700 }}>
              {scene.key_point}
            </p>
          </div>
        )}
      </AbsoluteFill>

      {scene.tts_url && <Audio src={scene.tts_url} />}
    </AbsoluteFill>
  )
}
