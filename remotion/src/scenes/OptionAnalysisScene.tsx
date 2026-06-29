import { interpolate, spring, useCurrentFrame, useVideoConfig, Audio } from 'remotion'
import { BrandConfig, Scene } from '../types'

interface Props { scene: Scene; brand: BrandConfig }

const WRONG_COLOR = '#C0392B'
const CORRECT_COLOR = '#1A7A4A'

export function OptionAnalysisScene({ scene, brand }: Props) {
  const frame = useCurrentFrame()
  const { fps } = useVideoConfig()

  const headerOpacity = interpolate(frame, [0, 15], [0, 1], { extrapolateRight: 'clamp' })
  const options = scene.options ?? []
  const highlightLabel = scene.highlight_option  // hangi şık şu an analiz ediliyor
  const correctLabel = scene.correct_label

  return (
    <div style={{
      width: '100%', height: '100%',
      background: brand.background_color,
      display: 'flex', flexDirection: 'column',
      padding: '60px 80px',
      fontFamily: brand.font_body,
    }}>
      {/* Başlık */}
      <div style={{ opacity: headerOpacity, marginBottom: 36 }}>
        <p style={{
          fontSize: 16, fontWeight: 700, color: brand.secondary_color,
          letterSpacing: 3, textTransform: 'uppercase', marginBottom: 8,
        }}>
          {scene.question_number ?? 1}. Soru — Şık Analizi
        </p>
        <p style={{
          fontSize: 22, color: brand.primary_color, fontFamily: brand.font_heading,
          lineHeight: 1.5, margin: 0,
          opacity: 0.75,
        }}>
          {scene.question_text?.slice(0, 100)}
          {(scene.question_text?.length ?? 0) > 100 ? '...' : ''}
        </p>
      </div>

      {/* Şıklar + analiz */}
      <div style={{ display: 'flex', flexDirection: 'column', gap: 14, flex: 1 }}>
        {options.map((opt, i) => {
          const isHighlighted = opt.label === highlightLabel
          const isCorrect = opt.label === correctLabel
          const isWrong = !isCorrect

          const optFrame = 20 + i * 12
          const optOpacity = interpolate(frame, [optFrame, optFrame + 12], [0, 1], { extrapolateRight: 'clamp' })

          let borderColor = `${brand.primary_color}20`
          let bgColor = '#fff'
          let labelBg = brand.primary_color
          let textColor = brand.primary_color
          let statusIcon = null

          if (isHighlighted) {
            if (isCorrect) {
              borderColor = CORRECT_COLOR
              bgColor = `${CORRECT_COLOR}08`
              labelBg = CORRECT_COLOR
              statusIcon = '✓'
            } else {
              borderColor = WRONG_COLOR
              bgColor = `${WRONG_COLOR}06`
              labelBg = WRONG_COLOR
              textColor = WRONG_COLOR
              statusIcon = '✗'
            }
          }

          return (
            <div key={opt.label} style={{
              display: 'flex', flexDirection: 'column',
              border: `2px solid ${borderColor}`,
              borderRadius: 14, overflow: 'hidden',
              opacity: optOpacity,
              background: bgColor,
              boxShadow: isHighlighted ? '0 4px 20px rgba(0,0,0,0.08)' : 'none',
            }}>
              <div style={{
                display: 'flex', alignItems: 'flex-start', gap: 18,
                padding: '16px 24px',
              }}>
                <div style={{
                  width: 36, height: 36, borderRadius: '50%', flexShrink: 0,
                  background: labelBg,
                  color: '#fff', fontWeight: 700, fontSize: 16,
                  display: 'flex', alignItems: 'center', justifyContent: 'center',
                }}>
                  {statusIcon ?? opt.label}
                </div>
                <div style={{ flex: 1 }}>
                  <span style={{ fontSize: 20, color: textColor, lineHeight: 1.5, fontWeight: isHighlighted ? 600 : 400 }}>
                    {opt.text}
                  </span>
                  {/* Açıklama sadece vurgulanan şık için */}
                  {isHighlighted && scene.explanation && (
                    <p style={{
                      margin: '10px 0 0', fontSize: 17,
                      color: isCorrect ? CORRECT_COLOR : WRONG_COLOR,
                      lineHeight: 1.6, fontWeight: 500,
                    }}>
                      {isCorrect ? '✓ ' : '✗ '}{scene.explanation}
                    </p>
                  )}
                </div>
                {isHighlighted && (
                  <div style={{
                    fontSize: 13, fontWeight: 700, padding: '4px 12px', borderRadius: 20,
                    background: isCorrect ? CORRECT_COLOR : WRONG_COLOR,
                    color: '#fff', flexShrink: 0, alignSelf: 'flex-start',
                  }}>
                    {isCorrect ? 'DOĞRU' : 'YANLIŞ'}
                  </div>
                )}
              </div>
            </div>
          )
        })}
      </div>

      {scene.tts_url && <Audio src={scene.tts_url} />}
    </div>
  )
}
