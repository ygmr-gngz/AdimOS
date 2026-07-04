/**
 * CalculationStepsScene — Hesaplama adımları (beyaz tahta stili)
 * Adımlar TTS sesiyle senkronize sırayla açılır
 */
import { interpolate, useCurrentFrame, useVideoConfig, Audio } from 'remotion'
import { BrandConfig, Scene } from '../types'
import { PALETTE } from '../brand'

const ACCENT = PALETTE.ACCENT
const BG_DARK = PALETTE.BG_DARK

interface Props { scene: Scene; brand: BrandConfig }

export function CalculationStepsScene({ scene, brand }: Props) {
  const frame = useCurrentFrame()
  const { width, height } = useVideoConfig()
  const isVertical = height > width

  const steps = scene.calculation_steps ?? []
  const headerOpacity = interpolate(frame, [0, 20], [0, 1], { extrapolateRight: 'clamp' })
  const padH = isVertical ? 48 : 110

  return (
    <div style={{
      width: '100%', height: '100%',
      background: `linear-gradient(145deg, ${BG_DARK} 0%, #0C1D36 100%)`,
      display: 'flex', flexDirection: 'column',
      alignItems: 'center', justifyContent: 'center',
      padding: `56px ${padH}px`,
      fontFamily: brand.font_body, position: 'relative', overflow: 'hidden',
    }}>
      <div style={{
        position: 'absolute', inset: 0,
        background: `radial-gradient(ellipse at 50% 30%, ${ACCENT}07 0%, transparent 60%)`,
        pointerEvents: 'none',
      }} />

      {/* Başlık */}
      <div style={{ opacity: headerOpacity, width: '100%', marginBottom: 28 }}>
        {scene.title && (
          <h2 style={{
            fontSize: isVertical ? 24 : 30,
            fontFamily: brand.font_heading, fontWeight: 700,
            color: '#FFFFFF', margin: '0 0 6px',
          }}>
            {scene.title}
          </h2>
        )}
        {scene.subtitle && (
          <p style={{ fontSize: 13, color: PALETTE.TEXT_DIM, margin: 0 }}>{scene.subtitle}</p>
        )}
      </div>

      {/* Adımlar */}
      <div style={{ width: '100%', display: 'flex', flexDirection: 'column', gap: isVertical ? 12 : 14 }}>
        {steps.map((step, i) => {
          const revealAt = Math.round((i / Math.max(steps.length, 1)) * 150)
          const sOpacity = interpolate(frame, [revealAt + 20, revealAt + 38], [0, 1], { extrapolateRight: 'clamp' })
          const sX = interpolate(frame, [revealAt + 20, revealAt + 38], [-30, 0], { extrapolateRight: 'clamp' })
          const isResult = step.is_result

          return (
            <div key={i} style={{
              display: 'flex', alignItems: 'center', gap: 16,
              opacity: sOpacity, transform: `translateX(${sX}px)`,
              background: isResult ? `${ACCENT}15` : 'rgba(255,255,255,0.04)',
              border: `1px solid ${isResult ? ACCENT : ACCENT}${isResult ? '45' : '12'}`,
              borderRadius: 12, padding: isVertical ? '12px 16px' : '14px 20px',
              borderLeft: isResult ? `4px solid ${ACCENT}` : `4px solid ${ACCENT}20`,
            }}>
              {/* Adım numarası */}
              {!isResult && (
                <div style={{
                  width: 28, height: 28, borderRadius: '50%', flexShrink: 0,
                  background: `${ACCENT}20`, border: `1.5px solid ${ACCENT}40`,
                  color: ACCENT, fontWeight: 800, fontSize: 13,
                  display: 'flex', alignItems: 'center', justifyContent: 'center',
                }}>
                  {i + 1}
                </div>
              )}
              {isResult && (
                <div style={{
                  width: 28, height: 28, borderRadius: 8, flexShrink: 0,
                  background: ACCENT,
                  display: 'flex', alignItems: 'center', justifyContent: 'center',
                  fontSize: 14,
                }}>
                  =
                </div>
              )}

              {/* İçerik */}
              <div style={{ flex: 1, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <span style={{
                  fontSize: isVertical ? 14 : 16,
                  color: isResult ? '#FFFFFF' : PALETTE.TEXT_MID,
                  fontWeight: isResult ? 700 : 400,
                  lineHeight: 1.5,
                }}>
                  {step.label}
                </span>
                <span style={{
                  fontSize: isVertical ? 16 : 20,
                  color: isResult ? ACCENT : PALETTE.CORRECT,
                  fontWeight: 800, fontVariantNumeric: 'tabular-nums',
                  marginLeft: 20, flexShrink: 0,
                }}>
                  {step.value}
                </span>
              </div>
            </div>
          )
        })}
      </div>

      {scene.explanation && (
        <div style={{
          width: '100%', marginTop: 18,
          background: `${ACCENT}08`, border: `1px solid ${ACCENT}20`,
          borderLeft: `4px solid ${ACCENT}`, borderRadius: 10,
          padding: '11px 15px',
          opacity: interpolate(frame, [170, 190], [0, 1], { extrapolateRight: 'clamp' }),
        }}>
          <p style={{ fontSize: isVertical ? 12 : 14, color: PALETTE.TEXT_MID, lineHeight: 1.65, margin: 0 }}>
            {scene.explanation}
          </p>
        </div>
      )}

      {scene.tts_url && <Audio src={scene.tts_url} />}
    </div>
  )
}
