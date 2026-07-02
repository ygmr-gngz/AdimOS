import { interpolate, spring, useCurrentFrame, useVideoConfig, Audio } from 'remotion'
import { BrandConfig, Scene } from '../types'

const GOLD = '#C9A96E'
const BG = '#08121E'
const GREEN = '#22C55E'
const RED = '#EF4444'
const GREEN_BG = 'rgba(34,197,94,0.12)'
const RED_BG = 'rgba(239,68,68,0.12)'

interface Props { scene: Scene; brand: BrandConfig }

export function OptionAnalysisScene({ scene, brand }: Props) {
  const frame = useCurrentFrame()
  const { fps, width, height } = useVideoConfig()
  const isVertical = height > width

  const headerOpacity = interpolate(frame, [0, 18], [0, 1], { extrapolateRight: 'clamp' })
  const options = scene.options ?? []
  const highlightLabel = scene.highlight_option
  const correctLabel = scene.correct_label

  const padH = isVertical ? 52 : 76
  const padV = isVertical ? 68 : 52

  return (
    <div style={{
      width: '100%', height: '100%',
      background: `linear-gradient(155deg, ${BG} 0%, #0C1E36 100%)`,
      display: 'flex', flexDirection: 'column',
      padding: `${padV}px ${padH}px`,
      fontFamily: brand.font_body,
      position: 'relative', overflow: 'hidden',
    }}>
      {/* Ambient glow for highlighted option */}
      {highlightLabel && (
        <div style={{
          position: 'absolute', top: '40%', left: '50%',
          transform: 'translate(-50%, -50%)',
          width: 700, height: 400, borderRadius: '50%',
          background: highlightLabel === correctLabel
            ? `radial-gradient(ellipse, ${GREEN}0C 0%, transparent 65%)`
            : `radial-gradient(ellipse, ${RED}0C 0%, transparent 65%)`,
          pointerEvents: 'none',
        }} />
      )}

      {/* Header */}
      <div style={{ opacity: headerOpacity, marginBottom: isVertical ? 32 : 28, flexShrink: 0 }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 10 }}>
          <div style={{ width: 5, height: 24, borderRadius: 3, background: GOLD }} />
          <p style={{
            fontSize: 15, fontWeight: 800, color: GOLD,
            letterSpacing: 3, textTransform: 'uppercase' as const, margin: 0,
          }}>
            {scene.question_number ?? 1}. Soru — Şık Analizi
          </p>
        </div>
        <p style={{
          fontSize: isVertical ? 20 : 21,
          color: 'rgba(255,255,255,0.55)',
          fontFamily: brand.font_heading,
          lineHeight: 1.5, margin: 0, marginLeft: 17,
        }}>
          {scene.question_text?.slice(0, 110)}
          {(scene.question_text?.length ?? 0) > 110 ? '...' : ''}
        </p>
      </div>

      {/* Options */}
      <div style={{ display: 'flex', flexDirection: 'column', gap: isVertical ? 14 : 13, flex: 1 }}>
        {options.map((opt, i) => {
          const isHighlighted = opt.label === highlightLabel
          const isCorrect = opt.label === correctLabel

          const f0 = 22 + i * 11
          const optOpacity = interpolate(frame, [f0, f0 + 14], [0, 1], { extrapolateRight: 'clamp' })
          const badgeScale = isHighlighted
            ? spring({ frame, fps, config: { damping: 16 }, from: 0.7, to: 1, delay: f0 })
            : 1

          let borderColor = 'rgba(255,255,255,0.10)'
          let bg = 'rgba(255,255,255,0.04)'
          let labelBg = 'rgba(255,255,255,0.12)'
          let labelColor = 'rgba(255,255,255,0.7)'
          let textColor = 'rgba(255,255,255,0.78)'
          let tagBg = ''
          let tagLabel = ''
          let statusIcon: string | null = null

          if (isHighlighted) {
            if (isCorrect) {
              borderColor = GREEN
              bg = GREEN_BG
              labelBg = GREEN
              labelColor = '#fff'
              textColor = '#FFFFFF'
              tagBg = GREEN
              tagLabel = 'DOĞRU'
              statusIcon = '✓'
            } else {
              borderColor = RED
              bg = RED_BG
              labelBg = RED
              labelColor = '#fff'
              textColor = 'rgba(255,255,255,0.9)'
              tagBg = RED
              tagLabel = 'YANLIŞ'
              statusIcon = '✗'
            }
          }

          return (
            <div key={opt.label} style={{
              border: `2px solid ${borderColor}`,
              borderRadius: 14, overflow: 'hidden',
              opacity: optOpacity, background: bg,
              boxShadow: isHighlighted
                ? `0 0 24px ${isCorrect ? GREEN : RED}30`
                : 'none',
            }}>
              <div style={{
                display: 'flex', alignItems: 'flex-start', gap: 18,
                padding: `${isVertical ? 16 : 14}px 22px`,
              }}>
                <div style={{
                  width: 38, height: 38, borderRadius: '50%', flexShrink: 0,
                  background: labelBg, color: labelColor,
                  fontWeight: 800, fontSize: 17,
                  display: 'flex', alignItems: 'center', justifyContent: 'center',
                  transform: `scale(${badgeScale})`,
                }}>
                  {statusIcon ?? opt.label}
                </div>
                <div style={{ flex: 1 }}>
                  <span style={{
                    fontSize: isVertical ? 21 : 21,
                    color: textColor, lineHeight: 1.55,
                    fontWeight: isHighlighted ? 600 : 400,
                  }}>
                    {opt.text}
                  </span>
                  {isHighlighted && scene.explanation && (
                    <p style={{
                      margin: '10px 0 0', fontSize: 17,
                      color: isCorrect ? GREEN : RED,
                      lineHeight: 1.6, fontWeight: 500,
                    }}>
                      {scene.explanation}
                    </p>
                  )}
                </div>
                {isHighlighted && tagLabel && (
                  <div style={{
                    fontSize: 12, fontWeight: 800, padding: '5px 14px', borderRadius: 20,
                    background: tagBg, color: '#fff', flexShrink: 0,
                    alignSelf: 'flex-start', letterSpacing: 1,
                  }}>
                    {tagLabel}
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
