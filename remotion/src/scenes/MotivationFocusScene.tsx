/**
 * MotivationFocusScene — 90-110 sn sınav odağı sahnesi
 */
import { AbsoluteFill, Audio, Img, interpolate, spring, useCurrentFrame, useVideoConfig } from 'remotion'
import { BrandConfig, Scene } from '../types'
import { T } from '../theme/tokens'

interface Props { scene: Scene; brand: BrandConfig }

export function MotivationFocusScene({ scene, brand }: Props) {
  const frame = useCurrentFrame()
  const { fps } = useVideoConfig()

  const title    = scene.title ?? ''
  const narration = scene.narration ?? scene.message ?? ''
  const imageUrl = scene.imageUrl ?? scene.image_url
  const audioUrl = scene.audioUrl ?? scene.tts_url

  const bgOp   = interpolate(frame, [0, 20], [0, 1], { extrapolateRight: 'clamp' })
  const cardY  = interpolate(
    spring({ frame, fps, config: { damping: 22, stiffness: 160 }, delay: 8 }),
    [0, 1], [60, 0]
  )
  const cardOp = interpolate(frame, [8, 26], [0, 1], { extrapolateRight: 'clamp' })
  const lineW  = interpolate(frame, [22, 46], [0, 1], { extrapolateRight: 'clamp' })

  return (
    <AbsoluteFill style={{ background: T.color.navy900, overflow: 'hidden' }}>
      {imageUrl && (
        <AbsoluteFill style={{ opacity: bgOp * 0.6 }}>
          <Img src={imageUrl} style={{ width: '100%', height: '100%', objectFit: 'cover' }} />
        </AbsoluteFill>
      )}
      <AbsoluteFill style={{ background: 'rgba(11,37,69,0.60)', opacity: bgOp }} />

      <AbsoluteFill style={{
        display: 'flex', flexDirection: 'column', justifyContent: 'center',
        paddingLeft: T.safe9x16.x, paddingRight: T.safe9x16.x,
      }}>
        <div style={{
          opacity: cardOp, transform: `translateY(${cardY}px)`,
          background: 'rgba(255,255,255,0.08)',
          border: `2px solid rgba(232,176,75,0.50)`,
          borderRadius: T.radius.card,
          padding: '40px 36px',
        }}>
          <div style={{ height: 4, borderRadius: 2, background: T.color.gold, marginBottom: 28, width: `${lineW * 100}%` }} />
          {title && (
            <div style={{ fontSize: 52, fontWeight: 800, color: T.color.gold, fontFamily: T.font.display, lineHeight: 1.2, marginBottom: 20 }}>
              {title}
            </div>
          )}
          <div style={{ fontSize: 42, fontWeight: 400, color: '#FFFFFF', fontFamily: T.font.body, lineHeight: 1.65 }}>
            {narration}
          </div>
          <div style={{ height: 4, borderRadius: 2, background: T.color.gold, marginTop: 28, opacity: 0.5, width: `${lineW * 60}%` }} />
        </div>
      </AbsoluteFill>

      {audioUrl && <Audio src={audioUrl} />}
    </AbsoluteFill>
  )
}
