/**
 * SplitQuizScene — 16:9 yatay bölünmüş ekran soru çözümü
 * Sol panel: çözüm adımları seslendirmeyle senkronize açılır (55%)
 * Sağ panel: soru + şıklar (tüm video boyunca sabit) (45%)
 */
import { interpolate, useCurrentFrame, useVideoConfig, Audio } from 'remotion'
import { BrandConfig, Scene, SolutionStep } from '../types'
import { PALETTE } from '../brand'

const ACCENT = PALETTE.ACCENT
const BG_DARK = PALETTE.BG_DARK
const BG_MID = PALETTE.BG_MID
const BG_CARD = PALETTE.BG_CARD

interface Props { scene: Scene; brand: BrandConfig }

// ── Çözüm adımı bileşeni ─────────────────────────────────────
function SolutionStepItem({ step, index, frame, totalSteps, fps }: {
  step: SolutionStep
  index: number
  frame: number
  totalSteps: number
  fps: number
}) {
  const revealAt = Math.round((index / Math.max(totalSteps, 1)) * 180)
  const opacity = interpolate(frame, [revealAt, revealAt + 20], [0, 1], { extrapolateRight: 'clamp' })
  const y = interpolate(frame, [revealAt, revealAt + 20], [16, 0], { extrapolateRight: 'clamp' })

  if (step.type === 'journal_entry') {
    return (
      <div style={{ opacity, transform: `translateY(${y}px)` }}>
        <div style={{
          background: 'rgba(43,127,224,0.08)',
          border: `1px solid ${ACCENT}30`,
          borderRadius: 10, overflow: 'hidden', fontSize: 13,
        }}>
          <div style={{
            background: `${ACCENT}20`, padding: '6px 14px',
            display: 'flex', justifyContent: 'space-between',
            color: PALETTE.ACCENT_LT, fontWeight: 700, fontSize: 11,
            letterSpacing: 2, textTransform: 'uppercase' as const,
          }}>
            <span>BORÇ</span><span>ALACAK</span>
          </div>
          {step.debit && (
            <div style={{ display: 'flex', justifyContent: 'space-between', padding: '8px 14px', borderBottom: `1px solid ${ACCENT}15` }}>
              <span style={{ color: '#FFFFFF', fontSize: 13 }}>
                {step.debit.code && <span style={{ color: PALETTE.TEXT_DIM, marginRight: 6 }}>{step.debit.code}</span>}
                {step.debit.name}
              </span>
              <span style={{ color: PALETTE.CORRECT, fontWeight: 700, fontVariantNumeric: 'tabular-nums' }}>
                {step.debit.amount.toLocaleString('tr-TR')} ₺
              </span>
            </div>
          )}
          {step.credits?.map((cr, i) => (
            <div key={i} style={{ display: 'flex', justifyContent: 'space-between', padding: '8px 14px 8px 28px', borderBottom: i < (step.credits!.length - 1) ? `1px solid ${ACCENT}10` : 'none' }}>
              <span style={{ color: 'rgba(255,255,255,0.75)', fontSize: 13 }}>
                {cr.code && <span style={{ color: PALETTE.TEXT_DIM, marginRight: 6 }}>{cr.code}</span>}
                {cr.name}
              </span>
              <span style={{ color: PALETTE.ACCENT_LT, fontWeight: 700, fontVariantNumeric: 'tabular-nums' }}>
                {cr.amount.toLocaleString('tr-TR')} ₺
              </span>
            </div>
          ))}
        </div>
      </div>
    )
  }

  if (step.type === 'formula') {
    return (
      <div style={{ opacity, transform: `translateY(${y}px)` }}>
        <div style={{
          background: 'rgba(43,127,224,0.06)', border: `1px solid ${ACCENT}25`,
          borderRadius: 10, padding: '10px 14px',
          display: 'flex', alignItems: 'baseline', gap: 10, flexWrap: 'wrap' as const,
        }}>
          <span style={{ color: PALETTE.TEXT_MID, fontSize: 14 }}>{step.formula}</span>
          {step.result && (
            <span style={{ color: ACCENT, fontWeight: 800, fontSize: 16 }}>{step.result}</span>
          )}
        </div>
      </div>
    )
  }

  if (step.type === 'note') {
    return (
      <div style={{ opacity, transform: `translateY(${y}px)` }}>
        <div style={{ display: 'flex', gap: 10, alignItems: 'flex-start' }}>
          <div style={{ width: 6, height: 6, borderRadius: '50%', background: ACCENT, marginTop: 7, flexShrink: 0 }} />
          <span style={{ fontSize: 13, color: PALETTE.TEXT_DIM, lineHeight: 1.6 }}>{step.text}</span>
        </div>
      </div>
    )
  }

  // Default: text
  return (
    <div style={{ opacity, transform: `translateY(${y}px)` }}>
      <div style={{ display: 'flex', gap: 10, alignItems: 'flex-start' }}>
        <div style={{
          width: 22, height: 22, borderRadius: '50%', flexShrink: 0,
          background: `${ACCENT}25`, border: `1.5px solid ${ACCENT}`,
          display: 'flex', alignItems: 'center', justifyContent: 'center',
          fontSize: 11, fontWeight: 800, color: ACCENT,
        }}>
          {index + 1}
        </div>
        <span style={{ fontSize: 14, color: '#FFFFFF', lineHeight: 1.65 }}>{step.text}</span>
      </div>
    </div>
  )
}

