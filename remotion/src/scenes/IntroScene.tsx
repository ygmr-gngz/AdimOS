import { interpolate, spring, useCurrentFrame, useVideoConfig, Audio } from 'remotion'
import { BrandConfig, Scene } from '../types'

interface Props { scene: Scene; brand: BrandConfig }

export function IntroScene({ scene, brand }: Props) {
  const frame = useCurrentFrame()
  const { fps } = useVideoConfig()

  const titleOpacity = spring({ frame, fps, config: { damping: 20 }, from: 0, to: 1, delay: 10 })
  const subtitleOpacity = interpolate(frame, [20, 45], [0, 1], { extrapolateRight: 'clamp' })
  const lineScale = interpolate(frame, [30, 50], [0, 1], { extrapolateRight: 'clamp' })
  const bgY = interpolate(frame, [0, 120], [0, -20], { extrapolateRight: 'clamp' })

  return (
    <div style={{
      width: '100%', height: '100%',
      background: brand.background_color,
      display: 'flex', flexDirection: 'column',
      alignItems: 'center', justifyContent: 'center',
      overflow: 'hidden',
    }}>
      {/* Dekoratif arka plan şekli */}
      <div style={{
        position: 'absolute', top: -200 + bgY, right: -200,
        width: 600, height: 600,
        borderRadius: '50%',
        background: brand.secondary_color,
        opacity: 0.08,
      }} />
      <div style={{
        position: 'absolute', bottom: -150 + bgY * 0.5, left: -150,
        width: 400, height: 400,
        borderRadius: '50%',
        background: brand.primary_color,
        opacity: 0.06,
      }} />

      {/* Logo alanı */}
      {brand.logo_url && (
        <img
          src={brand.logo_url}
          style={{ height: 60, marginBottom: 48, opacity: subtitleOpacity }}
        />
      )}

      {/* Başlık */}
      <div style={{
        opacity: titleOpacity,
        transform: `translateY(${interpolate(frame, [0, 20], [30, 0], { extrapolateRight: 'clamp' })}px)`,
        textAlign: 'center', padding: '0 80px',
      }}>
        <p style={{
          fontSize: 22, fontFamily: brand.font_body, fontWeight: 600,
          color: brand.secondary_color, letterSpacing: 4,
          textTransform: 'uppercase', marginBottom: 16,
        }}>
          {scene.subtitle ?? 'Soru Çözüm Serisi'}
        </p>
        <h1 style={{
          fontSize: 72, fontFamily: brand.font_heading, fontWeight: 700,
          color: brand.primary_color, lineHeight: 1.15, marginBottom: 0,
        }}>
          {scene.title ?? 'Ders Videosu'}
        </h1>
      </div>

      {/* Altın çizgi */}
      <div style={{
        width: 120 * lineScale, height: 4,
        background: brand.secondary_color,
        borderRadius: 2, marginTop: 40,
        opacity: subtitleOpacity,
      }} />

      {scene.tts_url && <Audio src={scene.tts_url} />}
    </div>
  )
}
