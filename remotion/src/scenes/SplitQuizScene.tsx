/**
 * SplitQuizScene — 16:9 yatay bölünmüş soru çözümü
 * Sol bölüm (%58): context_text (referans metin) + soru kökü + A-E seçenekler
 * Sağ bölüm (%42): öğretmen adım adım çözümü, sık hata, doğru cevap
 *
 * Min font boyutları (spec):
 *   context_text: 38px | question_text: 42px | options: 34px | çözüm: 38px
 */
import { interpolate, useCurrentFrame, useVideoConfig, Audio } from 'remotion'
import { BrandConfig, Scene, SolutionStep } from '../types'
import { PALETTE, LESSON_PALETTE as L } from '../brand'
import { BrandWatermark } from '../components/BrandWatermark'

const ACCENT = PALETTE.ACCENT  // #2B7FE0
const WHITE  = '#FFFFFF'

interface Props { scene: Scene; brand: BrandConfig }

// ── Çözüm adımı (sağ panel) ──────────────────────────────────
function StepRow({ step, index, frame, totalSteps }: {
  step: SolutionStep; index: number; frame: number; totalSteps: number
}) {
  const revealAt = Math.round((index / Math.max(totalSteps, 1)) * 160)
  const opacity  = interpolate(frame, [revealAt, revealAt + 18], [0, 1], { extrapolateRight: 'clamp' })
  const y        = interpolate(frame, [revealAt, revealAt + 18], [12, 0],  { extrapolateRight: 'clamp' })

  if (step.type === 'journal_entry') {
    return (
      <div style={{ opacity, transform: `translateY(${y}px)` }}>
        <div style={{
          background: `${ACCENT}08`, border: `1px solid ${ACCENT}30`,
          borderRadius: 8, overflow: 'hidden',
        }}>
          <div style={{
            background: `${ACCENT}18`, padding: '5px 12px',
            display: 'flex', justifyContent: 'space-between',
            color: ACCENT, fontWeight: 700, fontSize: 11, letterSpacing: 2,
          }}>
            <span>BORÇ</span><span>ALACAK</span>
          </div>
          {step.debit && (
            <div style={{ display: 'flex', justifyContent: 'space-between', padding: '7px 12px', borderBottom: `1px solid ${ACCENT}15` }}>
              <span style={{ color: L.DARK, fontSize: 14 }}>{step.debit.name}</span>
              <span style={{ color: L.GREEN, fontWeight: 700 }}>{step.debit.amount.toLocaleString('tr-TR')} ₺</span>
            </div>
          )}
          {step.credits?.map((cr, i) => (
            <div key={i} style={{ display: 'flex', justifyContent: 'space-between', padding: '7px 12px 7px 24px' }}>
              <span style={{ color: L.MID, fontSize: 14 }}>{cr.name}</span>
              <span style={{ color: ACCENT, fontWeight: 700 }}>{cr.amount.toLocaleString('tr-TR')} ₺</span>
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
          background: `${ACCENT}08`, border: `1px solid ${ACCENT}25`,
          borderRadius: 8, padding: '8px 12px',
          display: 'flex', alignItems: 'baseline', gap: 8, flexWrap: 'wrap' as const,
        }}>
          <span style={{ color: L.MID, fontSize: 32 }}>{step.formula}</span>
          {step.result && <span style={{ color: ACCENT, fontWeight: 800, fontSize: 38 }}>{step.result}</span>}
        </div>
      </div>
    )
  }

  if (step.type === 'note') {
    return (
      <div style={{ opacity, transform: `translateY(${y}px)`, display: 'flex', gap: 8, alignItems: 'flex-start' }}>
        <div style={{ width: 6, height: 6, borderRadius: '50%', background: ACCENT, marginTop: 14, flexShrink: 0 }} />
        <span style={{ fontSize: 34, color: L.MID, lineHeight: 1.55 }}>{step.text}</span>
      </div>
    )
  }

  // text (varsayılan)
  return (
    <div style={{ opacity, transform: `translateY(${y}px)`, display: 'flex', gap: 10, alignItems: 'flex-start' }}>
      <div style={{
        width: 24, height: 24, borderRadius: '50%', flexShrink: 0,
        background: ACCENT, display: 'flex', alignItems: 'center', justifyContent: 'center',
        fontSize: 12, fontWeight: 800, color: WHITE, marginTop: 5,
      }}>
        {index + 1}
      </div>
      <span style={{ fontSize: 38, color: L.DARK, lineHeight: 1.6 }}>{step.text}</span>
    </div>
  )
}

// ── Ana bileşen ───────────────────────────────────────────────
export function SplitQuizScene({ scene, brand }: Props) {
  const frame = useCurrentFrame()
  const { fps } = useVideoConfig()

  const steps   = scene.solution_steps ?? []
  const options = scene.options ?? []

  const rawSec  = scene.duration_seconds as number | string | undefined | null
  const safeSec = (typeof rawSec === 'number' && isFinite(rawSec) && rawSec > 0) ? rawSec
                : (typeof rawSec === 'string' && Number(rawSec) > 0) ? Number(rawSec) : 45
  const totalFrames = Math.round(safeSec * fps)

  const leftOpacity   = interpolate(frame, [0, 20],  [0, 1], { extrapolateRight: 'clamp' })
  const rightOpacity  = interpolate(frame, [8, 28],  [0, 1], { extrapolateRight: 'clamp' })
  const revealStart   = Math.round(totalFrames * 0.80)
  const correctReveal = interpolate(frame, [revealStart, revealStart + 25], [0, 1], { extrapolateRight: 'clamp' })

  // 5 seçenek → 3 sütun (3+2), 4 seçenek → 2 sütun (2+2), diğer → 2 sütun
  const gridCols = options.length === 5 ? 'repeat(3, 1fr)' : 'repeat(2, 1fr)'

  const audioSrc = scene.tts_url ?? scene.audio_url ?? undefined

  return (
    <div style={{
      width: '100%', height: '100%',
      background: WHITE,
      display: 'flex', flexDirection: 'row',
      fontFamily: brand.font_body, overflow: 'hidden', position: 'relative',
    }}>
      <BrandWatermark theme="light" opacity={0.04} logoUrl={brand.logo_url} />

      {/* ── Sol Panel: Soru (58%) ────────────────────────────── */}
      <div style={{
        width: '58%', height: '100%',
        background: WHITE,
        display: 'flex', flexDirection: 'column',
        padding: '28px 36px',
        borderRight: `2.5px solid ${ACCENT}`,
        position: 'relative', zIndex: 2,
        opacity: leftOpacity,
      }}>
        <div style={{ position: 'absolute', top: 0, left: 0, right: 0, height: 5, background: L.NAVY }} />

        {/* Soru numarası rozeti */}
        <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 16 }}>
          <div style={{
            background: L.NAVY, color: WHITE,
            borderRadius: 20, padding: '4px 16px',
            fontSize: 13, fontWeight: 800,
          }}>
            {scene.question_number ?? 1}. SORU
          </div>
          {scene.total_questions && (
            <span style={{ color: L.DIM, fontSize: 12 }}>/ {scene.total_questions}</span>
          )}
        </div>

        {/* REFERANS METİN (context_text) — yoksa görünmez */}
        {scene.context_text && scene.context_text.trim() && (
          <div style={{
            background: 'rgba(11,42,74,0.04)',
            border: `1.5px solid ${L.NAVY}30`,
            borderLeft: `4px solid ${L.NAVY}`,
            borderRadius: 8, padding: '12px 16px', marginBottom: 14,
          }}>
            <div style={{
              fontSize: 10, fontWeight: 800, color: L.NAVY,
              letterSpacing: 2, textTransform: 'uppercase' as const,
              fontFamily: 'Lato', marginBottom: 6,
            }}>
              REFERANS METİN
            </div>
            <p style={{
              fontSize: 38, color: L.DARK,
              lineHeight: 1.6, margin: 0,
              fontFamily: brand.font_heading, fontStyle: 'italic',
            }}>
              {scene.context_text}
            </p>
          </div>
        )}

        {/* Soru kökü */}
        <div style={{
          border: `1.5px solid ${ACCENT}`,
          boxShadow: `0 0 0 3px rgba(43,127,224,0.07)`,
          borderRadius: 10, padding: '14px 18px', marginBottom: 18,
          background: WHITE,
        }}>
          <p style={{
            fontSize: 42, fontFamily: brand.font_heading, fontWeight: 600,
            color: L.DARK, lineHeight: 1.55, margin: 0,
          }}>
            {scene.question_text}
          </p>
        </div>

        {/* Seçenekler — ızgara */}
        <div style={{
          display: 'grid',
          gridTemplateColumns: gridCols,
          gap: 8,
        }}>
          {options.map((opt) => {
            const isCorrect   = opt.label === scene.correct_label
            const showCorrect = isCorrect && scene.reveal_correct && correctReveal > 0.5
            return (
              <div key={opt.label} style={{
                display: 'flex', alignItems: 'flex-start', gap: 10,
                padding: '10px 12px', borderRadius: 8,
                background: showCorrect ? L.RED_BG : '#F8FAFC',
                border: `1.5px solid ${showCorrect ? L.RED : L.BORDER}`,
              }}>
                <div style={{
                  width: 28, height: 28, borderRadius: '50%', flexShrink: 0,
                  background: showCorrect ? L.RED : ACCENT,
                  color: WHITE, fontWeight: 800, fontSize: 13,
                  display: 'flex', alignItems: 'center', justifyContent: 'center',
                  marginTop: 3,
                }}>
                  {opt.label}
                </div>
                <span style={{
                  fontSize: 34, color: showCorrect ? L.RED : L.MID,
                  lineHeight: 1.45, fontWeight: showCorrect ? 700 : 400,
                }}>
                  {opt.text}
                </span>
              </div>
            )
          })}
        </div>

        {/* Alt: ders adı + marka imzası */}
        <div style={{ marginTop: 'auto', paddingTop: 10, display: 'flex', justifyContent: 'space-between', alignItems: 'flex-end' }}>
          {scene.title && <span style={{ fontSize: 11, color: L.DIM }}>{scene.title}</span>}
          <span style={{ fontSize: 11, fontWeight: 700, color: ACCENT, opacity: 0.8, marginLeft: 'auto' }}>
            {brand.handle ?? '@adimmusavir'}
          </span>
        </div>
      </div>

      {/* ── Sağ Panel: Çözüm (42%) ──────────────────────────── */}
      <div style={{
        width: '42%', height: '100%',
        background: '#EEF4FF',
        display: 'flex', flexDirection: 'column',
        padding: '28px 30px',
        opacity: rightOpacity,
        position: 'relative', zIndex: 2,
      }}>
        <div style={{ position: 'absolute', top: 0, left: 0, right: 0, height: 5, background: ACCENT }} />

        {/* Başlık */}
        <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 20 }}>
          <div style={{ width: 4, height: 24, borderRadius: 2, background: L.NAVY }} />
          <span style={{ fontSize: 13, fontWeight: 800, color: L.NAVY, letterSpacing: 3, textTransform: 'uppercase' as const }}>
            Öğretmen Çözümü
          </span>
        </div>

        {/* Adımlar */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: 14, flex: 1 }}>
          {steps.map((step, i) => (
            <StepRow key={i} step={step} index={i} frame={frame} totalSteps={steps.length} />
          ))}

          {/* Açıklama */}
          {scene.explanation && (
            <div style={{
              opacity: interpolate(frame, [revealStart - 10, revealStart + 15], [0, 1], { extrapolateRight: 'clamp' }),
              background: `${ACCENT}0A`, border: `1px solid ${ACCENT}30`,
              borderLeft: `4px solid ${ACCENT}`, borderRadius: 8, padding: '10px 12px', marginTop: 4,
            }}>
              <p style={{ fontSize: 32, color: L.MID, lineHeight: 1.65, margin: 0 }}>{scene.explanation}</p>
            </div>
          )}
        </div>

        {/* Doğru cevap kutucuğu — sahnenin son %20'sinde belirir */}
        {scene.reveal_correct && scene.correct_label && correctReveal > 0.1 && (
          <div style={{
            marginTop: 12,
            background: L.GREEN_BG, border: `2px solid ${L.GREEN}`,
            borderRadius: 10, padding: '10px 18px',
            display: 'flex', alignItems: 'center', gap: 10,
            opacity: correctReveal, transform: `scale(${0.94 + 0.06 * correctReveal})`,
          }}>
            <span style={{ fontSize: 20 }}>✅</span>
            <span style={{ fontSize: 38, color: L.GREEN, fontWeight: 900 }}>
              Doğru Cevap: {scene.correct_label}
            </span>
          </div>
        )}
      </div>

      {audioSrc && <Audio src={audioSrc} />}
    </div>
  )
}
