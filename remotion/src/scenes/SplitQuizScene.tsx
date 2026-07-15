/**
 * SplitQuizScene — 16:9 yatay bölünmüş ekran soru çözümü (referans format)
 * Sol panel (55%): soru metni + yatay şık satırı
 * Sağ panel (45%): çözüm adımları animasyonlu açılır
 * Doğru şık: kırmızı vurgu | Arka plan: beyaz | Aksent: marka mavisi
 */
import { interpolate, useCurrentFrame, useVideoConfig, Audio } from 'remotion'
import { BrandConfig, Scene, SolutionStep } from '../types'
import { PALETTE } from '../brand'
import { BrandWatermark } from '../components/BrandWatermark'

const ACCENT      = PALETTE.ACCENT        // #2B7FE0
const WHITE       = '#FFFFFF'
const PANEL_R_BG  = '#EEF4FF'            // hafif mavi tint — sağ panel
const TEXT_DARK   = '#0B1E3C'
const TEXT_MID    = '#475569'
const TEXT_DIM    = '#94A3B8'
const BORDER      = '#CBD5E1'
const RED_CORRECT = '#EF4444'
const RED_BG      = 'rgba(239,68,68,0.10)'

interface Props { scene: Scene; brand: BrandConfig }

// ── Çözüm adımı ───────────────────────────────────────────────
function SolutionStepItem({ step, index, frame, totalSteps }: {
  step: SolutionStep
  index: number
  frame: number
  totalSteps: number
}) {
  const revealAt = Math.round((index / Math.max(totalSteps, 1)) * 180)
  const opacity = interpolate(frame, [revealAt, revealAt + 20], [0, 1], { extrapolateRight: 'clamp' })
  const y = interpolate(frame, [revealAt, revealAt + 20], [14, 0], { extrapolateRight: 'clamp' })

  if (step.type === 'journal_entry') {
    return (
      <div style={{ opacity, transform: `translateY(${y}px)` }}>
        <div style={{
          background: 'rgba(43,127,224,0.05)',
          border: `1px solid ${ACCENT}30`,
          borderRadius: 10, overflow: 'hidden', fontSize: 13,
        }}>
          <div style={{
            background: `${ACCENT}15`, padding: '6px 14px',
            display: 'flex', justifyContent: 'space-between',
            color: ACCENT, fontWeight: 700, fontSize: 11,
            letterSpacing: 2, textTransform: 'uppercase' as const,
          }}>
            <span>BORÇ</span><span>ALACAK</span>
          </div>
          {step.debit && (
            <div style={{ display: 'flex', justifyContent: 'space-between', padding: '8px 14px', borderBottom: `1px solid ${ACCENT}15` }}>
              <span style={{ color: TEXT_DARK, fontSize: 13 }}>
                {step.debit.code && <span style={{ color: TEXT_DIM, marginRight: 6 }}>{step.debit.code}</span>}
                {step.debit.name}
              </span>
              <span style={{ color: '#059669', fontWeight: 700, fontVariantNumeric: 'tabular-nums' as const }}>
                {step.debit.amount.toLocaleString('tr-TR')} ₺
              </span>
            </div>
          )}
          {step.credits?.map((cr, i) => (
            <div key={i} style={{ display: 'flex', justifyContent: 'space-between', padding: '8px 14px 8px 28px', borderBottom: i < (step.credits!.length - 1) ? `1px solid ${ACCENT}10` : 'none' }}>
              <span style={{ color: TEXT_MID, fontSize: 13 }}>
                {cr.code && <span style={{ color: TEXT_DIM, marginRight: 6 }}>{cr.code}</span>}
                {cr.name}
              </span>
              <span style={{ color: ACCENT, fontWeight: 700, fontVariantNumeric: 'tabular-nums' as const }}>
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
          background: 'rgba(43,127,224,0.05)', border: `1px solid ${ACCENT}25`,
          borderRadius: 10, padding: '10px 14px',
          display: 'flex', alignItems: 'baseline', gap: 10, flexWrap: 'wrap' as const,
        }}>
          <span style={{ color: TEXT_MID, fontSize: 14 }}>{step.formula}</span>
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
          <div style={{ width: 6, height: 6, borderRadius: '50%', background: ACCENT, marginTop: 8, flexShrink: 0 }} />
          <span style={{ fontSize: 13, color: TEXT_MID, lineHeight: 1.6 }}>{step.text}</span>
        </div>
      </div>
    )
  }

  // text (default)
  return (
    <div style={{ opacity, transform: `translateY(${y}px)` }}>
      <div style={{ display: 'flex', gap: 10, alignItems: 'flex-start' }}>
        <div style={{
          width: 22, height: 22, borderRadius: '50%', flexShrink: 0,
          background: ACCENT,
          display: 'flex', alignItems: 'center', justifyContent: 'center',
          fontSize: 11, fontWeight: 800, color: WHITE,
        }}>
          {index + 1}
        </div>
        <span style={{ fontSize: 14, color: TEXT_DARK, lineHeight: 1.65 }}>{step.text}</span>
      </div>
    </div>
  )
}

// ── Ana bileşen ───────────────────────────────────────────────
export function SplitQuizScene({ scene, brand }: Props) {
  const frame = useCurrentFrame()
  const { fps } = useVideoConfig()

  const steps    = scene.solution_steps ?? []
  const options  = scene.options ?? []
  const totalFrames = Math.round(scene.duration_seconds * fps)

  const leftOpacity  = interpolate(frame, [0, 20],  [0, 1], { extrapolateRight: 'clamp' })
  const rightOpacity = interpolate(frame, [8, 28],  [0, 1], { extrapolateRight: 'clamp' })

  const revealStart  = Math.round(totalFrames * 0.78)
  const correctReveal = interpolate(frame, [revealStart, revealStart + 25], [0, 1], { extrapolateRight: 'clamp' })

  return (
    <div style={{
      width: '100%', height: '100%',
      background: WHITE,
      display: 'flex', flexDirection: 'row',
      fontFamily: brand.font_body, overflow: 'hidden', position: 'relative',
    }}>
      {/* Marka filigranı */}
      <BrandWatermark theme="light" opacity={0.045} />

      {/* ── Sol Panel: Soru (55%) ───────────────────────────── */}
      <div style={{
        width: '55%', height: '100%',
        background: WHITE,
        display: 'flex', flexDirection: 'column',
        padding: '36px 40px',
        borderRight: `2px solid ${ACCENT}`,
        position: 'relative', zIndex: 2,
        opacity: leftOpacity,
      }}>
        {/* Üst aksent çizgisi (çift kenarlık efekti) */}
        <div style={{ position: 'absolute', top: 0, left: 0, right: 0, height: 4, background: ACCENT }} />

        {/* Soru numarası */}
        <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 18 }}>
          <div style={{
            background: ACCENT, color: WHITE,
            borderRadius: 24, padding: '5px 18px',
            fontSize: 13, fontWeight: 800,
          }}>
            {scene.question_number ?? 1}. SORU
          </div>
          {scene.total_questions && (
            <span style={{ color: TEXT_DIM, fontSize: 12 }}>/ {scene.total_questions}</span>
          )}
        </div>

        {/* Soru metni — çift kenarlıklı kart */}
        <div style={{
          border: `1.5px solid ${ACCENT}`,
          boxShadow: `0 0 0 4px rgba(43,127,224,0.08)`,
          borderRadius: 12,
          padding: '18px 20px', marginBottom: 24,
          background: WHITE,
        }}>
          <p style={{
            fontSize: 16, fontFamily: brand.font_heading, fontWeight: 600,
            color: TEXT_DARK, lineHeight: 1.7, margin: 0,
          }}>
            {scene.question_text}
          </p>
        </div>

        {/* Şıklar — yatay satır, 4 seçenek yan yana */}
        <div style={{ display: 'flex', gap: 10 }}>
          {options.map((opt) => {
            const isCorrect   = opt.label === scene.correct_label
            const showCorrect = isCorrect && scene.reveal_correct && correctReveal > 0.5

            return (
              <div key={opt.label} style={{
                flex: 1,
                display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 7,
                padding: '12px 8px', borderRadius: 10,
                background: showCorrect ? RED_BG : '#F8FAFC',
                border: `1.5px solid ${showCorrect ? RED_CORRECT : BORDER}`,
                textAlign: 'center' as const,
              }}>
                <div style={{
                  width: 28, height: 28, borderRadius: '50%',
                  background: showCorrect ? RED_CORRECT : ACCENT,
                  color: WHITE,
                  fontWeight: 800, fontSize: 13,
                  display: 'flex', alignItems: 'center', justifyContent: 'center',
                  flexShrink: 0,
                }}>
                  {opt.label}
                </div>
                <span style={{
                  fontSize: 12, color: showCorrect ? RED_CORRECT : TEXT_MID,
                  lineHeight: 1.45, fontWeight: showCorrect ? 700 : 400,
                  display: '-webkit-box', WebkitLineClamp: 3,
                  WebkitBoxOrient: 'vertical' as const,
                  overflow: 'hidden',
                }}>
                  {opt.text}
                </span>
              </div>
            )
          })}
        </div>
      </div>

      {/* ── Sağ Panel: Çözüm (45%) ──────────────────────────── */}
      <div style={{
        width: '45%', height: '100%',
        background: PANEL_R_BG,
        display: 'flex', flexDirection: 'column',
        padding: '36px 32px',
        opacity: rightOpacity,
        position: 'relative', zIndex: 2,
      }}>
        {/* Üst aksent çizgisi */}
        <div style={{ position: 'absolute', top: 0, left: 0, right: 0, height: 4, background: ACCENT }} />

        {/* Başlık */}
        <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 22 }}>
          <div style={{ width: 4, height: 26, borderRadius: 3, background: ACCENT }} />
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
              frame={frame} totalSteps={steps.length}
            />
          ))}

          {/* Açıklama — çözüm sonunda belirir */}
          {scene.explanation && (
            <div style={{
              opacity: interpolate(frame, [revealStart - 10, revealStart + 20], [0, 1], { extrapolateRight: 'clamp' }),
              background: 'rgba(43,127,224,0.06)',
              border: `1px solid ${ACCENT}30`,
              borderLeft: `4px solid ${ACCENT}`,
              borderRadius: 10, padding: '12px 14px', marginTop: 4,
            }}>
              <p style={{ fontSize: 13, color: TEXT_MID, lineHeight: 1.7, margin: 0 }}>
                {scene.explanation}
              </p>
            </div>
          )}
        </div>

        {/* Alt: ders adı + marka imzası */}
        <div style={{ marginTop: 'auto', paddingTop: 14, display: 'flex', justifyContent: 'space-between', alignItems: 'flex-end' }}>
          {scene.title && (
            <span style={{ fontSize: 11, color: TEXT_DIM, letterSpacing: 1, opacity: 0.7 }}>
              {scene.title}
            </span>
          )}
          <span style={{ fontSize: 11, fontWeight: 700, color: ACCENT, opacity: 0.8, letterSpacing: '0.03em', marginLeft: 'auto' }}>
            @adimmusavir
          </span>
        </div>
      </div>

      {scene.tts_url && <Audio src={scene.tts_url} />}
    </div>
  )
}
