import { interpolate, spring, useCurrentFrame, useVideoConfig, Audio } from 'remotion'
import { BrandConfig, Scene } from '../types'

const GOLD = '#C9A96E'
const BG = '#08121E'
const GREEN = '#22C55E'
const GREEN_DIM = 'rgba(34,197,94,0.13)'
const GREEN_BORDER = 'rgba(34,197,94,0.55)'

interface Props { scene: Scene; brand: BrandConfig }

export function CorrectAnswerScene({ scene, brand }: Props) {
  const frame = useCurrentFrame()
  const { fps, width, height } = useVideoConfig()
  const isVertical = height > width

  const checkScale = spring({ frame, fps, config: { damping: 13, stiffness: 200 }, from: 0, to: 1 })
  const glowOpacity = interpolate(frame, [0, 20], [0, 1], { extrapolateRight: 'clamp' })
  const labelOpacity = interpolate(frame, [18, 34], [0, 1], { extrapolateRight: 'clamp' })
  const cardOpacity = interpolate(frame, [26, 44], [0, 1], { extrapolateRight: 'clamp' })
  const cardY = interpolate(frame, [26, 44], [20, 0], { extrapolateRight: 'clamp' })
  const explOpacity = interpolate(frame, [42, 60], [0, 1], { extrapolateRight: 'clamp' })

  const correctOption = scene.options?.find(o => o.label === scene.correct_label)
  const padH = isVertical ? 56 : 120

  return (
    <div style={{
      width: '100%', height: '100%',
      background: `linear-gradient(145deg, ${BG} 0%, #091828 55%, #0A0F1C 100%)`,
      display: 'flex', flexDirection: 'column',
      alignItems: 'center', justifyContent: 'center',
      padding: `60px ${padH}px`,
      fontFamily: brand.font_body,
      position: 'relative', overflow: 'hidden',
    }}>
      {/* Green ambient glow */}
      <div style={{
        position: 'absolute', inset: 0,
        background: `radial-gradient(ellipse at 50% 30%, ${GREEN}12 0%, transparent 60%)`,
        opacity: glowOpacity, pointerEvents: 'none',
      }} />

      {/* Big checkmark */}
      <div style={{
        width: isVertical ? 108 : 100, height: isVertical ? 108 : 100,
        borderRadius: '50%',
        background: GREEN,
        display: 'flex', alignItems: 'center', justifyContent: 'center',
        transform: `scale(${checkScale})`,
        marginBottom: isVertical ? 36 : 32,
        boxShadow: `0 0 40px ${GREEN}55, 0 8px 32px rgba(0,0,0,0.4)`,
      }}>
        <svg width="52" height="52" viewBox="0 0 52 52" fill="none">
          <path d="M11 26L22 37L41 15" stroke="white" strokeWidth="5.5"
            strokeLinecap="round" strokeLinejoin="round"/>
        </svg>
      </div>

      {/* "Doğru Cevap" label */}
      <div style={{ opacity: labelOpacity, marginBottom: isVertical ? 28 : 24, textAlign: 'center' }}>
        <p style={{
          fontSize: 14, fontWeight: 800, color: GREEN,
          letterSpacing: 4, textTransform: 'uppercase' as const, margin: 0,
        }}>
          Doğru Cevap
        </p>
      </div>

      {/* Correct option card */}
      {correctOption && (
        <div style={{
          display: 'flex', alignItems: 'flex-start', gap: 20,
          background: GREEN_DIM,
          border: `2px solid ${GREEN_BORDER}`,
          borderRadius: 18, padding: isVertical ? '22px 28px' : '22px 32px',
          marginBottom: isVertical ? 24 : 22,
          opacity: cardOpacity, transform: `translateY(${cardY}px)`,
          width: '100%',
        }}>
          <div style={{
            width: 46, height: 46, borderRadius: '50%', flexShrink: 0,
            background: GREEN, color: '#fff', fontWeight: 800, fontSize: 20,
            display: 'flex', alignItems: 'center', justifyContent: 'center',
            boxShadow: `0 0 16px ${GREEN}50`,
          }}>
            {scene.correct_label}
          </div>
          <span style={{
            fontSize: isVertical ? 24 : 26,
            fontFamily: brand.font_heading, fontWeight: 600,
            color: '#FFFFFF', lineHeight: 1.55,
          }}>
            {correctOption.text}
          </span>
        </div>
      )}

      {/* Explanation */}
      {scene.explanation && (
        <div style={{
          background: 'rgba(255,255,255,0.06)',
          border: `1px solid rgba(201,169,110,0.30)`,
          borderLeft: `4px solid ${GOLD}`,
          borderRadius: 14, padding: isVertical ? '20px 26px' : '20px 28px',
          opacity: explOpacity, width: '100%',
        }}>
          <p style={{
            fontSize: 12, fontWeight: 800, color: GOLD,
            letterSpacing: 3, textTransform: 'uppercase' as const, marginBottom: 10,
          }}>
            Çözüm Mantığı
          </p>
          <p style={{
            fontSize: isVertical ? 20 : 21,
            color: 'rgba(255,255,255,0.82)', lineHeight: 1.7, margin: 0,
          }}>
            {scene.explanation}
          </p>
        </div>
      )}

      {scene.tts_url && <Audio src={scene.tts_url} />}
    </div>
  )
}
