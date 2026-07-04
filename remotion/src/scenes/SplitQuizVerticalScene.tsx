/**
 * SplitQuizVerticalScene — 9:16 dikey bölünmüş ekran (Shorts/Reels)
 * Üst panel: soru + şıklar (sabit)
 * Alt panel: çözüm adımları sırayla açılır
 * Uzun çözümler için part_index / total_parts alanları ile "Bölüm 1/2" desteği
 */
import { interpolate, useCurrentFrame, useVideoConfig, Audio } from 'remotion'
import { BrandConfig, Scene } from '../types'
import { PALETTE } from '../brand'

const ACCENT = PALETTE.ACCENT
const BG_DARK = PALETTE.BG_DARK
const BG_MID = PALETTE.BG_MID
const BG_CARD = PALETTE.BG_CARD

interface Props { scene: Scene; brand: BrandConfig }

export function SplitQuizVerticalScene({ scene, brand }: Props) {
  const frame = useCurrentFrame()
  const { fps } = useVideoConfig()

  const steps = scene.solution_steps ?? []
  const options = scene.options ?? []
  const totalFrames = Math.round(scene.duration_seconds * fps)
  const revealStart = Math.round(totalFrames * 0.78)

  const topOpacity = interpolate(frame, [0, 18], [0, 1], { extrapolateRight: 'clamp' })
  const bottomOpacity = interpolate(frame, [12, 30], [0, 1], { extrapolateRight: 'clamp' })
  const correctReveal = interpolate(frame, [revealStart, revealStart + 22], [0, 1], { extrapolateRight: 'clamp' })

  return (
    <div style={{
      width: '100%', height: '100%',
      background: BG_DARK, display: 'flex', flexDirection: 'column',
      fontFamily: brand.font_body, overflow: 'hidden', position: 'relative',
    }}>
      {/* Ambient */}
      <div style={{
        position: 'absolute', top: -80, left: '50%', transform: 'translateX(-50%)',
        width: 600, height: 400, borderRadius: '50%',
        background: `radial-gradient(ellipse, ${ACCENT}0A 0%, transparent 65%)`,
        pointerEvents: 'none',
      }} />

      {/* Top accent bar */}
      <div style={{ height: 4, background: `linear-gradient(90deg, transparent, ${ACCENT}, transparent)`, opacity: 0.7 }} />

      {/* ── Üst Panel: Soru (42%) ─────────────────────── */}
      <div style={{
        height: '42%', flexShrink: 0,
        background: BG_MID, borderBottom: `1px solid ${ACCENT}25`,
        padding: '24px 28px', display: 'flex', flexDirection: 'column',
        opacity: topOpacity,
      }}>
        {/* Soru numarası + bölüm */}
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 14 }}>
          <div style={{
            background: ACCENT, color: '#fff',
            borderRadius: 20, padding: '4px 14px',
            fontSize: 12, fontWeight: 800,
          }}>
            {scene.question_number ?? 1}. Soru
          </div>
          {scene.total_questions && (
            <span style={{ color: PALETTE.TEXT_DIM, fontSize: 11 }}>
              {scene.question_number} / {scene.total_questions}
            </span>
          )}
        </div>

        {/* Soru metni — compacted */}
        <p style={{
          fontSize: 16, fontFamily: brand.font_heading, fontWeight: 600,
          color: '#FFFFFF', lineHeight: 1.55, margin: '0 0 12px',
          display: '-webkit-box', WebkitLineClamp: 3, WebkitBoxOrient: 'vertical' as const,
          overflow: 'hidden',
        }}>
          {scene.question_text}
        </p>

        {/* Seçenekler — iki sütun */}
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 6, flex: 1, alignContent: 'start' }}>
          {options.map((opt) => {
            const isCorrect = opt.label === scene.correct_label
            const showCorrect = isCorrect && scene.reveal_correct && correctReveal > 0.5
            return (
              <div key={opt.label} style={{
                display: 'flex', gap: 7, alignItems: 'center',
                padding: '7px 10px', borderRadius: 8,
                background: showCorrect ? 'rgba(34,197,94,0.15)' : 'rgba(255,255,255,0.04)',
                border: `1px solid ${showCorrect ? PALETTE.CORRECT : ACCENT}${showCorrect ? '55' : '15'}`,
              }}>
                <div style={{
                  width: 20, height: 20, borderRadius: '50%', flexShrink: 0,
                  background: showCorrect ? PALETTE.CORRECT : `${ACCENT}20`,
                  color: showCorrect ? '#fff' : ACCENT,
                  fontWeight: 800, fontSize: 10,
                  display: 'flex', alignItems: 'center', justifyContent: 'center',
                }}>
                  {showCorrect ? '✓' : opt.label}
                </div>
                <span style={{
                  fontSize: 11, color: showCorrect ? '#fff' : PALETTE.TEXT_MID,
                  lineHeight: 1.4, fontWeight: showCorrect ? 600 : 400,
                  overflow: 'hidden', display: '-webkit-box',
                  WebkitLineClamp: 2, WebkitBoxOrient: 'vertical' as const,
                }}>
                  {opt.text}
                </span>
              </div>
            )
          })}
        </div>
      </div>

      {/* ── Alt Panel: Çözüm (58%) ───────────────────── */}
      <div style={{
        flex: 1, padding: '20px 28px 24px',
        display: 'flex', flexDirection: 'column',
        opacity: bottomOpacity,
      }}>
        {/* Başlık */}
        <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 16 }}>
          <div style={{ width: 3, height: 22, borderRadius: 2, background: ACCENT }} />
          <span style={{
            fontSize: 11, fontWeight: 800, color: ACCENT,
            letterSpacing: 3, textTransform: 'uppercase' as const,
          }}>
            Çözüm
          </span>
        </div>

        {/* Adımlar */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: 10, flex: 1 }}>
          {steps.map((step, i) => {
            const revealAt = Math.round((i / Math.max(steps.length, 1)) * 160)
            const sOpacity = interpolate(frame, [revealAt, revealAt + 18], [0, 1], { extrapolateRight: 'clamp' })
            const sY = interpolate(frame, [revealAt, revealAt + 18], [12, 0], { extrapolateRight: 'clamp' })

            if (step.type === 'formula') {
              return (
                <div key={i} style={{ opacity: sOpacity, transform: `translateY(${sY}px)` }}>
                  <div style={{
                    background: `${ACCENT}0A`, border: `1px solid ${ACCENT}20`,
                    borderRadius: 8, padding: '8px 12px',
                    display: 'flex', gap: 8, alignItems: 'baseline', flexWrap: 'wrap' as const,
                  }}>
                    <span style={{ color: PALETTE.TEXT_MID, fontSize: 12 }}>{step.formula}</span>
                    {step.result && <span style={{ color: ACCENT, fontWeight: 800, fontSize: 14 }}>{step.result}</span>}
                  </div>
                </div>
              )
            }
            if (step.type === 'journal_entry') {
              return (
                <div key={i} style={{ opacity: sOpacity, transform: `translateY(${sY}px)` }}>
                  <div style={{
                    background: `${ACCENT}08`, border: `1px solid ${ACCENT}25`,
                    borderRadius: 8, overflow: 'hidden', fontSize: 11,
                  }}>
                    <div style={{
                      background: `${ACCENT}18`, padding: '4px 10px',
                      display: 'flex', justifyContent: 'space-between',
                      color: PALETTE.ACCENT_LT, fontWeight: 700, fontSize: 10, letterSpacing: 2,
                    }}>
                      <span>BORÇ</span><span>ALACAK</span>
                    </div>
                    {step.debit && (
                      <div style={{ display: 'flex', justifyContent: 'space-between', padding: '6px 10px', borderBottom: `1px solid ${ACCENT}12` }}>
                        <span style={{ color: '#fff' }}>{step.debit.name}</span>
                        <span style={{ color: PALETTE.CORRECT, fontWeight: 700 }}>{step.debit.amount.toLocaleString('tr-TR')} ₺</span>
                      </div>
                    )}
                    {step.credits?.map((cr, ci) => (
                      <div key={ci} style={{ display: 'flex', justifyContent: 'space-between', padding: '6px 10px 6px 20px' }}>
                        <span style={{ color: PALETTE.TEXT_MID }}>{cr.name}</span>
                        <span style={{ color: ACCENT, fontWeight: 700 }}>{cr.amount.toLocaleString('tr-TR')} ₺</span>
                      </div>
                    ))}
                  </div>
                </div>
              )
            }
            // text / note
            return (
              <div key={i} style={{ opacity: sOpacity, transform: `translateY(${sY}px)`, display: 'flex', gap: 8, alignItems: 'flex-start' }}>
                <div style={{
                  width: 18, height: 18, borderRadius: '50%', flexShrink: 0,
                  background: `${ACCENT}20`, border: `1px solid ${ACCENT}`,
                  color: ACCENT, fontWeight: 800, fontSize: 9,
                  display: 'flex', alignItems: 'center', justifyContent: 'center',
                }}>
                  {i + 1}
                </div>
                <span style={{ fontSize: 12, color: '#fff', lineHeight: 1.6 }}>{step.text}</span>
              </div>
            )
          })}

          {/* Açıklama */}
          {scene.explanation && (
            <div style={{
              opacity: interpolate(frame, [revealStart - 5, revealStart + 18], [0, 1], { extrapolateRight: 'clamp' }),
              background: `${ACCENT}0A`, border: `1px solid ${ACCENT}25`,
              borderLeft: `3px solid ${ACCENT}`, borderRadius: 8, padding: '10px 12px',
            }}>
              <p style={{ fontSize: 11, color: PALETTE.TEXT_MID, lineHeight: 1.6, margin: 0 }}>
                {scene.explanation}
              </p>
            </div>
          )}
        </div>

        {/* Marka imzası */}
        <div style={{ marginTop: 'auto', paddingTop: 10, textAlign: 'center' }}>
          <span style={{ fontSize: 10, color: PALETTE.TEXT_DIM, letterSpacing: 1.5 }}>@adimmusavir</span>
        </div>
      </div>

      {scene.tts_url && <Audio src={scene.tts_url} />}
    </div>
  )
}
