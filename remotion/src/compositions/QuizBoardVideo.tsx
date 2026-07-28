/**
 * QuizBoardVideo — 16:9 soru çözüm tahtası.
 *
 * Tasarım: Büyük marka filigranı arka planda (%85 yükseklik, düşük opaklık).
 * Soru üstte sabit, çözüm kutusu aşağı doğru adım adım dolup tamamlanır.
 *
 * Sahne tipleri:
 *   QuizBoardIntroScene    — animasyonlu başlık kartı
 *   QuizBoardQuestionScene — soru + şıklar (düşünme süresi)
 *   QuizBoardSolutionScene — soru sabit, çözüm kutusu aşağı dolar
 *   QuizBoardHighlightScene— altın kutu: anahtar kural / sınav ipucu
 *   QuizBoardOutroScene    — kapanış
 */
import { Audio, Img, interpolate, spring, useCurrentFrame, useVideoConfig } from 'remotion'
import { BrandConfig, Scene, StoryboardJSON } from '../types'
import { FPS, LESSON_PALETTE as L } from '../brand'

const NAVY  = '#0B2A4A'
const GOLD  = '#C9A96E'
const WHITE = '#FFFFFF'
const HEAD  = '"Playfair Display", serif'
const BODY  = '"Lato", sans-serif'
const MATH  = '"Noto Sans", "Lato", Arial, sans-serif'

// ── Filigran arka plan ────────────────────────────────────────
function Watermark({ logoUrl }: { logoUrl?: string }) {
  if (!logoUrl) return null
  return (
    <div style={{
      position: 'absolute', inset: 0,
      display: 'flex', alignItems: 'center', justifyContent: 'center',
      pointerEvents: 'none', zIndex: 0,
    }}>
      <Img
        src={logoUrl}
        style={{
          height: '85%', width: 'auto',
          objectFit: 'contain',
          opacity: 0.055,
          filter: 'grayscale(100%) brightness(2)',
        }}
      />
    </div>
  )
}

// ── QuizBoardIntroScene ───────────────────────────────────────
function QuizBoardIntroScene({ scene, brand }: { scene: Scene; brand: BrandConfig }) {
  const frame = useCurrentFrame()
  const { fps } = useVideoConfig()
  const total = Math.round((scene.duration_seconds ?? 8) * fps)

  const titleY = spring({ frame, fps, config: { damping: 18, mass: 0.7 } })
  const subtitleIn = interpolate(frame, [18, 36], [0, 1], { extrapolateRight: 'clamp' })
  const barGrow    = interpolate(frame, [10, 34], [0, 1], { extrapolateRight: 'clamp' })

  return (
    <div style={{
      width: '100%', height: '100%',
      background: NAVY,
      display: 'flex', flexDirection: 'column',
      alignItems: 'center', justifyContent: 'center',
      position: 'relative', overflow: 'hidden',
    }}>
      <Watermark logoUrl={brand.logo_url} />

      {/* Üst altın şerit */}
      <div style={{
        position: 'absolute', top: 0, left: 0, right: 0, height: 6,
        background: `linear-gradient(90deg, transparent, ${GOLD}, transparent)`,
        width: `${barGrow * 100}%`, zIndex: 2,
      }} />

      <div style={{ zIndex: 2, textAlign: 'center', padding: '0 120px' }}>
        {/* Rozet */}
        <div style={{
          display: 'inline-flex', alignItems: 'center', gap: 10,
          background: GOLD, borderRadius: 24, padding: '6px 22px', marginBottom: 28,
        }}>
          <span style={{ fontSize: 13, fontWeight: 900, color: NAVY, fontFamily: BODY, letterSpacing: 2 }}>
            SORU ÇÖZÜMÜ
          </span>
        </div>

        {/* Ana başlık */}
        <h1 style={{
          fontFamily: HEAD, fontSize: 86, fontWeight: 700, color: WHITE,
          lineHeight: 1.18, margin: '0 0 20px',
          transform: `translateY(${(1 - titleY) * 40}px)`,
          opacity: titleY,
        }}>
          {scene.title ?? 'Soru Çözümü'}
        </h1>

        {/* Alt başlık */}
        {scene.subtitle && (
          <p style={{
            fontFamily: BODY, fontSize: 32, color: `rgba(255,255,255,0.62)`,
            margin: 0, letterSpacing: 1, opacity: subtitleIn,
          }}>
            {scene.subtitle}
          </p>
        )}
      </div>

      {/* Alt altın çizgi */}
      <div style={{
        position: 'absolute', bottom: 0, left: 0, right: 0, height: 4,
        background: `linear-gradient(90deg, transparent, ${GOLD}, transparent)`,
        opacity: 0.6, zIndex: 2,
      }} />
      {scene.tts_url && <Audio src={scene.tts_url} />}
    </div>
  )
}

