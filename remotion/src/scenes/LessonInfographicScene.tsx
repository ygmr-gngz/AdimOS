import React from 'react'
import { AbsoluteFill, Audio, interpolate, useCurrentFrame } from 'remotion'
import { LESSON_PALETTE as L } from '../brand'
import { BrandConfig, Scene } from '../types'

interface Props { scene: Scene; brand: BrandConfig }

const COLORS = ['#D97706', '#2563A7', '#7C3A8C', '#0F766E']

function ConceptIcon({ index, color }: { index: number; color: string }) {
  if (index === 0) return <svg width="86" height="86" viewBox="0 0 86 86" fill="none"><circle cx="43" cy="24" r="13" stroke={color} strokeWidth="5"/><path d="M20 70c3-19 13-29 23-29s20 10 23 29" stroke={color} strokeWidth="5" strokeLinecap="round"/><path d="M8 73h70" stroke={color} strokeWidth="5" strokeLinecap="round"/></svg>
  if (index === 1) return <svg width="92" height="86" viewBox="0 0 92 86" fill="none"><rect x="20" y="8" width="52" height="68" rx="7" stroke={color} strokeWidth="5"/><path d="M30 25h32M30 39h32M30 53h20" stroke={color} strokeWidth="5" strokeLinecap="round"/><path d="M10 51l14 12M82 51L68 63" stroke={color} strokeWidth="5" strokeLinecap="round"/></svg>
  if (index === 2) return <svg width="100" height="86" viewBox="0 0 100 86" fill="none"><circle cx="33" cy="43" r="24" stroke={color} strokeWidth="7"/><circle cx="67" cy="43" r="24" stroke={color} strokeWidth="7"/><path d="M43 43h14" stroke={color} strokeWidth="7" strokeLinecap="round"/></svg>
  return <svg width="100" height="86" viewBox="0 0 100 86" fill="none"><path d="M11 73h78M18 73V37h18v36M41 73V22h18v51M64 73V10h18v63" stroke={color} strokeWidth="5" strokeLinejoin="round"/><path d="M14 31l23-13 18 7L82 4" stroke={color} strokeWidth="5" strokeLinecap="round" strokeLinejoin="round"/></svg>
}

export const LessonInfographicScene: React.FC<Props> = ({ scene, brand }) => {
  const frame = useCurrentFrame()
  const cards = (scene.cards ?? []).slice(0, 4)
  return (
    <AbsoluteFill style={{ background: '#F7F8FA', fontFamily: brand.font_body, padding: '54px 64px 46px' }}>
      <div style={{ opacity: interpolate(frame, [0, 18], [0, 1], { extrapolateRight: 'clamp' }) }}>
        <h1 style={{ margin: 0, color: '#111827', fontSize: 54, lineHeight: 1.1, fontWeight: 900 }}>
          {scene.infographic_title ?? scene.title}
        </h1>
        {(scene.infographic_subtitle ?? scene.definition) && (
          <p style={{ margin: '14px 0 34px', color: '#334155', fontSize: 24, lineHeight: 1.45, maxWidth: 1540 }}>
            {scene.infographic_subtitle ?? scene.definition}
          </p>
        )}
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: `repeat(${Math.max(cards.length, 1)}, 1fr)`, gap: 22, flex: 1 }}>
        {cards.map((card, index) => {
          const color = COLORS[index % COLORS.length]
          const reveal = interpolate(frame, [14 + index * 8, 32 + index * 8], [0, 1], { extrapolateRight: 'clamp' })
          return (
            <div key={`${card.title}-${index}`} style={{
              opacity: reveal, transform: `translateY(${(1 - reveal) * 20}px)`,
              background: '#FFFFFF', border: `2px solid ${color}55`, borderTop: `6px solid ${color}`,
              borderRadius: 26, padding: '32px 28px', boxShadow: '0 12px 34px rgba(15,23,42,0.08)',
              display: 'flex', flexDirection: 'column', minHeight: 560,
            }}>
              <div style={{ height: 110, border: `4px solid ${color}44`, borderRadius: '60px 60px 16px 16px', marginBottom: 28, display: 'flex', alignItems: 'center', justifyContent: 'center', background: `${color}0A` }}>
                <ConceptIcon index={index} color={color} />
              </div>
              <h2 style={{ margin: 0, color, fontSize: 31, lineHeight: 1.2, fontWeight: 900 }}>{card.title}</h2>
              {card.category && <strong style={{ marginTop: 8, color: '#111827', fontSize: 21 }}>{card.category}</strong>}
              <p style={{ color: '#334155', fontSize: 21, lineHeight: 1.5, margin: '22px 0 0' }}>{card.content}</p>
              {card.rule && <p style={{ color: '#0F172A', fontWeight: 800, fontSize: 20, lineHeight: 1.45, marginTop: 'auto' }}>{card.rule}</p>}
            </div>
          )
        })}
      </div>

      {scene.key_point && (
        <div style={{ marginTop: 24, background: '#FFFFFF', border: `2px solid ${L.RED}`, borderRadius: 18, padding: '18px 26px', color: '#111827', fontSize: 24, fontWeight: 800 }}>
          {scene.key_point}
        </div>
      )}
      {scene.tts_url && <Audio src={scene.tts_url} />}
    </AbsoluteFill>
  )
}
