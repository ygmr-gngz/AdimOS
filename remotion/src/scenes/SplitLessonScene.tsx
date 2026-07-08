/**
 * SplitLessonScene — 16:9 yatay bölünmüş ekran konu anlatımı (SplitQuizScene kardeşi)
 * Sol panel (55%): konu başlığı + tanım kartı + anahtar maddeler
 * Sağ panel (45%): örnek / önemli / sınav notu — animasyonlu açılır
 * Arka plan: beyaz | Aksent: marka mavisi (+ onemli → amber, sinav_notu → teal)
 */
import { interpolate, useCurrentFrame, useVideoConfig, Audio } from 'remotion'
import { BrandConfig, Scene } from '../types'
import { PALETTE } from '../brand'

const ACCENT     = PALETTE.ACCENT        // #2B7FE0
const WHITE      = '#FFFFFF'
const PANEL_R_BG = '#EEF4FF'
const TEXT_DARK  = '#0B1E3C'
const TEXT_MID   = '#475569'
const TEXT_DIM   = '#94A3B8'
const BORDER     = '#CBD5E1'

const RIGHT_PANEL_CONFIG = {
  ornek:      { label: 'ÖRNEK',      accent: ACCENT,     bg: 'rgba(43,127,224,0.06)',  border: 'rgba(43,127,224,0.30)' },
  onemli:     { label: 'ÖNEMLİ',    accent: '#F59E0B',  bg: 'rgba(245,158,11,0.07)', border: 'rgba(245,158,11,0.35)' },
  sinav_notu: { label: 'SINAV NOTU', accent: '#0D9488',  bg: 'rgba(13,148,136,0.07)', border: 'rgba(13,148,136,0.35)' },
} as const

type RightPanelType = keyof typeof RIGHT_PANEL_CONFIG

interface Props { scene: Scene; brand: BrandConfig }