// ── Ana bileşen ───────────────────────────────────────────────
export function SplitQuizScene({ scene, brand }: Props) {
  const frame = useCurrentFrame()
  const { fps } = useVideoConfig()

  const steps = scene.solution_steps ?? []
  const totalFrames = Math.round(scene.duration_seconds * fps)
  const options = scene.options ?? []

  // Sağ panel (soru) fade in
  const rightOpacity = interpolate(frame, [0, 20], [0, 1], { extrapolateRight: 'clamp' })
  // Sol panel başlık
  const leftHeaderOpacity = interpolate(frame, [10, 30], [0, 1], { extrapolateRight: 'clamp' })

  // Doğru şık vurgulama — son %20'de
  const revealStart = Math.round(totalFrames * 0.78)
  const correctReveal = interpolate(frame, [revealStart, revealStart + 25], [0, 1], { extrapolateRight: 'clamp' })

  return (
    <div style={{
      width: '100%', height: '100%',
      background: BG_DARK,
      display: 'flex', flexDirection: 'row',
      fontFamily: brand.font_body, overflow: 'hidden', position: 'relative',
    }}>
      {/* Ambient glow */}
      <div style={{
        position: 'absolute', top: -100, left: -100,
        width: 500, height: 500, borderRadius: '50%',
        background: `radial-gradient(circle, ${ACCENT}0C 0%, transparent 65%)`,
        pointerEvents: 'none',
      }} />

      {/* Logo filigran — merkezi, %5 opaklık */}
      <div style={{
        position: 'absolute', inset: 0,
        display: 'flex', alignItems: 'center', justifyContent: 'center',
        pointerEvents: 'none', zIndex: 1, overflow: 'hidden',
      }}>
        <span style={{
          fontSize: 96, fontWeight: 900, letterSpacing: '0.06em',
          textTransform: 'uppercase', color: PALETTE.ACCENT_LT,
          opacity: 0.05, transform: 'rotate(-15deg)', whiteSpace: 'nowrap',
          userSelect: 'none',
        }}>
          ADIM MÜŞAVİRLİK
        </span>
      </div>

      {/* ── Sol Panel: Çözüm (55%) ────────────────────── */}
      <div style={{
        width: '55%', height: '100%',
        background: BG_DARK,
        borderRight: `1px solid ${ACCENT}20`,
        display: 'flex', flexDirection: 'column',
        padding: '40px 36px',
        position: 'relative', zIndex: 2,
      }}>
        {/* Başlık */}
        <div style={{
          opacity: leftHeaderOpacity,
          display: 'flex', alignItems: 'center', gap: 12, marginBottom: 24,
        }}>
          <div style={{ width: 4, height: 28, borderRadius: 3, background: ACCENT }} />
          <span style={{
            fontSize: 13, fontWeight: 800, color: ACCENT,
            letterSpacing: 3, textTransform: 'uppercase' as const,
          }}>
            Çözüm
          </span>
        </div>

        {/* Adımlar */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: 14, flex: 1 }}>
          {steps.map((step, i) => (
            <SolutionStepItem
              key={i} step={step} index={i}
              frame={frame} totalSteps={steps.length} fps={fps}
            />
          ))}

          {/* Açıklama — çözüm sonunda */}
          {scene.explanation && (
            <div style={{
              opacity: interpolate(frame, [revealStart - 10, revealStart + 20], [0, 1], { extrapolateRight: 'clamp' }),
              background: `${ACCENT}0D`,
              border: `1px solid ${ACCENT}30`,
              borderLeft: `4px solid ${ACCENT}`,
              borderRadius: 10, padding: '14px 16px', marginTop: 4,
            }}>
              <p style={{ fontSize: 13, color: PALETTE.TEXT_MID, lineHeight: 1.7, margin: 0 }}>
                {scene.explanation}
              </p>
            </div>
          )}
        </div>

        {/* Alt: lesson adı */}
        {scene.title && (
          <div style={{
            marginTop: 'auto', paddingTop: 16,
            borderTop: `1px solid ${ACCENT}15`,
            opacity: 0.45,
          }}>
            <span style={{ fontSize: 11, color: PALETTE.TEXT_DIM, letterSpacing: 1 }}>
              {scene.title}
            </span>
          </div>
        )}
      </div>

      {/* ── Sağ Panel: Soru (45%) ─────────────────────── */}
      <div style={{
        width: '45%', height: '100%',
        background: BG_MID,
        display: 'flex', flexDirection: 'column',
        padding: '40px 32px',
        opacity: rightOpacity,
        position: 'relative', zIndex: 2,
      }}>
        {/* Soru numarası */}
        <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 20 }}>
          <div style={{
            background: ACCENT, color: '#fff',
            borderRadius: 24, padding: '5px 16px',
            fontSize: 13, fontWeight: 800,
          }}>
            {scene.question_number ?? 1}. SORU
          </div>
          {scene.total_questions && (
            <span style={{ color: PALETTE.TEXT_DIM, fontSize: 12 }}>
              / {scene.total_questions}
            </span>
          )}
        </div>

        {/* Soru metni */}
        <div style={{
          background: BG_CARD, borderRadius: 14,
          border: `1px solid ${ACCENT}18`,
          padding: '20px 22px', marginBottom: 20, flex: 'none',
        }}>
          <p style={{
            fontSize: 15, fontFamily: brand.font_heading, fontWeight: 600,
            color: '#FFFFFF', lineHeight: 1.7, margin: 0,
          }}>
            {scene.question_text}
          </p>
        </div>

        {/* Seçenekler */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
          {options.map((opt) => {
            const isCorrect = opt.label === scene.correct_label
            const showCorrect = isCorrect && scene.reveal_correct && correctReveal > 0.5

            return (
              <div key={opt.label} style={{
                display: 'flex', alignItems: 'flex-start', gap: 10,
                padding: '10px 14px', borderRadius: 10,
                background: showCorrect ? 'rgba(34,197,94,0.12)' : 'rgba(255,255,255,0.04)',
                border: `1.5px solid ${showCorrect ? PALETTE.CORRECT : ACCENT}${showCorrect ? '60' : '15'}`,
                transition: 'all 0.3s',
                opacity: showCorrect ? 1 : (correctReveal > 0.5 && isCorrect ? 1 : 0.85),
              }}>
                <div style={{
                  width: 26, height: 26, borderRadius: '50%', flexShrink: 0,
                  background: showCorrect ? PALETTE.CORRECT : `${ACCENT}20`,
                  border: `1.5px solid ${showCorrect ? PALETTE.CORRECT : ACCENT}`,
                  color: showCorrect ? '#fff' : ACCENT,
                  fontWeight: 800, fontSize: 12,
                  display: 'flex', alignItems: 'center', justifyContent: 'center',
                }}>
                  {showCorrect ? '✓' : opt.label}
                </div>
                <span style={{
                  fontSize: 13, color: showCorrect ? '#FFFFFF' : PALETTE.TEXT_MID,
                  lineHeight: 1.55, fontWeight: showCorrect ? 600 : 400,
                }}>
                  {opt.text}
                </span>
              </div>
            )
          })}
        </div>

        {/* Köşe imzası */}
        <div style={{
          position: 'absolute', bottom: 14, right: 18,
          fontSize: 11, fontWeight: 700, color: PALETTE.ACCENT_LT,
          opacity: 0.7, letterSpacing: '0.03em',
        }}>
          @adimmusavir
        </div>
      </div>

      {scene.tts_url && <Audio src={scene.tts_url} />}
    </div>
  )
}
