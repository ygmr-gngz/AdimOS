/**
 * MotivationProblemScene — 5-25 sn problem/empati sahnesi
 */
import { AbsoluteFill, Audio, Img, interpolate, spring, useCurrentFrame, useVideoConfig } from 'remotion'
import { BrandConfig, Scene } from '../types'
import { T } from '../theme/tokens'
import { kenBurnsScale } from '../utils'

interface Props { scene: Scene; brand: BrandConfig }

export function MotivationProblemScene({ scene, brand }: Props) {
  const frame = useCurrentFrame()
  const { fps } = useVideoConfig()

  const title    = scene.title ?? ''
  const narration = scene.narration ?? scene.message ?? ''
  const imageUrl = scene.imageUrl ?? scene.image_url
  const audioUrl = scene.audioUrl ?? scene.tts_url

  const headerOp = interpolate(frame, [0, 14], [0, 1], { extrapolateRight: 'clamp' })
  const bodyY = interpolate(
    spring({ frame, fps, config: { damping: 20, stiffness: 160 }, delay: 10 }),
    [0, 1], [40, 0]
  )
  const bodyOp = interpolate(frame, [10, 26], [0, 1], { extrapolateRight: 'clamp' })

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
        background: 'linear-gradient(to bottom, rgba(11,37,69,0.55) 0%, rgba(11,37,69,0.70) 60%, rgba(11,37,69,0.88) 100%)',
      }} />

      <AbsoluteFill style={{
        display: 'flex', flexDirection: 'column',
        paddingLeft: T.safe9x16.x, paddingRight: T.safe9x16.x,
        paddingTop: T.safe9x16.top + 20,
        paddingBottom: T.safe9x16.bottom,
        gap: 24,
      }}>
        <div style={{ opacity: headerOp }}>
          <div style={{
            display: 'inline-flex', alignItems: 'center', gap: 10,
            background: 'rgba(232,176,75,0.18)', borderRadius: T.radius.chip,
            padding: '8px 18px', border: `1.5px solid ${T.color.gold500}`,
          }}>
            <div style={{ width: 8, height: 8, borderRadius: '50%', background: T.color.gold500 }} />
            <span style={{ fontSize: 26, fontWeight: 700, color: T.color.gold500, fontFamily: T.font.body }}>
              Bunu biliyor musun?
            </span>
          </div>
        </div>

        {title && (
          <div style={{ opacity: headerOp }}>
            <div style={{ fontSize: 58, fontWeight: 800, color: '#FFFFFF', fontFamily: T.font.display, lineHeight: 1.2 }}>
              {title}
            </div>
          </div>
        )}

        <div style={{ opacity: bodyOp, transform: `translateY(${bodyY}px)`, marginTop: 8 }}>
          <div style={{ fontSize: 42, fontWeight: 400, color: 'rgba(255,255,255,0.90)', fontFamily: T.font.body, lineHeight: 1.55 }}>
            {narration}
          </div>
        </div>
      </AbsoluteFill>

      {audioUrl && <Audio src={audioUrl} />}
    </AbsoluteFill>
  )
}