export function SplitLessonScene({ scene, brand }: Props) {
  const frame = useCurrentFrame()
  const { fps } = useVideoConfig()

  const totalFrames  = Math.round(scene.duration_seconds * fps)
  const keyPoints    = scene.key_points ?? []
  const rightType    = (scene.right_panel_type ?? 'ornek') as RightPanelType
  const cfg          = RIGHT_PANEL_CONFIG[rightType] ?? RIGHT_PANEL_CONFIG.ornek
  const panelAccent  = cfg.accent

  const leftOpacity  = interpolate(frame, [0, 20],  [0, 1], { extrapolateRight: 'clamp' })
  const rightOpacity = interpolate(frame, [8, 28],  [0, 1], { extrapolateRight: 'clamp' })

  // Anahtar maddeler sırayla belirir
  const bulletRevealAt = (i: number) =>
    Math.round((i / Math.max(keyPoints.length, 1)) * 160) + 20

  // Sağ panel içeriği ve açıklama belirme zamanı
  const rightContentAt = 40
  const explanationAt  = Math.round(totalFrames * 0.65)

  return (
    <div style={{
      width: '100%', height: '100%',
      background: WHITE,
      display: 'flex', flexDirection: 'row',
      fontFamily: brand.font_body, overflow: 'hidden', position: 'relative',
    }}>
      {/* Logo filigran — merkezi, %5 opaklık */}
      <div style={{
        position: 'absolute', inset: 0,
        display: 'flex', alignItems: 'center', justifyContent: 'center',
        pointerEvents: 'none', zIndex: 1, overflow: 'hidden',
      }}>
        <span style={{
          fontSize: 96, fontWeight: 900, letterSpacing: '0.06em',
          textTransform: 'uppercase', color: ACCENT,
          opacity: 0.05, transform: 'rotate(-15deg)', whiteSpace: 'nowrap',
          userSelect: 'none',
        }}>
          ADIM MÜŞAVİRLİK
        </span>
      </div>

      {/* ── Sol Panel: Konu Anlatımı (55%) ─────────────────────── */}
      <div style={{
        width: '55%', height: '100%',
        background: WHITE,
        display: 'flex', flexDirection: 'column',
        padding: '36px 40px',
        borderRight: `2px solid ${ACCENT}`,
        position: 'relative', zIndex: 2,
        opacity: leftOpacity,
      }}>
        {/* Üst aksent çizgisi */}
        <div style={{ position: 'absolute', top: 0, left: 0, right: 0, height: 4, background: ACCENT }} />

        {/* Slayt numarası rozeti */}
        <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 18 }}>
          <div style={{
            background: ACCENT, color: WHITE,
            borderRadius: 24, padding: '5px 18px',
            fontSize: 13, fontWeight: 800,
          }}>
            {scene.question_number ?? 1}. KONU
          </div>
          {scene.total_questions && (
            <span style={{ color: TEXT_DIM, fontSize: 12 }}>/ {scene.total_questions}</span>
          )}
        </div>

        {/* Tanım kartı — çift çerçeve (SplitQuizScene soru kartı ile aynı) */}
        <div style={{
          border: `1.5px solid ${ACCENT}`,
          boxShadow: `0 0 0 4px rgba(43,127,224,0.08)`,
          borderRadius: 12,
          padding: '18px 20px', marginBottom: 22,
          background: WHITE,
        }}>
          <p style={{
            fontSize: 15, fontFamily: brand.font_heading, fontWeight: 600,
            color: TEXT_DARK, lineHeight: 1.7, margin: 0,
          }}>
            {scene.question_text}
          </p>
        </div>

        {/* Anahtar maddeler — sıralı bullet list */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: 10, flex: 1 }}>
          {keyPoints.map((point, i) => {
            const at = bulletRevealAt(i)
            const opacity = interpolate(frame, [at, at + 18], [0, 1], { extrapolateRight: 'clamp' })
            const y       = interpolate(frame, [at, at + 18], [12, 0],  { extrapolateRight: 'clamp' })
            return (
              <div key={i} style={{ opacity, transform: `translateY(${y}px)`, display: 'flex', gap: 10, alignItems: 'flex-start' }}>
                <div style={{
                  width: 22, height: 22, borderRadius: '50%', flexShrink: 0,
                  background: ACCENT,
                  display: 'flex', alignItems: 'center', justifyContent: 'center',
                  fontSize: 11, fontWeight: 800, color: WHITE, marginTop: 1,
                }}>
                  {i + 1}
                </div>
                <span style={{ fontSize: 14, color: TEXT_DARK, lineHeight: 1.65 }}>{point}</span>
              </div>
            )
          })}
        </div>
      </div>

      {/* ── Sağ Panel: Örnek / Önemli / Sınav Notu (45%) ────────── */}
      <div style={{
        width: '45%', height: '100%',
        background: PANEL_R_BG,
        display: 'flex', flexDirection: 'column',
        padding: '36px 32px',
        opacity: rightOpacity,
        position: 'relative', zIndex: 2,
      }}>
        {/* Üst aksent çizgisi (panelAccent ile) */}
        <div style={{ position: 'absolute', top: 0, left: 0, right: 0, height: 4, background: panelAccent }} />

        {/* Başlık */}
        <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 22 }}>
          <div style={{ width: 4, height: 26, borderRadius: 3, background: panelAccent }} />
          <span style={{
            fontSize: 13, fontWeight: 800, color: panelAccent,
            letterSpacing: 3, textTransform: 'uppercase' as const,
          }}>
            {cfg.label}
          </span>
        </div>

        {/* Ana sağ panel içeriği */}
        <div style={{
          flex: 1, display: 'flex', flexDirection: 'column', gap: 14,
          opacity: interpolate(frame, [rightContentAt, rightContentAt + 22], [0, 1], { extrapolateRight: 'clamp' }),
          transform: `translateY(${interpolate(frame, [rightContentAt, rightContentAt + 22], [10, 0], { extrapolateRight: 'clamp' })}px)`,
        }}>
          {scene.right_content && (
            <div style={{
              background: cfg.bg,
              border: `1px solid ${cfg.border}`,
              borderLeft: `4px solid ${panelAccent}`,
              borderRadius: 10, padding: '14px 16px',
            }}>
              <p style={{ fontSize: 14, color: TEXT_DARK, lineHeight: 1.72, margin: 0 }}>
                {scene.right_content}
              </p>
            </div>
          )}

          {/* Açıklama notu — sahnenin ortasından sonra belirir */}
          {scene.explanation && (
            <div style={{
              opacity: interpolate(frame, [explanationAt, explanationAt + 22], [0, 1], { extrapolateRight: 'clamp' }),
              background: 'rgba(43,127,224,0.05)',
              border: `1px solid ${ACCENT}25`,
              borderLeft: `3px solid ${ACCENT}`,
              borderRadius: 10, padding: '12px 14px',
            }}>
              <p style={{ fontSize: 13, color: TEXT_MID, lineHeight: 1.7, margin: 0 }}>
                {scene.explanation}
              </p>
            </div>
          )}
        </div>

        {/* Alt: konu başlığı + marka imzası */}
        <div style={{ marginTop: 'auto', paddingTop: 14, display: 'flex', justifyContent: 'space-between', alignItems: 'flex-end' }}>
          {scene.title && (
            <span style={{ fontSize: 11, color: TEXT_DIM, letterSpacing: 1, opacity: 0.7 }}>
              {scene.title}
            </span>
          )}
          <span style={{ fontSize: 11, fontWeight: 700, color: ACCENT, opacity: 0.8, letterSpacing: '0.03em', marginLeft: 'auto' }}>
            {brand.handle ?? '@adimmusavir'}
          </span>
        </div>
      </div>

      {scene.tts_url && <Audio src={scene.tts_url} />}
    </div>
  )
}
