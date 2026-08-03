/**
 * MotivationStepScene — 55-90 sn numaralı adım sahnesi
 */
import { AbsoluteFill, Audio, Img, interpolate, spring, useCurrentFrame, useVideoConfig } from 'remotion'
import { BrandConfig, Scene } from '../types'
import { T } from '../theme/tokens'
import { kenBurnsScale } from '../utils'

interface Props { scene: Scene; brand: BrandConfig }

export function MotivationStepScene({ scene, brand }: Props) {
  const frame = useCurrentFrame()
  const { fps } = useVideoConfig()

  const stepNumber = scene.step_number ?? 1
  const stepTitle  = scene.step_title ?? scene.title ?? ''
  const narration  = scene.narration ?? scene.message ?? ''
  const imageUrl   = scene.imageUrl ?? scene.image_url
  const audioUrl   = scene.audioUrl ?? scene.tts_url

  const numOp    = interpolate(frame, [0, 16], [0, 1], { extrapolateRight: 'clamp' })
  const numScale = spring({ frame, fps, config: { damping: 12, stiffness: 200 }, delay: 0 })
  const cardY    = interpolate(
    spring({ frame, fps, config: { damping: 20, stiffness: 160 }, delay: 10 }),
    [0, 1], [50, 0]
  )
  const cardOp = interpolate(frame, [10, 28], [0, 1], { extrapolateRight: 'clamp' })
  const textOp = interpolate(frame, [20, 36], [0, 1], { extrapolateRight: 'clamp' })

  return (
    <AbsoluteFill style={{ background: T.color.navy900, overflow: 'hidden' }}>
      {imageUrl && (
        <AbsoluteFill>
          <Img src={imageUrl} style={{
            width: '100%', height: '100%', objectFit: 'cover', filter: 'saturate(0.92)',
            transform: `scale(${kenBurnsScale(frame, scene.duration_seconds, fps, String(scene.id ?? ''))})`,
          }} />
        </AbsoluteFill>
      )}
      <AbsoluteFill style={{
        background: 'linear-gradient(to bottom, rgba(11,37,69,0.40) 0%, rgba(11,37,69,0.82) 100%)',
      }} />

      <AbsoluteFill style={{
        display: 'flex', flexDirection: 'column', justifyContent: 'center',
        paddingLeft: T.safe9x16.x, paddingRight: T.safe9x16.x,
      }}>
        <div style={{ opacity: numOp, transform: `scale(${0.6 + numScale * 0.4})`, transformOrigin: 'left center', display: 'flex', alignItems: 'center', gap: 14, marginBottom: 20 }}>
          <div style={{ width: 72, height: 72, borderRadius: T.radius.badge, background: T.color.gold, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
            <span style={{ fontSize: 36, fontWeight: 900, color: T.color.navy900, fontFamily: T.font.display }}>
              {stepNumber}
            </span>
          </div>
          <span style={{ fontSize: 26, fontWeight: 600, color: T.color.gold, fontFamily: T.font.body, letterSpacing: 1.5, textTransform: 'uppercase' as const }}>
            Adım {stepNumber}
          </span>
        </div>

        <div style={{ opacity: cardOp, transform: `translateY(${cardY}px)` }}>
          <div style={{ fontSize: 60, fontWeight: 800, color: '#FFFFFF', fontFamily: T.font.display, lineHeight: 1.2, marginBottom: 20 }}>
            {stepTitle}
          </div>
        </div>

        <div style={{ opacity: textOp }}>
          <div style={{ fontSize: 40, fontWeight: 400, color: 'rgba(255,255,255,0.88)', fontFamily: T.font.body, lineHeight: 1.6, borderLeft: `4px solid ${T.color.gold}`, paddingLeft: 20 }}>
            {narration}
          </div>
        </div>
      </AbsoluteFill>

      {audioUrl && <Audio src={audioUrl} />}
    </AbsoluteFill>
  )
}
