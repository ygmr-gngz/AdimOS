import { interpolate, spring, useCurrentFrame, useVideoConfig, Audio } from 'remotion'
import { BrandConfig, Scene } from '../types'

interface Props { scene: Scene; brand: BrandConfig }

export function KeyPointScene({ scene, brand }: Props) {
  const frame = useCurrentFrame()
  const { fps } = useVideoConfig()

  const iconScale = spring({ frame, fps, config: { damping: 18 }, from: 0, to: 1, delay: 5 })
  const textOpacity = interpolate(frame, [20, 45], [0, 1], { extrapolateRight: 'clamp' })
  const textY = interpolate(frame, [20, 45], [24, 0], { extrapolateRight: 'clamp' })

  return (
    <div style={{
      width: '100%', height: '100%',
      background: brand.primary_color,
      display: 'flex', flexDirection: 'column',
      alignItems: 'center', justifyContent: 'center',
      padding: '60px 120px',
      fontFamily: brand.font_body,
    }}>
      {/* Dekoratif element */}
      <div style={{
        position: 'absolute', top: 0, right: 0,
        width: 0, height: 0,
        borderStyle: 'solid',
        borderWidth: '0 180px 180px 0',
        borderColor: `transparent ${brand.secondary_color}20 transparent transparent`,
      }} />

      {/* Uyarı ikonu */}
      <div style={{
        width: 80, height: 80,
        background: brand.secondary_color,
        borderRadius: 20,
        display: 'flex', alignItems: 'center', justifyContent: 'center',
        transform: `scale(${iconScale})`,
        marginBottom: 36,
        boxShadow: `0 8px 32px ${brand.secondary_color}40`,
      }}>
        <svg width="40" height="40" viewBox="0 0 40 40" fill="none">
          <path d="M20 8L36 32H4L20 8Z" stroke="white" strokeWidth="3" strokeLinejoin="round"/>
          <line x1="20" y1="18" x2="20" y2="26" stroke="white" strokeWidth="3" strokeLinecap="round"/>
          <circle cx="20" cy="30" r="1.5" fill="white"/>
        </svg>
      </div>

      <div style={{
        opacity: textOpacity,
        transform: `translateY(${textY}px)`,
        textAlign: 'center', maxWidth: 900,
      }}>
        <p style={{
          fontSize: 16, fontWeight: 700,
          color: brand.secondary_color,
          letterSpacing: 3, textTransform: 'uppercase', marginBottom: 20,
        }}>
          Bu Soruda Dikkat Edilmesi Gereken Nokta
        </p>

        <p style={{
          fontSize: 32, fontFamily: brand.font_heading, fontWeight: 600,
          color: '#fff', lineHeight: 1.6, margin: 0,
        }}>
          {scene.key_point ?? scene.explanation}
        </p>

        {/* Vurgular */}
        {scene.bullet_points && scene.bullet_points.length > 0 && (
          <div style={{ marginTop: 36, textAlign: 'left', display: 'inline-block' }}>
            {scene.bullet_points.map((point, i) => {
              const pOpacity = interpolate(frame, [45 + i * 10, 60 + i * 10], [0, 1], { extrapolateRight: 'clamp' })
              return (
                <div key={i} style={{
                  display: 'flex', gap: 14, alignItems: 'flex-start',
                  marginBottom: 16, opacity: pOpacity,
                }}>
                  <div style={{
                    width: 8, height: 8, borderRadius: '50%',
                    background: brand.secondary_color,
                    marginTop: 10, flexShrink: 0,
                  }} />
                  <p style={{ fontSize: 22, color: '#ffffffCC', margin: 0, lineHeight: 1.6 }}>
                    {point}
                  </p>
                </div>
              )
            })}
          </div>
        )}
      </div>

      {scene.tts_url && <Audio src={scene.tts_url} />}
    </div>
  )
}
