import { interpolate, spring, useCurrentFrame, useVideoConfig, Audio } from 'remotion'
import { BrandConfig, Scene } from '../types'

interface Props { scene: Scene; brand: BrandConfig }

export function OutroScene({ scene, brand }: Props) {
  const frame = useCurrentFrame()
  const { fps } = useVideoConfig()

  const logoOpacity = spring({ frame, fps, config: { damping: 20 }, from: 0, to: 1, delay: 5 })
  const titleOpacity = interpolate(frame, [15, 35], [0, 1], { extrapolateRight: 'clamp' })
  const subOpacity = interpolate(frame, [30, 50], [0, 1], { extrapolateRight: 'clamp' })
  const lineScale = interpolate(frame, [25, 45], [0, 1], { extrapolateRight: 'clamp' })

  return (
    <div style={{
      width: '100%', height: '100%',
      background: brand.primary_color,
      display: 'flex', flexDirection: 'column',
      alignItems: 'center', justifyContent: 'center',
      fontFamily: brand.font_body,
      overflow: 'hidden',
    }}>
      {/* Arka plan daireler */}
      <div style={{
        position: 'absolute', bottom: -200, right: -200,
        width: 600, height: 600, borderRadius: '50%',
        background: brand.secondary_color, opacity: 0.08,
      }} />

      {brand.logo_url && (
        <img
          src={brand.logo_url}
          style={{ height: 64, marginBottom: 40, opacity: logoOpacity, filter: 'brightness(10)' }}
        />
      )}

      <div style={{ opacity: titleOpacity, textAlign: 'center' }}>
        <h2 style={{
          fontSize: 48, fontFamily: brand.font_heading, fontWeight: 700,
          color: '#fff', margin: 0, marginBottom: 12,
        }}>
          {scene.title ?? 'Soru Çözümü Tamamlandı'}
        </h2>
      </div>

      <div style={{
        width: 80 * lineScale, height: 3,
        background: brand.secondary_color, borderRadius: 2, margin: '24px 0',
      }} />

      <div style={{ opacity: subOpacity, textAlign: 'center', maxWidth: 700 }}>
        <p style={{
          fontSize: 22, color: '#ffffff99', lineHeight: 1.7, margin: 0,
        }}>
          {scene.subtitle ?? 'Bir sonraki derste görüşmek üzere. Başarılar!'}
        </p>
      </div>

      {scene.tts_url && <Audio src={scene.tts_url} />}
    </div>
  )
}
