import { interpolate, spring, useCurrentFrame, useVideoConfig, Audio } from 'remotion'
import { BrandConfig, Scene } from '../types'

const GOLD = '#C9A96E'
const BG_DARK = '#08121E'
const BG_MID = '#0D2040'

interface Props { scene: Scene; brand: BrandConfig }

export function IntroScene({ scene, brand }: Props) {
  const frame = useCurrentFrame()
  const { fps, width, height } = useVideoConfig()
  const isVertical = height > width

  const badgeScale = spring({ frame, fps, config: { damping: 18, stiffness: 180 }, from: 0, to: 1 })
  const titleOpacity = interpolate(frame, [15, 40], [0, 1], { extrapolateRight: 'clamp' })
  const titleY = interpolate(frame, [15, 40], [50, 0], { extrapolateRight: 'clamp' })
  const lineW = interpolate(frame, [42, 68], [0, 160], { extrapolateRight: 'clamp' })
  const subOpacity = interpolate(frame, [45, 68], [0, 1], { extrapolateRight: 'clamp' })

  const titleSize = isVertical ? 80 : 104
  const px = isVertical ? 64 : 140

  return (
    <div style={{
      width: '100%', height: '100%',
      background: `linear-gradient(145deg, ${BG_DARK} 0%, ${BG_MID} 55%, ${BG_DARK} 100%)`,
      display: 'flex', flexDirection: 'column',
      alignItems: 'center', justifyContent: 'center',
      overflow: 'hidden', position: 'relative',
      fontFamily: brand.font_body,
    }}>
      {/* Ambient glow top-right */}
      <div style={{
        position: 'absolute', top: -160, right: -160,
        width: 560, height: 560, borderRadius: '50%',
        background: `radial-gradient(circle, ${GOLD}18 0%, transparent 60%)`,
        pointerEvents: 'none',
      }} />
      {/* Ambient glow bottom-left */}
      <div style={{
        position: 'absolute', bottom: -180, left: -140,
        width: 600, height: 600, borderRadius: '50%',
        background: 'radial-gradient(circle, #1A4A9040 0%, transparent 60%)',
        pointerEvents: 'none',
      }} />

      {/* Top accent bar */}
      <div style={{
        position: 'absolute', top: 0, left: '10%', right: '10%', height: 4,
        background: `linear-gradient(90deg, transparent 0%, ${GOLD} 40%, ${GOLD} 60%, transparent 100%)`,
        opacity: 0.7,
      }} />

      {/* Badge */}
      <div style={{ transform: `scale(${badgeScale})`, marginBottom: isVertical ? 48 : 52 }}>
        <div style={{
          background: GOLD, color: '#08121E',
          fontWeight: 800, fontSize: isVertical ? 20 : 18,
          letterSpacing: 3.5, textTransform: 'uppercase' as const,
          padding: '11px 38px', borderRadius: 50,
          boxShadow: `0 0 36px ${GOLD}55`,
        }}>
          {scene.subtitle ?? 'SGS Soru Çözüm Serisi'}
        </div>
      </div>

      {/* Title */}
      <div style={{
        opacity: titleOpacity, transform: `translateY(${titleY}px)`,
        textAlign: 'center', padding: `0 ${px}px`,
      }}>
        <h1 style={{
          fontSize: titleSize,
          fontFamily: brand.font_heading, fontWeight: 700,
          color: '#FFFFFF', lineHeight: 1.18, margin: 0,
          textShadow: '0 4px 40px rgba(0,0,0,0.55)',
        }}>
          {scene.title ?? 'Ders Videosu'}
        </h1>
      </div>

      {/* Gold divider */}
      <div style={{
        width: lineW, height: 3,
        background: GOLD, borderRadius: 2,
        margin: isVertical ? '44px 0 30px' : '48px 0 28px',
      }} />

      {/* Subtitle */}
      <p style={{
        opacity: subOpacity,
        fontSize: isVertical ? 22 : 23,
        color: 'rgba(255,255,255,0.55)',
        letterSpacing: 0.5, margin: 0, textAlign: 'center',
        padding: `0 ${px}px`, lineHeight: 1.6,
      }}>
        {scene.key_point ?? 'Sınavda çıkan sorularla birlikte öğren'}
      </p>

      {/* Bottom accent bar */}
      <div style={{
        position: 'absolute', bottom: 0, left: '10%', right: '10%', height: 4,
        background: `linear-gradient(90deg, transparent 0%, ${GOLD} 40%, ${GOLD} 60%, transparent 100%)`,
        opacity: 0.35,
      }} />

      {scene.tts_url && <Audio src={scene.tts_url} />}
    </div>
  )
}
