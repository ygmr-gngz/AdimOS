/**
 * ChalkboardSolutionScene — Öğretmen tahtasında soru çözermiş gibi pedagojik sahne.
 *
 * Sol panel (38%): Soru kartı, verilenler, istenen, yöntem
 * Sağ panel (62%): Tahta — adımlar sırayla canlanır; aktif satır tam opaklık, geçenler soluk
 * Alt bar: common_mistake (kırmızı) veya exam_tip (amber) veya ikisi sırayla
 * Final: answer (yeşil kutu) sahnenin son %10'unda görünür
 *
 * Font fallback zinciri matematik sembolleri için Noto Sans kullanır.
 */
import { interpolate, useCurrentFrame, useVideoConfig, Audio } from 'remotion'
import { Scene, BrandConfig, ChalkboardStep } from '../types'
import { LESSON_PALETTE as L } from '../brand'
import { BrandWatermark } from '../components/BrandWatermark'

interface Props { scene: Scene; brand: BrandConfig }

// ── Renk haritası ─────────────────────────────────────────────
const STEP_COLORS: Record<string, string> = {
  navy:  L.NAVY,
  blue:  L.BLUE,
  red:   L.RED,
  green: L.GREEN,
  amber: L.AMBER,
  gold:  L.GOLD,
}

function stepColor(step: ChalkboardStep): string {
  if (step.step_type === 'common_mistake') return L.RED
  if (step.step_type === 'verification')   return L.GREEN
  if (step.step_type === 'answer')         return L.GREEN
  if (step.step_type === 'exam_tip')       return L.AMBER
  if (step.color)                          return STEP_COLORS[step.color] ?? L.NAVY
  return L.NAVY
}

// ── Matematik-uyumlu font zinciri ────────────────────────────
const MATH_FONT = '"Noto Sans", "Lato", "DejaVu Sans", Arial, sans-serif'
const HEAD_FONT = '"Playfair Display", "Noto Sans", serif'

