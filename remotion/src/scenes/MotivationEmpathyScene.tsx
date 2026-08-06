/**
 * MotivationEmpathyScene — 25-55 sn yalnız değilsin sahnesi
 */
import { AbsoluteFill, Audio, Img, interpolate, spring, useCurrentFrame, useVideoConfig } from 'remotion'
import { BrandConfig, Scene } from '../types'
import { T } from '../theme/tokens'
import { kenBurnsScale } from '../utils'

interface Props { scene: Scene; brand: BrandConfig }

export function MotivationEmpathyScene({ scene, brand }: Props) {
  const frame = useCurrentFrame()
  const { fps } = useVideoConfig()

  const title    = scene.title ?? ''
  const narration = scene.narration ?? scene.message ?? ''
  const imageUrl = scene.imageUrl ?? scene.image_url
  const audioUrl = scene.audioUrl ?? scene.tts_url

  const quoteOp    = interpolate(frame, [0, 20], [0, 1], { extrapolateRight: 'clamp' })
  const quoteScale = spring({ frame, fps, config: { damping: 14, stiffness: 120 }, delay: 0 })
  const textOp     = interpolate(frame, [14, 32], [0, 1], { extrapolateRight: 'clamp' })
  const textY      = interpolate(
    spring({ frame, fps, config: { damping: 22, stiffness: 180 }, delay: 14 }),
    [0, 1], [30, 0]
  )

  return (
    <AbsoluteFill style={{ background: T.color.navy700, overflow: 'hidden' }}>
      {imageUrl && (
        <AbsoluteFill>
          <Img src={imageUrl} style={{
            width: '100%', height: '100%', objectFit: 'cover', filter: 'saturate(0.92)',
            transform: `scale(${kenBurnsScale(frame, scene.duration_seconds, fps, String(scene.id ?? ''))})`,
          }} />
        </AbsoluteFill>
      )}
      <AbsoluteFill style={{ background: 'rgba(21,53,95,0.72)' }} />

      <AbsoluteFill style={{
        display: 'flex', flexDirection: 'column', justifyContent: 'center',
        paddingLeft: T.safe9x16.x, paddingRight: T.safe9x16.x,
      }}>
        <div style={{
          opacity: quoteOp,
          transform: `scale(${quoteScale})`,
          transformOrigin: 'left center',
          fontSize: 160, fontWeight: 900, color: T.color.gold500,
          lineHeight: 1, marginBottom: -20,
          fontFamily: 'serif',
        }}>
          {'"'}
        </div>

        <div style={{ opacity: textOp, transform: `translateY(${textY}px)`, paddingLeft: 12 }}>
          {title && (
            <div style={{ fontSize: 52, fontWeight: 700, color: '#FFFFFF', fontFamily: T.font.display, lineHeight: 1.25, marginBottom: 20 }}>
              {title}
            </div>
          )}
          <div style={{ fontSize: 40, fontWeight: 400, color: 'rgba(255,255,255,0.88)', fontFamily: T.font.body, lineHeight: 1.65 }}>
            {narration}
          </div>
          <div style={{ marginTop: 28, display: 'flex', alignItems: 'center', gap: 10 }}>
            <div style={{ width: 40, height: 2, background: T.color.gold500 }} />
            <span style={{ fontSize: 26, color: T.color.gold500, fontWeight: 600, fontFamily: T.font.body }}>
              Adım Müşavir
            </span>
          </div>
        </div>
      </AbsoluteFill>

      {audioUrl && <Audio src={audioUrl} />}
    </AbsoluteFill>
  )
}
