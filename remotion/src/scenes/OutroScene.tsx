import { interpolate, spring, useCurrentFrame, useVideoConfig, Audio } from 'remotion'
import { BrandConfig, Scene } from '../types'

const ACCENT = '#2B7FE0'
const BG = '#08121E'

interface Props { scene: Scene; brand: BrandConfig }

export function OutroScene({ scene, brand }: Props) {
  const frame = useCurrentFrame()
  const { fps, width, height } = useVideoConfig()
  const isVertical = height > width

  const iconScale = spring({ frame, fps, config: { damping: 18 }, from: 0, to: 1 })
  const titleOpacity = interpolate(frame, [18, 40], [0, 1], { extrapolateRight: 'clamp' })
  const titleY = interpolate(frame, [18, 40], [40, 0], { extrapolateRight: 'clamp' })
  const lineW = interpolate(frame, [35, 58], [0, 140], { extrapolateRight: 'clamp' })
  const subOpacity = interpolate(frame, [42, 62], [0, 1], { extrapolateRight: 'clamp' })
  const cardOpacity = interpolate(frame, [52, 72], [0, 1], { extrapolateRight: 'clamp' })

  return (
    <div style={{
      width: '100%', height: '100%',
      background: `linear-gradient(145deg, ${BG} 0%, #0C1E38 55%, ${BG} 100%)`,
      display: 'flex', flexDirection: 'column',
      alignItems: 'center', justifyContent: 'center',
      fontFamily: brand.font_body,
      overflow: 'hidden', position: 'relative',
    }}>
      {/* Gold glow at top */}
      <div style={{
        position: 'absolute', top: -80, left: '50%',
        transform: 'translateX(-50%)',
        width: 700, height: 400, borderRadius: '50%',
        background: `radial-gradient(ellipse, ${ACCENT}15 0%, transparent 65%)`,
        pointerEvents: 'none',
      }} />

      {/* Corner accents */}
      <div style={{
        position: 'absolute', top: 0, left: 0, right: 0, height: 4,
        background: `linear-gradient(90deg, transparent 0%, ${ACCENT} 40%, ${ACCENT} 60%, transparent 100%)`,
        opacity: 0.6,
      }} />
      <div style={{
        position: 'absolute', bottom: 0, left: 0, right: 0, height: 4,
        background: `linear-gradient(90deg, transparent 0%, ${ACCENT} 40%, ${ACCENT} 60%, transparent 100%)`,
        opacity: 0.3,
      }} />

      {/* Star/Trophy icon */}
      <div style={{
        width: isVertical ? 90 : 80, height: isVertical ? 90 : 80,
        background: ACCENT, borderRadius: '50%',
        display: 'flex', alignItems: 'center', justifyContent: 'center',
        transform: `scale(${iconScale})`,
        marginBottom: 32,
        boxShadow: `0 0 40px ${ACCENT}55, 0 8px 28px rgba(0,0,0,0.5)`,
      }}>
        <svg width="44" height="44" viewBox="0 0 44 44" fill="none">
          <path d="M22 6L26.5 16.5H38L29 23.5L32.5 34L22 27.5L11.5 34L15 23.5L6 16.5H17.5L22 6Z"
            fill="#08121E" stroke="#08121E" strokeWidth="1" strokeLinejoin="round"/>
        </svg>
      </div>

      {/* Title */}
      <div style={{
        opacity: titleOpacity, transform: `translateY(${titleY}px)`,
        textAlign: 'center', padding: isVertical ? '0 60px' : '0 120px',
      }}>
        <h2 style={{
          fontSize: isVertical ? 56 : 64,
          fontFamily: brand.font_heading, fontWeight: 700,
          color: '#FFFFFF', margin: 0, lineHeight: 1.2,
          textShadow: '0 4px 30px rgba(0,0,0,0.5)',
        }}>
          {scene.title ?? 'Tebrikler!'}
        </h2>
      </div>

      {/* Gold line */}
      <div style={{
        width: lineW, height: 3,
        background: ACCENT, borderRadius: 2,
        margin: isVertical ? '36px 0 24px' : '32px 0 20px',
      }} />

      {/* Subtitle */}
      <p style={{
        opacity: subOpacity,
        fontSize: isVertical ? 22 : 24,
        color: 'rgba(255,255,255,0.6)',
        lineHeight: 1.6, margin: 0, textAlign: 'center',
        padding: isVertical ? '0 60px' : '0 140px',
      }}>
        {scene.subtitle ?? 'Soru çözümü tamamlandı. Bir sonraki derste görüşmek üzere!'}
      </p>

      {/* CTA card */}
      <div style={{
        opacity: cardOpacity,
        marginTop: isVertical ? 48 : 40,
        background: 'rgba(43,127,224,0.10)',
        border: `1px solid ${ACCENT}40`,
        borderRadius: 16, padding: '18px 40px',
        textAlign: 'center',
      }}>
        <p style={{
          fontSize: isVertical ? 18 : 18,
          color: ACCENT, fontWeight: 700, letterSpacing: 2,
          textTransform: 'uppercase' as const, margin: 0,
        }}>
          Beğendiysen paylaş & takip et
        </p>
      </div>

      {scene.tts_url && <Audio src={scene.tts_url} />}
    </div>
  )
}