// ── QuizBoardQuestionScene ────────────────────────────────────
function QuizBoardQuestionScene({ scene, brand }: { scene: Scene; brand: BrandConfig }) {
  const frame = useCurrentFrame()
  const { fps } = useVideoConfig()

  const fadeIn = interpolate(frame, [0, 22], [0, 1], { extrapolateRight: 'clamp' })
  const slideY = interpolate(frame, [0, 22], [24, 0], { extrapolateRight: 'clamp' })
  const options = scene.options ?? []

  return (
    <div style={{
      width: '100%', height: '100%',
      background: '#F8FAFC',
      display: 'flex', flexDirection: 'column',
      position: 'relative', overflow: 'hidden',
    }}>
      <Watermark logoUrl={brand.logo_url} />

      {/* Üst lacivert şerit */}
      <div style={{ position: 'absolute', top: 0, left: 0, right: 0, height: 6, background: NAVY, zIndex: 3 }} />

      <div style={{
        zIndex: 2, flex: 1, display: 'flex', flexDirection: 'column',
        padding: '52px 80px 40px',
        opacity: fadeIn, transform: `translateY(${slideY}px)`,
      }}>
        {/* Soru etiketi */}
        <div style={{
          display: 'inline-flex', alignItems: 'center', gap: 8,
          background: NAVY, borderRadius: 20, padding: '5px 18px',
          alignSelf: 'flex-start', marginBottom: 24,
        }}>
          {scene.question_number && (
            <span style={{ fontSize: 13, fontWeight: 900, color: GOLD, fontFamily: BODY }}>
              {scene.question_number}.
            </span>
          )}
          <span style={{ fontSize: 13, fontWeight: 800, color: WHITE, fontFamily: BODY, letterSpacing: 1.5 }}>
            SORU
          </span>
          {scene.total_questions && (
            <span style={{ fontSize: 11, color: `rgba(255,255,255,0.5)`, fontFamily: BODY }}>
              / {scene.total_questions}
            </span>
          )}
        </div>

        {/* Soru metni */}
        <div style={{
          background: WHITE, border: `1.5px solid ${L.BORDER}`,
          borderLeft: `5px solid ${NAVY}`,
          borderRadius: 12, padding: '28px 36px', marginBottom: 28,
          boxShadow: '0 2px 20px rgba(11,42,74,0.06)',
        }}>
          <p style={{
            fontFamily: HEAD, fontSize: 46, fontWeight: 600,
            color: NAVY, lineHeight: 1.55, margin: 0,
          }}>
            {scene.question_text}
          </p>
        </div>

        {/* Şıklar */}
        {options.length > 0 && (
          <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
            {options.map((opt, i) => {
              const delay = i * 8
              const optIn = interpolate(frame, [delay + 10, delay + 28], [0, 1], { extrapolateRight: 'clamp' })
              return (
                <div key={opt.label} style={{
                  display: 'flex', alignItems: 'center', gap: 16,
                  opacity: optIn, transform: `translateX(${(1 - optIn) * 16}px)`,
                }}>
                  <div style={{
                    width: 38, height: 38, borderRadius: '50%', flexShrink: 0,
                    background: NAVY, color: WHITE,
                    fontWeight: 900, fontSize: 16, fontFamily: BODY,
                    display: 'flex', alignItems: 'center', justifyContent: 'center',
                  }}>
                    {opt.label}
                  </div>
                  <span style={{ fontSize: 32, color: L.DARK, fontFamily: MATH, lineHeight: 1.45 }}>
                    {opt.text}
                  </span>
                </div>
              )
            })}
          </div>
        )}
      </div>

      {/* Alt bar — marka */}
      <div style={{
        position: 'absolute', bottom: 0, left: 0, right: 0,
        height: 48, zIndex: 3,
        background: NAVY,
        display: 'flex', alignItems: 'center', justifyContent: 'flex-end',
        padding: '0 32px',
      }}>
        <span style={{ fontSize: 14, color: `rgba(255,255,255,0.55)`, fontFamily: BODY }}>
          {brand.handle ?? '@adimmusavir'}
        </span>
      </div>

      {scene.tts_url && <Audio src={scene.tts_url} />}
    </div>
  )
}

