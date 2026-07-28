/**
 * MotivationOutroScene — 110-120 sn kapanış sahnesi
 */
import { AbsoluteFill, Audio, Img, interpolate, spring, useCurrentFrame, useVideoConfig } from 'remotion'
import { BrandConfig, Scene } from '../types'
import { T } from '../theme/tokens'

interface Props { scene: Scene; brand: BrandConfig }

export function MotivationOutroScene({ scene, brand }: Props) {
  const frame = useCurrentFrame()
  const { fps } = useVideoConfig()

  const ctaText  = scene.cta_text ?? scene.narration ?? ''
  const imageUrl = scene.imageUrl ?? scene.image_url
  const audioUrl = scene.audioUrl ?? scene.tts_url
  const logoUrl  = brand?.logo_url

  const bgOp     = interpolate(frame, [0, 20], [0, 1], { extrapolateRight: 'clamp' })
  const logoY    = interpolate(
    spring({ frame, fps, config: { damping: 18, stiffness: 180 }, delay: 6 }),
    [0, 1], [-40, 0]
  )
  const logoOp   = interpolate(frame, [6, 22], [0, 1], { extrapolateRight: 'clamp' })
  const ctaOp    = interpolate(frame, [18, 36], [0, 1], { extrapolateRight: 'clamp' })
  const ctaY     = interpolate(
    spring({ frame, fps, config: { damping: 22, stiffness: 160 }, delay: 18 }),
    [0, 1], [30, 0]
  )
  const socialOp = interpolate(frame, [30, 46], [0, 1], { extrapolateRight: 'clamp' })

  return (
    <AbsoluteFill style={{ background: T.color.navy900, overflow: 'hidden' }}>
      {imageUrl && (
        <AbsoluteFill style={{ opacity: bgOp * 0.4 }}>
          <Img src={imageUrl} style={{ width: '100%', height: '100%', objectFit: 'cover' }} />
        </AbsoluteFill>
      )}
      <AbsoluteFill style={{ background: 'rgba(11,37,69,0.82)', opacity: bgOp }} />
      <AbsoluteFill style={{ background: 'radial-gradient(ellipse 80% 50% at 50% 50%, rgba(232,176,75,0.12) 0%, transparent 70%)', opacity: bgOp }} />

      <AbsoluteFill style={{
        display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center',
        paddingLeft: T.safe9x16.x, paddingRight: T.safe9x16.x,
        paddingTop: T.safe9x16.top, paddingBottom: T.safe9x16.bottom,
      }}>
        {logoUrl && (
          <div style={{ opacity: logoOp, transform: `translateY(${logoY}px)`, marginBottom: 32 }}>
            <Img src={logoUrl} style={{ width: 180, height: 'auto', objectFit: 'contain' }} />
          </div>
        )}

        <div style={{ opacity: logoOp, width: 60, height: 3, background: T.color.gold, borderRadius: 2, marginBottom: 32 }} />

        {ctaText && (
          <div style={{ opacity: ctaOp, transform: `translateY(${ctaY}px)`, textAlign: 'center', marginBottom: 36 }}>
            <div style={{ fontSize: 44, fontWeight: 700, color: '#FFFFFF', fontFamily: T.font.display, lineHeight: 1.45 }}>
              {ctaText}
            </div>
          </div>
        )}

        <div style={{ opacity: socialOp, display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 10 }}>
          <div style={{ fontSize: 34, fontWeight: 700, color: T.color.gold, fontFamily: T.font.body }}>@adimmusavir</div>
          <div style={{ fontSize: 26, color: 'rgba(255,255,255,0.55)', fontFamily: T.font.body, letterSpacing: 1 }}>YouTube · Instagram · TikTok</div>
        </div>
      </AbsoluteFill>

      {audioUrl && <Audio src={audioUrl} />}
    </AbsoluteFill>
  )
}
