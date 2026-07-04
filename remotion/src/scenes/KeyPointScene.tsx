import { interpolate, spring, useCurrentFrame, useVideoConfig, Audio } from 'remotion'
import { BrandConfig, Scene } from '../types'

const ACCENT = '#2B7FE0'
const BG = '#08121E'

interface Props { scene: Scene; brand: BrandConfig }

export function KeyPointScene({ scene, brand }: Props) {
  const frame = useCurrentFrame()
  const { fps, width, height } = useVideoConfig()
  const isVertical = height > width

  const iconScale = spring({ frame, fps, config: { damping: 16, stiffness: 200 }, from: 0, to: 1 })
  const labelOpacity = interpolate(frame, [18, 36], [0, 1], { extrapolateRight: 'clamp' })
  const textOpacity = interpolate(frame, [25, 48], [0, 1], { extrapolateRight: 'clamp' })
  const textY = interpolate(frame, [25, 48], [28, 0], { extrapolateRight: 'clamp' })
  const cardOpacity = interpolate(frame, [22, 42], [0, 1], { extrapolateRight: 'clamp' })

  const padH = isVertical ? 56 : 110

  return (
    <div style={{
      width: '100%', height: '100%',
      background: `linear-gradient(150deg, ${BG} 0%, #0D1E38 55%, #09131E 100%)`,
      display: 'flex', flexDirection: 'column',
      alignItems: 'center', justifyContent: 'center',
      padding: `60px ${padH}px`,
      fontFamily: brand.font_body,
      position: 'relative', overflow: 'hidden',
    }}>
      {/* Gold ambient glow */}
      <div style={{
        position: 'absolute', inset: 0,
        background: `radial-gradient(ellipse at 50% 40%, ${ACCENT}10 0%, transparent 60%)`,
        pointerEvents: 'none',
      }} />

      {/* Top corner accent */}
      <div style={{
        position: 'absolute', top: 0, right: 0,
        width: 200, height: 200,
        background: `linear-gradient(225deg, ${ACCENT}20 0%, transparent 60%)`,
        pointerEvents: 'none',
      }} />
      <div style={{
        position: 'absolute', bottom: 0, left: 0,
        width: 160, height: 160,
        background: `linear-gradient(45deg, ${ACCENT}15 0%, transparent 60%)`,
        pointerEvents: 'none',
      }} />

      {/* Warning icon */}
      <div style={{
        width: isVertical ? 88 : 80, height: isVertical ? 88 : 80,
        background: ACCENT,
        borderRadius: 22,
        display: 'flex', alignItems: 'center', justifyContent: 'center',
        transform: `scale(${iconScale})`,
        marginBottom: 28,
        boxShadow: `0 0 40px ${ACCENT}55, 0 8px 24px rgba(0,0,0,0.4)`,
      }}>
        <svg width="42" height="42" viewBox="0 0 42 42" fill="none">
          <path d="M21 7L38 35H4L21 7Z" fill="none" stroke="#08121E" strokeWidth="3.5" strokeLinejoin="round"/>
          <line x1="21" y1="18" x2="21" y2="27" stroke="#08121E" strokeWidth="3.5" strokeLinecap="round"/>
          <circle cx="21" cy="31.5" r="2" fill="#08121E"/>
        </svg>
      </div>

      {/* Label */}
      <div style={{ opacity: labelOpacity, marginBottom: 22, textAlign: 'center' }}>
        <p style={{
          fontSize: 13, fontWeight: 800, color: ACCENT,
          letterSpacing: 4, textTransform: 'uppercase' as const, margin: 0,
        }}>
          Dikkat Edilmesi Gereken Nokta
        </p>
      </div>

      {/* Main key point */}
      <div style={{
        opacity: cardOpacity,
        background: 'rgba(43,127,224,0.09)',
        border: `1px solid ${ACCENT}40`,
        borderRadius: 18, padding: isVertical ? '28px 32px' : '26px 36px',
        marginBottom: scene.bullet_points && scene.bullet_points.length > 0 ? 28 : 0,
        width: '100%',
      }}>
        <p style={{
          opacity: textOpacity, transform: `translateY(${textY}px)`,
          fontSize: isVertical ? 28 : 32,
          fontFamily: brand.font_heading, fontWeight: 600,
          color: '#FFFFFF', lineHeight: 1.6, margin: 0, textAlign: 'center',
        }}>
          {scene.key_point ?? scene.explanation}
        </p>
      </div>

      {/* Bullet points */}
      {scene.bullet_points && scene.bullet_points.length > 0 && (
        <div style={{ width: '100%', display: 'flex', flexDirection: 'column', gap: 14 }}>
          {scene.bullet_points.map((point, i) => {
            const pOpacity = interpolate(frame, [48 + i * 10, 64 + i * 10], [0, 1], { extrapolateRight: 'clamp' })
            const pX = interpolate(frame, [48 + i * 10, 64 + i * 10], [-24, 0], { extrapolateRight: 'clamp' })
            return (
              <div key={i} style={{
                display: 'flex', gap: 16, alignItems: 'flex-start',
                opacity: pOpacity, transform: `translateX(${pX}px)`,
              }}>
                <div style={{
                  width: 10, height: 10, borderRadius: '50%',
                  background: ACCENT, marginTop: 11, flexShrink: 0,
                  boxShadow: `0 0 8px ${ACCENT}80`,
                }} />
                <p style={{
                  fontSize: isVertical ? 21 : 22,
                  color: 'rgba(255,255,255,0.78)', margin: 0, lineHeight: 1.65,
                }}>
                  {point}
                </p>
              </div>
            )
          })}
        </div>
      )}

      {scene.tts_url && <Audio src={scene.tts_url} />}
    </div>
  )
}
