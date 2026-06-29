import { interpolate, useCurrentFrame, Audio } from 'remotion'
import { BrandConfig, Scene } from '../types'

interface Props { scene: Scene; brand: BrandConfig }

export function ThinkingScene({ scene, brand }: Props) {
  const frame = useCurrentFrame()
  const totalFrames = scene.duration_seconds * 30

  const opacity = interpolate(frame, [0, 15], [0, 1], { extrapolateRight: 'clamp' })
  // 3 nokta animasyonu
  const dot1 = Math.sin(frame * 0.15) * 0.5 + 0.5
  const dot2 = Math.sin(frame * 0.15 - 1) * 0.5 + 0.5
  const dot3 = Math.sin(frame * 0.15 - 2) * 0.5 + 0.5

  // Progress bar (geri sayım hissi)
  const progress = interpolate(frame, [0, totalFrames], [1, 0], { extrapolateRight: 'clamp' })

  return (
    <div style={{
      width: '100%', height: '100%',
      background: brand.primary_color,
      display: 'flex', flexDirection: 'column',
      alignItems: 'center', justifyContent: 'center',
      opacity,
    }}>
      {/* Merkez içerik */}
      <div style={{ textAlign: 'center' }}>
        <p style={{
          fontSize: 28, fontFamily: brand.font_body, fontWeight: 600,
          color: brand.secondary_color, letterSpacing: 3,
          textTransform: 'uppercase', marginBottom: 24,
        }}>
          Düşünelim...
        </p>

        {/* 3 nokta */}
        <div style={{ display: 'flex', gap: 16, justifyContent: 'center', marginBottom: 48 }}>
          {[dot1, dot2, dot3].map((d, i) => (
            <div key={i} style={{
              width: 16, height: 16, borderRadius: '50%',
              background: '#fff', opacity: 0.3 + d * 0.7,
              transform: `scale(${0.8 + d * 0.4})`,
            }} />
          ))}
        </div>

        <p style={{
          fontSize: 22, fontFamily: brand.font_heading,
          color: '#ffffff99', lineHeight: 1.6,
          maxWidth: 600,
        }}>
          {scene.question_text
            ? `"${scene.question_text.slice(0, 80)}${scene.question_text.length > 80 ? '...' : ''}"`
            : 'Soruyu okuyun ve cevabı düşünün'}
        </p>
      </div>

      {/* Alt progress bar */}
      <div style={{
        position: 'absolute', bottom: 0, left: 0, right: 0,
        height: 5, background: 'rgba(255,255,255,0.1)',
      }}>
        <div style={{
          height: '100%', background: brand.secondary_color,
          width: `${progress * 100}%`,
          transition: 'none',
        }} />
      </div>

      {scene.tts_url && <Audio src={scene.tts_url} />}
    </div>
  )
}
