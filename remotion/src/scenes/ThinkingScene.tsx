import { interpolate, spring, useCurrentFrame, useVideoConfig, Audio } from 'remotion'
import { BrandConfig, Scene } from '../types'

const GOLD = '#C9A96E'
const BG = '#08121E'

interface Props { scene: Scene; brand: BrandConfig }

export function ThinkingScene({ scene, brand }: Props) {
  const frame = useCurrentFrame()
  const { fps } = useVideoConfig()
  const totalFrames = scene.duration_seconds * 30

  const progress = interpolate(frame, [0, totalFrames], [1, 0], { extrapolateRight: 'clamp' })
  const ringScale = spring({ frame, fps, config: { damping: 14 }, from: 0.5, to: 1 })
  const textOpacity = interpolate(frame, [8, 25], [0, 1], { extrapolateRight: 'clamp' })

  // Breathing pulse
  const pulse = Math.sin(frame * 0.07) * 0.035 + 1

  // Orbiting dots
  const dot1 = Math.sin(frame * 0.15) * 0.45 + 0.55
  const dot2 = Math.sin(frame * 0.15 - 1.1) * 0.45 + 0.55
  const dot3 = Math.sin(frame * 0.15 - 2.2) * 0.45 + 0.55

  return (
    <div style={{
      width: '100%', height: '100%',
      background: `linear-gradient(145deg, ${BG} 0%, #0A1A30 60%, ${BG} 100%)`,
      display: 'flex', flexDirection: 'column',
      alignItems: 'center', justifyContent: 'center',
      fontFamily: brand.font_body, overflow: 'hidden', position: 'relative',
    }}>
      {/* Background radial */}
      <div style={{
        position: 'absolute', inset: 0,
        background: `radial-gradient(ellipse at 50% 40%, ${GOLD}0C 0%, transparent 65%)`,
        pointerEvents: 'none',
      }} />

      {/* Ring + question mark */}
      <div style={{
        position: 'relative', width: 180, height: 180,
        transform: `scale(${pulse * ringScale})`,
        marginBottom: 52,
      }}>
        {/* Outer ring */}
        <div style={{
          position: 'absolute', inset: 0, borderRadius: '50%',
          border: `3px solid ${GOLD}35`,
        }} />
        {/* Inner glow ring */}
        <div style={{
          position: 'absolute', inset: 10, borderRadius: '50%',
          border: `3px solid ${GOLD}`,
          opacity: 0.25 + progress * 0.75,
        }} />
        {/* Center */}
        <div style={{
          position: 'absolute', inset: 28, borderRadius: '50%',
          background: `radial-gradient(circle, ${GOLD}22 0%, transparent 70%)`,
          display: 'flex', alignItems: 'center', justifyContent: 'center',
        }}>
          <span style={{ fontSize: 54, fontWeight: 900, color: GOLD, lineHeight: 1 }}>?</span>
        </div>
      </div>

      {/* Text */}
      <div style={{ opacity: textOpacity, textAlign: 'center', maxWidth: 720, padding: '0 64px' }}>
        <p style={{
          fontSize: 26, fontWeight: 800, color: GOLD,
          letterSpacing: 5, textTransform: 'uppercase' as const, marginBottom: 24,
        }}>
          Düşünelim...
        </p>

        {/* 3 animated dots */}
        <div style={{ display: 'flex', gap: 14, justifyContent: 'center', marginBottom: 36 }}>
          {[dot1, dot2, dot3].map((d, i) => (
            <div key={i} style={{
              width: 14, height: 14, borderRadius: '50%',
              background: GOLD, opacity: 0.2 + d * 0.8,
              transform: `scale(${0.7 + d * 0.5})`,
            }} />
          ))}
        </div>

        {scene.question_text && (
          <p style={{
            fontSize: 20, color: 'rgba(255,255,255,0.5)',
            lineHeight: 1.65, fontFamily: brand.font_heading, margin: 0,
          }}>
            "{scene.question_text.slice(0, 90)}{scene.question_text.length > 90 ? '...' : ''}"
          </p>
        )}
      </div>

      {/* Progress bar */}
      <div style={{
        position: 'absolute', bottom: 0, left: 0, right: 0, height: 5,
        background: 'rgba(255,255,255,0.07)',
      }}>
        <div style={{
          height: '100%', background: GOLD,
          width: `${progress * 100}%`,
          borderRadius: '0 4px 4px 0',
        }} />
      </div>

      {scene.tts_url && <Audio src={scene.tts_url} />}
    </div>
  )
}
