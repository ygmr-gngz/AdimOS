import React from 'react'
import { AbsoluteFill, Audio, spring, useCurrentFrame, useVideoConfig } from 'remotion'
import { LESSON_PALETTE as L } from '../brand'
import { LessonWatermark, TopNavyBar, BottomGoldBar, BrandHandle, categoryBadgeStyle } from '../components/LessonBrand'
import { Scene, BrandConfig, InfographicCard } from '../types'

interface Props { scene: Scene; brand: BrandConfig }

/** Tek bir kart */
const Card: React.FC<{ card: InfographicCard; delay: number; isHighlighted: boolean }> = ({ card, delay, isHighlighted }) => {
  const frame = useCurrentFrame()
  const { fps } = useVideoConfig()
  const cardIn = spring({ frame: frame - delay, fps, config: { damping: 16, stiffness: 130, mass: 1 } })

  return (
    <div style={{
      background: isHighlighted ? L.NAVY_DIM : L.BG_CARD,
      border: `2px solid ${isHighlighted ? L.GOLD : L.BORDER}`,
      borderRadius: 16, padding: '24px 28px',
      opacity: cardIn, transform: `translateY(${(1 - cardIn) * 20}px)`,
      flex: 1, minWidth: 0,
      boxShadow: isHighlighted ? `0 4px 24px rgba(201,169,110,0.18)` : 'none',
      transition: 'border-color 0.3s, box-shadow 0.3s',
    }}>
      {/* Üst: İkon + kod + başlık */}
      <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 14 }}>
        {card.icon && (
          <span style={{ fontSize: 30, lineHeight: 1 }}>{card.icon}</span>
        )}
        <div style={{ flex: 1, minWidth: 0 }}>
          {card.code && (
            <span style={{
              fontSize: 12, fontWeight: 800, color: L.GOLD,
              letterSpacing: 1, fontFamily: 'Lato', display: 'block',
            }}>
              {card.code}
            </span>
          )}
          <div style={{
            fontSize: 17, fontWeight: 800, color: L.NAVY,
            fontFamily: 'Lato', lineHeight: 1.2,
          }}>
            {card.title}
          </div>
        </div>
        {card.category && (
          <div style={categoryBadgeStyle(card.category, card.category_color)}>
            {card.category}
          </div>
        )}
      </div>

      {/* İçerik */}
      {card.content && (
        <p style={{
          fontSize: 15, color: L.MID, lineHeight: 1.55,
          margin: '0 0 10px', fontFamily: 'Lato',
        }}>
          {card.content}
        </p>
      )}
      {card.rule && (
        <div style={{
          background: L.GOLD_DIM, border: `1px solid ${L.GOLD}`,
          borderRadius: 8, padding: '8px 12px', marginBottom: 8,
          fontSize: 13, color: L.DARK, fontFamily: 'Lato',
        }}>
          📌 {card.rule}
        </div>
      )}
      {card.example && (
        <div style={{
          background: 'rgba(43,127,224,0.08)', border: '1px solid rgba(43,127,224,0.25)',
          borderRadius: 8, padding: '8px 12px',
          fontSize: 13, color: '#1D4ED8', fontFamily: 'Lato',
        }}>
          💡 {card.example}
        </div>
      )}
    </div>
  )
}

export const LessonCardScene: React.FC<Props> = ({ scene, brand }) => {
  const frame = useCurrentFrame()
  const { fps, durationInFrames } = useVideoConfig()
  const cards = scene.cards ?? []

  // Sahne ilerledikçe kartları sırayla vurgula
  const highlightIndex = cards.length > 1
    ? Math.floor((frame / durationInFrames) * cards.length)
    : 0

  const titleIn = spring({ frame, fps, config: { damping: 16, stiffness: 140, mass: 1 } })

  const rows = Math.ceil(cards.length / 2)
  const perRow = Math.ceil(cards.length / rows)

  return (
    <AbsoluteFill style={{ background: L.BG, fontFamily: 'Lato' }}>
      <LessonWatermark />
      <TopNavyBar />
      <BottomGoldBar />
      <BrandHandle handle={brand.handle} />

      <AbsoluteFill style={{
        display: 'flex', flexDirection: 'column',
        padding: '72px 80px 60px',
      }}>
        {/* Başlık */}
        {scene.infographic_title && (
          <div style={{
            opacity: titleIn, transform: `translateY(${(1 - titleIn) * 16}px)`,
            marginBottom: 32,
          }}>
            <h2 style={{
              fontSize: 36, fontWeight: 900, color: L.NAVY,
              fontFamily: brand.font_heading ?? 'Playfair Display',
              margin: '0 0 6px',
            }}>
              {scene.infographic_title}
            </h2>
            {scene.infographic_subtitle && (
              <p style={{ fontSize: 17, color: L.MID, margin: 0 }}>
                {scene.infographic_subtitle}
              </p>
            )}
          </div>
        )}

        {/* Kart grid */}
        <div style={{ flex: 1, display: 'flex', flexDirection: 'column', gap: 16 }}>
          {Array.from({ length: rows }).map((_, rowIdx) => {
            const rowCards = cards.slice(rowIdx * perRow, (rowIdx + 1) * perRow)
            return (
              <div key={rowIdx} style={{ display: 'flex', gap: 16, flex: 1 }}>
                {rowCards.map((card, i) => {
                  const globalIdx = rowIdx * perRow + i
                  return (
                    <Card
                      key={globalIdx}
                      card={card}
                      delay={8 + globalIdx * 5}
                      isHighlighted={globalIdx === highlightIndex}
                    />
                  )
                })}
              </div>
            )
          })}
        </div>

        {/* Footer notu */}
        {scene.footer_note && (
          <div style={{
            marginTop: 16, paddingTop: 12,
            borderTop: `1px solid ${L.BORDER}`,
            fontSize: 13, color: L.DIM, fontStyle: 'italic',
          }}>
            * {scene.footer_note}
          </div>
        )}
      </AbsoluteFill>

      {scene.tts_url && <Audio src={scene.tts_url} />}
    </AbsoluteFill>
  )
}
