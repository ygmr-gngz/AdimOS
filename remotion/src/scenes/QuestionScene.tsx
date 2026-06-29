import { interpolate, spring, useCurrentFrame, useVideoConfig, Audio } from 'remotion'
import { BrandConfig, Scene } from '../types'

interface Props { scene: Scene; brand: BrandConfig }

export function QuestionScene({ scene, brand }: Props) {
  const frame = useCurrentFrame()
  const { fps } = useVideoConfig()

  const headerOpacity = interpolate(frame, [0, 15], [0, 1], { extrapolateRight: 'clamp' })
  const questionOpacity = interpolate(frame, [10, 30], [0, 1], { extrapolateRight: 'clamp' })
  const questionY = interpolate(frame, [10, 30], [20, 0], { extrapolateRight: 'clamp' })

  const options = scene.options ?? []

  return (
    <div style={{
      width: '100%', height: '100%',
      background: brand.background_color,
      display: 'flex', flexDirection: 'column',
      padding: '60px 80px',
      fontFamily: brand.font_body,
    }}>
      {/* Üst bar: ders adı + soru sayacı */}
      <div style={{
        display: 'flex', justifyContent: 'space-between', alignItems: 'center',
        opacity: headerOpacity, marginBottom: 40,
      }}>
        <div style={{
          display: 'flex', alignItems: 'center', gap: 12,
        }}>
          <div style={{
            width: 6, height: 32, borderRadius: 3,
            background: brand.secondary_color,
          }} />
          <span style={{ fontSize: 20, fontWeight: 600, color: brand.primary_color }}>
            {scene.title ?? 'Soru'}
          </span>
        </div>
        <div style={{
          background: brand.primary_color,
          color: '#fff', borderRadius: 24,
          padding: '8px 24px', fontSize: 18, fontWeight: 700,
        }}>
          {scene.question_number ?? 1} / {scene.total_questions ?? 4}
        </div>
      </div>

      {/* Soru metni */}
      <div style={{
        background: '#fff',
        border: `2px solid ${brand.primary_color}18`,
        borderRadius: 16, padding: '36px 40px',
        marginBottom: 32, flexShrink: 0,
        opacity: questionOpacity,
        transform: `translateY(${questionY}px)`,
        boxShadow: '0 4px 24px rgba(11,42,74,0.06)',
      }}>
        <p style={{
          fontSize: 26, fontFamily: brand.font_heading, fontWeight: 600,
          color: brand.primary_color, lineHeight: 1.6, margin: 0,
        }}>
          {scene.question_text}
        </p>
      </div>

      {/* Şıklar */}
      <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
        {options.map((opt, i) => {
          const optFrame = 35 + i * 10
          const optOpacity = interpolate(frame, [optFrame, optFrame + 15], [0, 1], { extrapolateRight: 'clamp' })
          const optX = interpolate(frame, [optFrame, optFrame + 15], [-30, 0], { extrapolateRight: 'clamp' })

          return (
            <div
              key={opt.label}
              style={{
                display: 'flex', alignItems: 'flex-start', gap: 20,
                background: '#fff',
                border: `1.5px solid ${brand.primary_color}20`,
                borderRadius: 12, padding: '18px 24px',
                opacity: optOpacity,
                transform: `translateX(${optX}px)`,
                boxShadow: '0 2px 8px rgba(11,42,74,0.04)',
              }}
            >
              <div style={{
                width: 36, height: 36, borderRadius: '50%', flexShrink: 0,
                background: brand.primary_color,
                color: '#fff', fontWeight: 700, fontSize: 16,
                display: 'flex', alignItems: 'center', justifyContent: 'center',
              }}>
                {opt.label}
              </div>
              <span style={{ fontSize: 22, color: brand.primary_color, lineHeight: 1.5 }}>
                {opt.text}
              </span>
            </div>
          )
        })}
      </div>

      {scene.tts_url && <Audio src={scene.tts_url} />}
    </div>
  )
}
