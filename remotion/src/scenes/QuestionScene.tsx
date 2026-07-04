import { interpolate, useCurrentFrame, useVideoConfig, Audio } from 'remotion'
import { BrandConfig, Scene } from '../types'

const ACCENT = '#2B7FE0'
const BG = '#08121E'

interface Props { scene: Scene; brand: BrandConfig }

export function QuestionScene({ scene, brand }: Props) {
  const frame = useCurrentFrame()
  const { width, height } = useVideoConfig()
  const isVertical = height > width
  const options = scene.options ?? []

  const headerOpacity = interpolate(frame, [0, 18], [0, 1], { extrapolateRight: 'clamp' })
  const cardOpacity = interpolate(frame, [12, 30], [0, 1], { extrapolateRight: 'clamp' })
  const cardY = interpolate(frame, [12, 30], [28, 0], { extrapolateRight: 'clamp' })

  const padH = isVertical ? 56 : 80
  const padV = isVertical ? 72 : 56

  return (
    <div style={{
      width: '100%', height: '100%',
      background: `linear-gradient(160deg, ${BG} 0%, #0D1E38 100%)`,
      display: 'flex', flexDirection: 'column',
      padding: `${padV}px ${padH}px`,
      fontFamily: brand.font_body,
      position: 'relative', overflow: 'hidden',
    }}>
      {/* Subtle ambient glow */}
      <div style={{
        position: 'absolute', top: -60, right: -80,
        width: 360, height: 360, borderRadius: '50%',
        background: `radial-gradient(circle, ${ACCENT}10 0%, transparent 65%)`,
        pointerEvents: 'none',
      }} />

      {/* Header */}
      <div style={{
        display: 'flex', justifyContent: 'space-between', alignItems: 'center',
        marginBottom: isVertical ? 36 : 30, opacity: headerOpacity, flexShrink: 0,
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 14 }}>
          <div style={{ width: 5, height: 30, borderRadius: 3, background: ACCENT }} />
          <span style={{ fontSize: 20, fontWeight: 600, color: 'rgba(255,255,255,0.7)' }}>
            {scene.title ?? 'Muhasebe'}
          </span>
        </div>
        <div style={{
          background: ACCENT, color: '#08121E',
          borderRadius: 30, padding: '7px 22px',
          fontSize: 17, fontWeight: 800, letterSpacing: 0.5,
        }}>
          {scene.question_number ?? 1}&nbsp;/&nbsp;{scene.total_questions ?? 5}
        </div>
      </div>

      {/* Question card */}
      <div style={{
        background: 'rgba(255,255,255,0.07)',
        border: '1px solid rgba(255,255,255,0.14)',
        borderRadius: 18, padding: isVertical ? '28px 32px' : '24px 36px',
        marginBottom: isVertical ? 28 : 22,
        opacity: cardOpacity, transform: `translateY(${cardY}px)`,
        flexShrink: 0,
      }}>
        <p style={{
          fontSize: isVertical ? 26 : 28,
          fontFamily: brand.font_heading, fontWeight: 600,
          color: '#FFFFFF', lineHeight: 1.65, margin: 0,
        }}>
          {scene.question_text}
        </p>
      </div>

      {/* Options */}
      <div style={{ display: 'flex', flexDirection: 'column', gap: isVertical ? 14 : 12, flex: 1 }}>
        {options.map((opt, i) => {
          const f0 = 32 + i * 9
          const optOpacity = interpolate(frame, [f0, f0 + 14], [0, 1], { extrapolateRight: 'clamp' })
          const optX = interpolate(frame, [f0, f0 + 14], [-44, 0], { extrapolateRight: 'clamp' })
          return (
            <div key={opt.label} style={{
              display: 'flex', alignItems: 'center', gap: 18,
              background: 'rgba(255,255,255,0.05)',
              border: '1px solid rgba(255,255,255,0.10)',
              borderRadius: 13, padding: isVertical ? '16px 22px' : '14px 22px',
              opacity: optOpacity, transform: `translateX(${optX}px)`,
            }}>
              <div style={{
                width: 40, height: 40, borderRadius: '50%', flexShrink: 0,
                background: ACCENT, color: '#08121E',
                fontWeight: 800, fontSize: 17,
                display: 'flex', alignItems: 'center', justifyContent: 'center',
              }}>
                {opt.label}
              </div>
              <span style={{ fontSize: 22, color: 'rgba(255,255,255,0.88)', lineHeight: 1.55 }}>
                {opt.text}
              </span>
            </div>
          )
        })}
      </div>

      {scene.tts_url && <Audio src={scene.tts_url} />}
    </div>
  )
}