// ── Sol panel: soru kartı ────────────────────────────────────
function QuestionPanel({ scene, brand, fadeIn }: {
  scene: Scene; brand: BrandConfig; fadeIn: number
}) {
  const options = scene.options ?? []
  return (
    <div style={{
      width: '38%', height: '100%',
      background: L.BG,
      display: 'flex', flexDirection: 'column',
      padding: '40px 32px',
      borderRight: `3px solid ${L.NAVY}`,
      position: 'relative', zIndex: 2,
      opacity: fadeIn,
    }}>
      {/* Üst lacivert şerit */}
      <div style={{ position: 'absolute', top: 0, left: 0, right: 0, height: 5, background: L.NAVY }} />

      {/* Soru etiketi */}
      <div style={{
        display: 'inline-flex', alignItems: 'center', gap: 8,
        background: L.NAVY, borderRadius: 20,
        padding: '5px 16px', marginBottom: 14, alignSelf: 'flex-start',
      }}>
        {scene.question_number && (
          <span style={{ fontSize: 12, fontWeight: 900, color: L.GOLD, fontFamily: 'Lato', letterSpacing: 1 }}>
            {scene.question_number}.
          </span>
        )}
        <span style={{ fontSize: 12, fontWeight: 800, color: '#fff', fontFamily: 'Lato', letterSpacing: 1.5 }}>
          SORU
        </span>
      </div>

      {/* Referans metin — context_text */}
      {scene.context_text && scene.context_text.trim() && (
        <div style={{
          background: 'rgba(11,42,74,0.04)',
          border: `1.5px solid ${L.NAVY}30`,
          borderLeft: `3px solid ${L.NAVY}`,
          borderRadius: 8, padding: '9px 12px', marginBottom: 12,
        }}>
          <div style={{
            fontSize: 9, fontWeight: 800, color: L.NAVY, letterSpacing: 2,
            textTransform: 'uppercase' as const, fontFamily: 'Lato', marginBottom: 4,
          }}>
            REFERANS METİN
          </div>
          <p style={{
            fontSize: 26, color: L.DARK, lineHeight: 1.55, margin: 0,
            fontFamily: HEAD_FONT, fontStyle: 'italic',
          }}>
            {scene.context_text}
          </p>
        </div>
      )}

      {/* Soru metni */}
      {scene.question_text && (
        <div style={{
          background: L.NAVY_DIM, border: `1.5px solid ${L.BORDER}`,
          borderRadius: 12, padding: '12px 14px', marginBottom: 14,
        }}>
          <p style={{
            fontSize: 38, fontFamily: HEAD_FONT, fontWeight: 600,
            color: L.DARK, lineHeight: 1.5, margin: 0,
          }}>
            {scene.question_text}
          </p>
        </div>
      )}

      {/* Seçenekler (A-E) */}
      {options.length > 0 && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 6, marginBottom: 14 }}>
          {options.map(opt => (
            <div key={opt.label} style={{
              display: 'flex', alignItems: 'flex-start', gap: 8,
            }}>
              <div style={{
                width: 20, height: 20, borderRadius: '50%', flexShrink: 0,
                background: L.NAVY, color: '#fff',
                fontWeight: 800, fontSize: 10,
                display: 'flex', alignItems: 'center', justifyContent: 'center',
                marginTop: 2,
              }}>
                {opt.label}
              </div>
              <span style={{ fontSize: 22, color: L.MID, lineHeight: 1.45 }}>{opt.text}</span>
            </div>
          ))}
        </div>
      )}

      {/* Verilenler */}
      {scene.given && scene.given.length > 0 && (
        <div style={{ marginBottom: 18 }}>
          <div style={{
            fontSize: 11, fontWeight: 800, color: L.NAVY, letterSpacing: 2,
            textTransform: 'uppercase', marginBottom: 8, fontFamily: 'Lato',
          }}>
            VERİLENLER
          </div>
          <div style={{
            background: 'rgba(43,127,224,0.07)', border: '1px solid rgba(43,127,224,0.20)',
            borderRadius: 10, padding: '12px 16px',
            display: 'flex', flexDirection: 'column', gap: 7,
          }}>
            {scene.given.map((g, i) => (
              <div key={i} style={{ display: 'flex', alignItems: 'baseline', gap: 10 }}>
                <div style={{
                  width: 6, height: 6, borderRadius: 3, background: L.BLUE,
                  flexShrink: 0, marginTop: 2,
                }} />
                <span style={{
                  fontSize: 34, color: L.DARK, fontFamily: MATH_FONT,
                  fontWeight: 700, lineHeight: 1.45,
                }}>
                  {g}
                </span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* İstenen */}
      {scene.asked && (
        <div style={{ marginBottom: 18 }}>
          <div style={{
            fontSize: 11, fontWeight: 800, color: L.NAVY, letterSpacing: 2,
            textTransform: 'uppercase', marginBottom: 8, fontFamily: 'Lato',
          }}>
            İSTENEN
          </div>
          <div style={{
            background: L.GOLD_DIM, border: `1px solid ${L.GOLD}`,
            borderRadius: 10, padding: '10px 16px',
          }}>
            <span style={{
              fontSize: 36, color: L.NAVY, fontFamily: MATH_FONT,
              fontWeight: 800,
            }}>
              {scene.asked}
            </span>
          </div>
        </div>
      )}

      {/* Yöntem */}
      {scene.method_text && (
        <div>
          <div style={{
            fontSize: 11, fontWeight: 800, color: L.NAVY, letterSpacing: 2,
            textTransform: 'uppercase', marginBottom: 8, fontFamily: 'Lato',
          }}>
            YÖNTEM
          </div>
          <p style={{
            fontSize: 14, color: L.MID, lineHeight: 1.65, margin: 0,
            fontFamily: 'Lato',
          }}>
            {scene.method_text}
          </p>
        </div>
      )}

      {/* Alt: ders adı */}
      <div style={{ marginTop: 'auto', paddingTop: 16 }}>
        {scene.title && (
          <span style={{ fontSize: 11, color: L.DIM, fontFamily: 'Lato' }}>
            {scene.title}
          </span>
        )}
        <div style={{
          fontSize: 11, fontWeight: 700, color: L.NAVY,
          fontFamily: 'Lato', opacity: 0.6, marginTop: 4,
        }}>
          {brand.handle ?? '@adimmusavir'}
        </div>
      </div>
    </div>
  )
}

// ── Sağ panel: tahta ─────────────────────────────────────────
function ChalkboardPanel({ steps, frame, totalFrames, brand }: {
  steps: ChalkboardStep[]
  frame: number
  totalFrames: number
  brand: BrandConfig
}) {
  // "Solve" ve diğer normal adımlar — common_mistake/exam_tip/answer hariç
  const boardSteps = steps.filter(
    s => s.step_type !== 'common_mistake' && s.step_type !== 'exam_tip' && s.step_type !== 'answer',
  )
  const N = boardSteps.length
  if (N === 0) return null

  // Her adım için reveal frame (eşit dağılım, max %85 zaman)
  const usableFrames = Math.floor(totalFrames * 0.85)
  const revealFrame  = (i: number) => Math.floor((i / N) * usableFrames)
  const nextReveal   = (i: number) => i < N - 1 ? revealFrame(i + 1) : usableFrames

  return (
    <div style={{
      flex: 1, height: '100%',
      background: '#F9FAFB',
      display: 'flex', flexDirection: 'column',
      padding: '40px 44px 32px',
      position: 'relative', zIndex: 2,
    }}>
      {/* Tahta başlığı */}
      <div style={{
        display: 'flex', alignItems: 'center', gap: 12, marginBottom: 28,
      }}>
        <div style={{ width: 5, height: 28, borderRadius: 3, background: L.NAVY }} />
        <span style={{
          fontSize: 14, fontWeight: 800, color: L.NAVY,
          fontFamily: 'Lato', letterSpacing: 3, textTransform: 'uppercase',
        }}>
          Çözüm
        </span>
      </div>

      {/* Adımlar */}
      <div style={{ display: 'flex', flexDirection: 'column', gap: 18, flex: 1 }}>
        {boardSteps.map((step, i) => {
          const rf = revealFrame(i)
          const nr = nextReveal(i)
          const opacity = interpolate(frame, [rf, rf + 18], [0, 1], { extrapolateRight: 'clamp' })
          const tx      = interpolate(frame, [rf, rf + 18], [-14, 0], { extrapolateRight: 'clamp' })
          const isActive = frame >= rf && frame < nr
          const isPast   = frame >= nr
          const color    = stepColor(step)
          const isSpecial = step.step_type === 'verification'

          // "Tahta yazısı" — aktif satırın altında büyüyen çizgi
          const lineGrow = interpolate(frame, [rf, rf + 22], [0, 1], { extrapolateRight: 'clamp' })

          return (
            <div key={i} style={{
              opacity: opacity * (isPast ? 0.65 : 1),
              transform: `translateX(${tx}px)`,
            }}>
              <div style={{
                display: 'flex', alignItems: 'flex-start', gap: 14,
              }}>
                {/* Sol aksent çizgisi */}
                <div style={{
                  width: 3, flexShrink: 0,
                  alignSelf: 'stretch',
                  background: isActive ? color : (isPast ? L.BORDER : 'transparent'),
                  borderRadius: 2,
                  transition: 'background 0.2s',
                }} />

                <div style={{ flex: 1 }}>
                  {/* Adım etiketi */}
                  {step.step_type && step.step_type !== 'solve' && (
                    <div style={{
                      fontSize: 10, fontWeight: 800, color: color,
                      letterSpacing: 1.5, textTransform: 'uppercase',
                      fontFamily: 'Lato', marginBottom: 4,
                    }}>
                      {step.step_type === 'verification' ? 'KONTROL' :
                       step.step_type === 'given'        ? 'VERİLEN' :
                       step.step_type === 'asked'        ? 'İSTENEN' :
                       step.step_type === 'method'       ? 'YÖNTEM'  : ''}
                    </div>
                  )}

                  {/* Tahta metni */}
                  <div style={{
                    fontSize: isActive ? 58 : 46,
                    fontFamily: MATH_FONT,
                    fontWeight: isActive ? 700 : 600,
                    color: isActive ? color : (isPast ? L.MID : color),
                    lineHeight: 1.4,
                    letterSpacing: 0.5,
                    background: isSpecial && isActive
                      ? 'rgba(34,197,94,0.08)'
                      : 'transparent',
                    borderRadius: isSpecial ? 6 : 0,
                    padding: isSpecial ? '4px 8px' : 0,
                    display: 'inline-block',
                  }}>
                    {step.board_text}
                  </div>

                  {/* Tahta yazısı alt çizgi animasyonu (sadece aktif adım) */}
                  {isActive && (
                    <div style={{
                      height: 2,
                      width: `${lineGrow * 100}%`,
                      background: `linear-gradient(90deg, ${color}, transparent)`,
                      borderRadius: 1, marginTop: 3, opacity: 0.4,
                    }} />
                  )}

                  {/* Açıklama notu */}
                  {step.annotation && isActive && (
                    <div style={{
                      fontSize: 13, color: L.MID, fontFamily: 'Lato',
                      marginTop: 6, lineHeight: 1.55, fontStyle: 'italic',
                      opacity: interpolate(frame, [rf + 14, rf + 28], [0, 1], { extrapolateRight: 'clamp' }),
                    }}>
                      ↳ {step.annotation}
                    </div>
                  )}
                </div>
              </div>
            </div>
          )
        })}
      </div>
    </div>
  )
}

// ── Ana bileşen ───────────────────────────────────────────────
export function ChalkboardSolutionScene({ scene, brand }: Props) {
  const frame      = useCurrentFrame()
  const { fps }    = useVideoConfig()
  const totalFrames = Math.round(scene.duration_seconds * fps)
  const steps      = scene.chalkboard_steps ?? []

  const fadeIn     = interpolate(frame, [0, 20], [0, 1], { extrapolateRight: 'clamp' })

  // Alt bar: common_mistake %70'den itibaren, exam_tip %82'den, answer %90'dan
  const mistakeIn  = interpolate(frame, [Math.floor(totalFrames * 0.70), Math.floor(totalFrames * 0.70) + 20], [0, 1], { extrapolateRight: 'clamp' })
  const tipIn      = interpolate(frame, [Math.floor(totalFrames * 0.82), Math.floor(totalFrames * 0.82) + 18], [0, 1], { extrapolateRight: 'clamp' })
  const answerIn   = interpolate(frame, [Math.floor(totalFrames * 0.90), Math.floor(totalFrames * 0.90) + 15], [0, 1], { extrapolateRight: 'clamp' })

  const showMistake = !!scene.common_mistake && frame >= Math.floor(totalFrames * 0.70)
  const showTip     = !!scene.exam_tip       && frame >= Math.floor(totalFrames * 0.82)
  const showAnswer  = !!scene.answer         && frame >= Math.floor(totalFrames * 0.90)

  return (
    <div style={{
      width: '100%', height: '100%',
      background: L.BG,
      display: 'flex', flexDirection: 'column',
      fontFamily: MATH_FONT,
      overflow: 'hidden', position: 'relative',
    }}>
      {/* Marka filigranı */}
      <BrandWatermark theme="light" opacity={0.04} logoUrl={brand.logo_url} />

      {/* Üst lacivert şerit */}
      <div style={{ position: 'absolute', top: 0, left: 0, right: 0, height: 5, background: L.NAVY, zIndex: 10 }} />
      {/* Alt altın şerit */}
      <div style={{
        position: 'absolute', bottom: 0, left: 0, right: 0, height: 3, zIndex: 10,
        background: `linear-gradient(90deg, transparent, ${L.GOLD} 25%, ${L.GOLD} 75%, transparent)`,
        opacity: 0.7,
      }} />

      {/* Ana satır: sol + sağ panel */}
      <div style={{ display: 'flex', flex: 1, overflow: 'hidden' }}>
        <QuestionPanel scene={scene} brand={brand} fadeIn={fadeIn} />
        <ChalkboardPanel steps={steps} frame={frame} totalFrames={totalFrames} brand={brand} />
      </div>

      {/* Alt bilgi barı — common_mistake / exam_tip / answer */}
      {(showMistake || showTip || showAnswer) && (
        <div style={{
          borderTop: `1px solid ${L.BORDER}`,
          padding: '14px 40px',
          display: 'flex', gap: 16, alignItems: 'center',
          background: L.BG, zIndex: 5, minHeight: 72,
        }}>
          {showMistake && (
            <div style={{
              display: 'flex', alignItems: 'center', gap: 10, flex: 1,
              opacity: mistakeIn, transform: `translateY(${(1 - mistakeIn) * 8}px)`,
            }}>
              <span style={{ fontSize: 16 }}>⚠️</span>
              <span style={{
                fontSize: 22, color: L.RED, fontFamily: 'Lato',
                fontWeight: 700, lineHeight: 1.45,
              }}>
                {scene.common_mistake}
              </span>
            </div>
          )}
          {showTip && (
            <div style={{
              display: 'flex', alignItems: 'center', gap: 10, flex: 1,
              opacity: tipIn, transform: `translateY(${(1 - tipIn) * 8}px)`,
            }}>
              <span style={{ fontSize: 16 }}>💡</span>
              <span style={{
                fontSize: 22, color: L.AMBER, fontFamily: 'Lato',
                fontWeight: 700, lineHeight: 1.45,
              }}>
                {scene.exam_tip}
              </span>
            </div>
          )}
          {showAnswer && (
            <div style={{
              display: 'flex', alignItems: 'center', gap: 12,
              background: L.GREEN_BG, border: `2px solid ${L.GREEN}`,
              borderRadius: 10, padding: '8px 20px',
              opacity: answerIn, transform: `scale(${0.92 + 0.08 * answerIn})`,
            }}>
              <span style={{ fontSize: 14 }}>✅</span>
              <span style={{
                fontSize: 52, color: '#166534', fontFamily: MATH_FONT,
                fontWeight: 900, letterSpacing: 0.5,
              }}>
                {scene.answer}
              </span>
            </div>
          )}
        </div>
      )}

      {scene.tts_url && <Audio src={scene.tts_url} />}
    </div>
  )
}