// ── QuizBoardSolutionScene ────────────────────────────────────
// Soru üstte sabit, çözüm kutusu aşağı doğru adım adım dolar.
function QuizBoardSolutionScene({ scene, brand }: { scene: Scene; brand: BrandConfig }) {
  const frame = useCurrentFrame()
  const { fps } = useVideoConfig()
  const total   = Math.round((scene.duration_seconds ?? 60) * fps)

  const steps   = scene.chalkboard_steps ?? []
  const options = scene.options ?? []
  const N       = steps.length

  // Soru bölümü yüksekliği
  const QUESTION_H = options.length > 0 ? '42%' : '32%'

  // Çözüm adımları reveal zamanlaması — toplam sürenin %80'i
  const usable = Math.floor(total * 0.80)
  const revealAt  = (i: number) => Math.floor((i / Math.max(N, 1)) * usable)

  // Doğru şık — sahne sonunun %88'inden itibaren
  const answerIn = interpolate(
    frame,
    [Math.floor(total * 0.88), Math.floor(total * 0.88) + 20],
    [0, 1], { extrapolateRight: 'clamp' },
  )
  const showAnswer = !!scene.correct_label && frame >= Math.floor(total * 0.88)

  const fadeIn = interpolate(frame, [0, 20], [0, 1], { extrapolateRight: 'clamp' })

  return (
    <div style={{
      width: '100%', height: '100%',
      background: '#F8FAFC',
      display: 'flex', flexDirection: 'column',
      position: 'relative', overflow: 'hidden',
    }}>
      <Watermark logoUrl={brand.logo_url} />

      {/* Üst lacivert şerit */}
      <div style={{ position: 'absolute', top: 0, left: 0, right: 0, height: 6, background: NAVY, zIndex: 3 }} />

      {/* Soru bölümü — sabit */}
      <div style={{
        height: QUESTION_H, flexShrink: 0,
        zIndex: 2, padding: '36px 80px 16px',
        background: '#F8FAFC',
        borderBottom: `2px solid rgba(11,42,74,0.12)`,
        opacity: fadeIn,
      }}>
        <div style={{ display: 'flex', alignItems: 'flex-start', gap: 16 }}>
          {/* Soru rozet */}
          {scene.question_number && (
            <div style={{
              width: 44, height: 44, borderRadius: '50%', flexShrink: 0,
              background: NAVY, color: GOLD,
              fontWeight: 900, fontSize: 18, fontFamily: BODY,
              display: 'flex', alignItems: 'center', justifyContent: 'center', marginTop: 4,
            }}>
              {scene.question_number}
            </div>
          )}
          <div style={{ flex: 1 }}>
            <p style={{
              fontFamily: HEAD, fontSize: 38, fontWeight: 600,
              color: NAVY, lineHeight: 1.5, margin: '0 0 14px',
            }}>
              {scene.question_text}
            </p>
            {/* Şıklar — yatay/kompakt */}
            {options.length > 0 && (
              <div style={{ display: 'flex', flexWrap: 'wrap', gap: '8px 20px' }}>
                {options.map(opt => {
                  const isCorrect = showAnswer && opt.label === scene.correct_label
                  return (
                    <div key={opt.label} style={{
                      display: 'flex', alignItems: 'center', gap: 8,
                      background: isCorrect ? L.GREEN_BG : 'rgba(11,42,74,0.05)',
                      border: `1.5px solid ${isCorrect ? L.GREEN : 'rgba(11,42,74,0.15)'}`,
                      borderRadius: 8, padding: '5px 14px',
                      transition: 'all 0.3s',
                    }}>
                      <span style={{
                        fontSize: 13, fontWeight: 900, color: isCorrect ? L.GREEN : NAVY,
                        fontFamily: BODY,
                      }}>
                        {opt.label})
                      </span>
                      <span style={{
                        fontSize: 22, color: isCorrect ? '#166534' : L.MID,
                        fontFamily: MATH, fontWeight: isCorrect ? 700 : 400,
                      }}>
                        {opt.text}
                      </span>
                    </div>
                  )
                })}
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Çözüm bölümü — adım adım dolar */}
      <div style={{
        flex: 1, zIndex: 2, padding: '20px 80px 56px',
        overflowY: 'hidden',
      }}>
        {/* Çözüm başlığı */}
        <div style={{
          display: 'flex', alignItems: 'center', gap: 10, marginBottom: 16,
        }}>
          <div style={{ width: 4, height: 22, background: GOLD, borderRadius: 2 }} />
          <span style={{ fontSize: 13, fontWeight: 800, color: NAVY, fontFamily: BODY, letterSpacing: 2 }}>
            ÇÖZÜM
          </span>
        </div>

        {/* Adımlar */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
          {steps.map((step, i) => {
            const rf = revealAt(i)
            const opacity = interpolate(frame, [rf, rf + 16], [0, 1], { extrapolateRight: 'clamp' })
            const tx      = interpolate(frame, [rf, rf + 16], [-12, 0], { extrapolateRight: 'clamp' })
            const isActive = frame >= rf && frame < revealAt(i + 1)

            const isAnswer  = step.step_type === 'answer' || step.step_type === 'verification'
            const isMistake = step.step_type === 'common_mistake'
            const isTip     = step.step_type === 'exam_tip'

            const accentColor = isMistake ? L.RED : isTip ? L.AMBER : isAnswer ? L.GREEN : NAVY

            return (
              <div key={i} style={{
                display: 'flex', alignItems: 'flex-start', gap: 12,
                opacity, transform: `translateX(${tx}px)`,
              }}>
                {/* Sol aksent */}
                <div style={{
                  width: 3, alignSelf: 'stretch', flexShrink: 0,
                  background: isActive ? accentColor : `${accentColor}40`,
                  borderRadius: 2, minHeight: 28,
                }} />
                <div style={{ flex: 1 }}>
                  {/* Etiket */}
                  {step.step_type && step.step_type !== 'solve' && (
                    <div style={{
                      fontSize: 10, fontWeight: 800, color: accentColor,
                      letterSpacing: 2, textTransform: 'uppercase' as const,
                      fontFamily: BODY, marginBottom: 3,
                    }}>
                      {step.step_type === 'verification' ? 'KONTROL'
                       : step.step_type === 'common_mistake' ? 'SIKÇA YAPILAN HATA'
                       : step.step_type === 'exam_tip' ? 'SINAV İPUCU'
                       : step.step_type === 'answer' ? 'CEVAP'
                       : ''}
                    </div>
                  )}
                  <div style={{
                    fontSize: isActive ? 44 : 36,
                    fontFamily: MATH,
                    fontWeight: isActive ? 700 : 500,
                    color: accentColor,
                    lineHeight: 1.45,
                    background: isActive && isAnswer ? L.GREEN_BG : 'transparent',
                    borderRadius: isAnswer ? 6 : 0,
                    padding: isAnswer ? '3px 8px' : 0,
                    display: 'inline-block',
                  }}>
                    {step.board_text}
                  </div>
                  {step.annotation && isActive && (
                    <div style={{
                      fontSize: 22, color: L.MID, fontFamily: BODY,
                      marginTop: 4, lineHeight: 1.5, fontStyle: 'italic',
                    }}>
                      ↳ {step.annotation}
                    </div>
                  )}
                </div>
              </div>
            )
          })}
        </div>

        {/* Doğru cevap kutusu */}
        {showAnswer && scene.answer && (
          <div style={{
            marginTop: 18,
            display: 'flex', alignItems: 'center', gap: 14,
            background: L.GREEN_BG, border: `2px solid ${L.GREEN}`,
            borderRadius: 12, padding: '12px 24px',
            opacity: answerIn, transform: `scale(${0.94 + 0.06 * answerIn})`,
          }}>
            <span style={{ fontSize: 18 }}>✅</span>
            <span style={{
              fontSize: 44, color: '#166534', fontFamily: MATH,
              fontWeight: 900,
            }}>
              {scene.answer}
            </span>
          </div>
        )}
      </div>

      {/* Alt bar */}
      <div style={{
        position: 'absolute', bottom: 0, left: 0, right: 0,
        height: 44, zIndex: 3, background: NAVY,
        display: 'flex', alignItems: 'center', justifyContent: 'flex-end',
        padding: '0 32px',
      }}>
        <span style={{ fontSize: 13, color: `rgba(255,255,255,0.5)`, fontFamily: BODY }}>
          {brand.handle ?? '@adimmusavir'}
        </span>
      </div>

      {scene.tts_url && <Audio src={scene.tts_url} />}
    </div>
  )
}

// ── QuizBoardHighlightScene ───────────────────────────────────
// Altın çerçeveli anahtar kural veya sınav ipucu — sahne tam ekran
function QuizBoardHighlightScene({ scene, brand }: { scene: Scene; brand: BrandConfig }) {
  const frame = useCurrentFrame()
  const { fps } = useVideoConfig()

  const cardScale = spring({ frame, fps, config: { damping: 16, mass: 0.6 } })
  const textIn    = interpolate(frame, [14, 32], [0, 1], { extrapolateRight: 'clamp' })

  return (
    <div style={{
      width: '100%', height: '100%',
      background: NAVY,
      display: 'flex', alignItems: 'center', justifyContent: 'center',
      position: 'relative', overflow: 'hidden',
    }}>
      <Watermark logoUrl={brand.logo_url} />

      {/* Altın çerçeve kutu */}
      <div style={{
        zIndex: 2, maxWidth: 1280, width: '88%',
        border: `3px solid ${GOLD}`,
        borderRadius: 20, padding: '56px 72px',
        background: 'rgba(201,169,110,0.06)',
        transform: `scale(${0.88 + 0.12 * cardScale})`,
        textAlign: 'center',
      }}>
        {/* Etiket */}
        <div style={{
          display: 'inline-flex', alignItems: 'center', gap: 8,
          background: GOLD, borderRadius: 20, padding: '4px 18px', marginBottom: 28,
        }}>
          <span style={{ fontSize: 12, fontWeight: 900, color: NAVY, fontFamily: BODY, letterSpacing: 2 }}>
            {scene.key_point ? 'ANAHTAR KURAL' : 'SINAV İPUCU'}
          </span>
        </div>

        {/* Ana metin */}
        <p style={{
          fontFamily: HEAD, fontSize: 58, fontWeight: 600, color: WHITE,
          lineHeight: 1.45, margin: '0 0 24px',
          opacity: textIn, transform: `translateY(${(1 - textIn) * 16}px)`,
        }}>
          {scene.key_point ?? scene.exam_tip ?? scene.title}
        </p>

        {/* Alt açıklama */}
        {scene.explanation && (
          <p style={{
            fontFamily: BODY, fontSize: 28, color: `rgba(255,255,255,0.62)`,
            lineHeight: 1.6, margin: 0,
            opacity: interpolate(frame, [24, 40], [0, 1], { extrapolateRight: 'clamp' }),
          }}>
            {scene.explanation}
          </p>
        )}
      </div>

      {/* Alt altın çizgi */}
      <div style={{
        position: 'absolute', bottom: 0, left: 0, right: 0, height: 4,
        background: `linear-gradient(90deg, transparent, ${GOLD}, transparent)`,
        zIndex: 3,
      }} />

      {scene.tts_url && <Audio src={scene.tts_url} />}
    </div>
  )
}

// ── QuizBoardOutroScene ───────────────────────────────────────
function QuizBoardOutroScene({ scene, brand }: { scene: Scene; brand: BrandConfig }) {
  const frame = useCurrentFrame()
  const { fps } = useVideoConfig()

  const logoScale = spring({ frame, fps, config: { damping: 14, mass: 0.5 } })
  const textIn    = interpolate(frame, [18, 38], [0, 1], { extrapolateRight: 'clamp' })
  const lineGrow  = interpolate(frame, [10, 38], [0, 1], { extrapolateRight: 'clamp' })

  return (
    <div style={{
      width: '100%', height: '100%',
      background: NAVY,
      display: 'flex', flexDirection: 'column',
      alignItems: 'center', justifyContent: 'center',
      position: 'relative', overflow: 'hidden',
    }}>
      <Watermark logoUrl={brand.logo_url} />

      <div style={{ zIndex: 2, textAlign: 'center', padding: '0 120px' }}>
        {/* Logo */}
        {brand.logo_url && (
          <div style={{
            marginBottom: 28,
            transform: `scale(${0.85 + 0.15 * logoScale})`,
          }}>
            <Img
              src={brand.logo_url}
              style={{ height: 72, width: 'auto', objectFit: 'contain' }}
            />
          </div>
        )}

        {/* Altın ayırıcı */}
        <div style={{
          height: 2, background: GOLD, borderRadius: 1,
          width: `${lineGrow * 260}px`, margin: '0 auto 28px',
        }} />

        <h2 style={{
          fontFamily: HEAD, fontSize: 62, fontWeight: 700, color: WHITE,
          margin: '0 0 16px', opacity: textIn,
          transform: `translateY(${(1 - textIn) * 18}px)`,
        }}>
          {scene.title ?? 'Soru Çözüldü'}
        </h2>

        {scene.subtitle && (
          <p style={{
            fontFamily: BODY, fontSize: 28, color: `rgba(255,255,255,0.6)`,
            margin: '0 0 32px',
            opacity: interpolate(frame, [24, 42], [0, 1], { extrapolateRight: 'clamp' }),
          }}>
            {scene.subtitle}
          </p>
        )}

        {/* CTA */}
        {(scene.cta_text ?? brand.handle) && (
          <div style={{
            display: 'inline-flex', alignItems: 'center', gap: 10,
            background: GOLD, borderRadius: 24, padding: '8px 28px',
            opacity: interpolate(frame, [30, 48], [0, 1], { extrapolateRight: 'clamp' }),
          }}>
            <span style={{ fontSize: 18, fontWeight: 800, color: NAVY, fontFamily: BODY }}>
              {scene.cta_text ?? brand.handle ?? '@adimmusavir'}
            </span>
          </div>
        )}
      </div>

      {/* Alt altın çizgi */}
      <div style={{
        position: 'absolute', bottom: 0, left: 0, right: 0, height: 4,
        background: `linear-gradient(90deg, transparent, ${GOLD}, transparent)`,
        opacity: 0.6, zIndex: 3,
      }} />

      {scene.tts_url && <Audio src={scene.tts_url} />}
    </div>
  )
}

// ── Sahne yönlendirici ────────────────────────────────────────
function QuizBoardSceneDispatcher({ scene, brand }: { scene: Scene; brand: BrandConfig }) {
  switch (scene.component) {
    case 'QuizBoardIntroScene':     return <QuizBoardIntroScene scene={scene} brand={brand} />
    case 'QuizBoardQuestionScene':  return <QuizBoardQuestionScene scene={scene} brand={brand} />
    case 'QuizBoardSolutionScene':  return <QuizBoardSolutionScene scene={scene} brand={brand} />
    case 'QuizBoardHighlightScene': return <QuizBoardHighlightScene scene={scene} brand={brand} />
    case 'QuizBoardOutroScene':     return <QuizBoardOutroScene scene={scene} brand={brand} />
    default:
      return <QuizBoardSolutionScene scene={scene} brand={brand} />
  }
}

// ── Frame hesabı ─────────────────────────────────────────────
export function getQuizBoardTotalFrames(storyboard?: StoryboardJSON): number {
  if (!storyboard?.scenes?.length) return 300
  const total = storyboard.scenes.reduce((s, sc) => s + (sc.duration_seconds ?? 10), 0)
  return Math.max(Math.round(total * FPS), 60)
}

// ── Ana kompozisyon ───────────────────────────────────────────
interface QuizBoardProps { storyboard: StoryboardJSON }

export function QuizBoardVideo({ storyboard }: QuizBoardProps) {
  const frame = useCurrentFrame()

  const brand: BrandConfig = {
    primary_color:    storyboard.brand?.primary_color    ?? '#0B2A4A',
    secondary_color:  storyboard.brand?.secondary_color  ?? '#C9A96E',
    background_color: storyboard.brand?.background_color ?? '#F8FAFC',
    font_heading:     storyboard.brand?.font_heading      ?? 'Playfair Display',
    font_body:        storyboard.brand?.font_body         ?? 'Lato',
    logo_url:         storyboard.brand?.logo_url,
    handle:           storyboard.brand?.handle            ?? '@adimmusavir',
  }

  // Aktif sahneyi bul
  let elapsed = 0
  let activeScene: Scene | null = null
  let sceneStart = 0

  for (const scene of storyboard.scenes) {
    const dur = Math.round((scene.duration_seconds ?? 10) * FPS)
    if (frame < elapsed + dur) {
      activeScene = scene
      sceneStart  = elapsed
      break
    }
    elapsed += dur
  }

  if (!activeScene) {
    activeScene = storyboard.scenes[storyboard.scenes.length - 1]
    sceneStart  = elapsed - Math.round((activeScene?.duration_seconds ?? 10) * FPS)
  }

  return (
    <div style={{ width: '100%', height: '100%', overflow: 'hidden' }}>
      {activeScene && (
        <QuizBoardSceneDispatcher scene={activeScene} brand={brand} />
      )}
    </div>
  )
}
