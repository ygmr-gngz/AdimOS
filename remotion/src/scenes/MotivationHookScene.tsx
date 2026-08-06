/**
 * MotivationHookScene — 0-5 sn kanca sahnesi
 */
import { AbsoluteFill, Audio, Img, interpolate, spring, useCurrentFrame, useVideoConfig } from 'remotion'
import { BrandConfig, Scene } from '../types'
import { T } from '../theme/tokens'
import { kenBurnsScale } from '../utils'

interface Props { scene: Scene; brand: BrandConfig }

export function MotivationHookScene({ scene, brand }: Props) {
  const frame = useCurrentFrame()
  const { fps } = useVideoConfig()

  const message  = scene.message ?? scene.title ?? ''
  const imageUrl = scene.imageUrl ?? scene.image_url
  const audioUrl = scene.audioUrl ?? scene.tts_url

  const textY = interpolate(
    spring({ frame, fps, config: { damping: 18, stiffness: 200 }, delay: 4 }),
    [0, 1], [60, 0]
  )
  const textOp = interpolate(frame, [4, 18], [0, 1], { extrapolateRight: 'clamp' })
  const barH   = interpolate(frame, [12, 30], [0, 6], { extrapolateRight: 'clamp' })
  const lines  = message.split(/\n/).filter(Boolean)

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
      <AbsoluteFill style={{ background: 'rgba(11,37,69,0.35)' }} />
      <AbsoluteFill style={{
        background: 'linear-gradient(to top, rgba(11,37,69,0.85) 0%, transparent 55%)',
      }} />

      <AbsoluteFill style={{
        display: 'flex', flexDirection: 'column', justifyContent: 'flex-end',
        paddingLeft: T.safe9x16.x, paddingRight: T.safe9x16.x,
        paddingBottom: T.safe9x16.bottom + 20,
      }}>
        <div style={{ opacity: textOp, transform: `translateY(${textY}px)` }}>
          {lines.map((line, i) => (
            <div key={i} style={{
              fontSize: message.length > 60 ? 68 : 80,
              fontWeight: 800, color: '#FFFFFF', lineHeight: 1.15,
              fontFamily: T.font.display,
              marginBottom: i < lines.length - 1 ? 8 : 0,
            }}>
              {line}
            </div>
          ))}
          <div style={{ marginTop: 20, width: 72, height: barH, background: T.color.gold500, borderRadius: 3 }} />
        </div>
      </AbsoluteFill>

      {audioUrl && <Audio src={audioUrl} />}
    </AbsoluteFill>
  )
}
