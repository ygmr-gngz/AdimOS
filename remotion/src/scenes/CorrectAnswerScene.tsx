import { interpolate, spring, useCurrentFrame, useVideoConfig, Audio } from 'remotion'
import { BrandConfig, Scene } from '../types'

interface Props { scene: Scene; brand: BrandConfig }

const CORRECT_COLOR = '#1A7A4A'

export function CorrectAnswerScene({ scene, brand }: Props) {
  const frame = useCurrentFrame()
  const { fps } = useVideoConfig()

  const checkScale = spring({ frame, fps, config: { damping: 14, stiffness: 180 }, from: 0, to: 1 })
  const contentOpacity = interpolate(frame, [20, 40], [0, 1], { extrapolateRight: 'clamp' })
  const contentY = interpolate(frame, [20, 40], [20, 0], { extrapolateRight: 'clamp' })
  const correctOption = scene.options?.find(o => o.label === scene.correct_label)

  return (
    <div style={{
      width: '100%', height: '100%',
      background: brand.background_color,
      display: 'flex', flexDirection: 'column',
      alignItems: 'center', justifyContent: 'center',
      padding: '60px 120px',
      fontFamily: brand.font_body,
    }}>
      {/* Büyük tik işareti */}
      <div style={{
        width: 100, height: 100, borderRadius: '50%',
        background: CORRECT_COLOR,
        display: 'flex', alignItems: 'center', justifyContent: 'center',
        transform: `scale(${checkScale})`,
        marginBottom: 40,
        boxShadow: `0 8px 32px ${CORRECT_COLOR}40`,
      }}>
        <svg width="52" height="52" viewBox="0 0 52 52" fill="none">
          <path d="M12 26L22 36L40 16" stroke="white" strokeWidth="5" strokeLinecap="round" strokeLinejoin="round"/>
        </svg>
      </div>

      {/* Doğru cevap başlığı */}
      <div style={{ opacity: contentOpacity, transform: `translateY(${contentY}px)`, textAlign: 'center' }}>
        <p style={{
          fontSize: 16, fontWeight: 700, color: CORRECT_COLOR,
          letterSpacing: 3, textTransform: 'uppercase', marginBottom: 16,
        }}>
          Doğru Cevap
        </p>

        {/* Doğru şık kutusu */}
        {correctOption && (
          <div style={{
            display: 'flex', alignItems: 'flex-start', gap: 20,
            background: `${CORRECT_COLOR}0A`,
            border: `2px solid ${CORRECT_COLOR}`,
            borderRadius: 16, padding: '24px 32px',
            marginBottom: 36, textAlign: 'left',
          }}>
            <div style={{
              width: 44, height: 44, borderRadius: '50%', flexShrink: 0,
              background: CORRECT_COLOR,
              color: '#fff', fontWeight: 700, fontSize: 20,
              display: 'flex', alignItems: 'center', justifyContent: 'center',
            }}>
              {scene.correct_label}
            </div>
            <span style={{
              fontSize: 24, fontFamily: brand.font_heading, fontWeight: 600,
              color: brand.primary_color, lineHeight: 1.5,
            }}>
              {correctOption.text}
            </span>
          </div>
        )}

        {/* Açıklama */}
        {scene.explanation && (
          <div style={{
            background: '#fff',
            border: `1.5px solid ${brand.primary_color}15`,
            borderRadius: 14, padding: '24px 32px',
            textAlign: 'left',
          }}>
            <p style={{
              fontSize: 12, fontWeight: 700, color: brand.secondary_color,
              letterSpacing: 2, textTransform: 'uppercase', marginBottom: 12,
            }}>
              Çözüm Mantığı
            </p>
            <p style={{
              fontSize: 22, color: brand.primary_color, lineHeight: 1.7, margin: 0,
            }}>
              {scene.explanation}
            </p>
          </div>
        )}
      </div>

      {scene.tts_url && <Audio src={scene.tts_url} />}
    </div>
  )
}
