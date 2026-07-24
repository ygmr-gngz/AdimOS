/**
 * EducationalReelScene — 2 dakikalık SGS eğitim Reels sahnesi (9:16)
 *
 * Her sahne bir segment_type taşır:
 *   hook    (0–5s)    : Güçlü kanca başlığı
 *   context (5–20s)   : Konunun önemi
 *   content (20–70s)  : Bilgi / çözüm adımı
 *   mistake (70–95s)  : Sık yapılan hata
 *   tip     (95–110s) : Sınav ipucu
 *   outro   (110–120s): Özet + CTA
 *
 * Her sahne:
 *   - visual.visual_url varsa: arka plan fotoğraf + overlay
 *   - yoksa: lacivert gradyan zemini
 *   - motion: zoom_in / zoom_out / pan_left / pan_right / static
 */
import { AbsoluteFill, Img, interpolate, useCurrentFrame, useVideoConfig, Audio } from 'remotion'
import { Scene, BrandConfig, ReelSegmentType } from '../types'
import { PALETTE } from '../brand'

interface Props { scene: Scene; brand: BrandConfig }

const ACCENT = PALETTE.ACCENT   // #2B7FE0
const WHITE  = '#FFFFFF'

// ── Ken Burns (zoom/pan) efekti ─────────────────────────────
function useKenBurns(motion: string | undefined) {
  const frame  = useCurrentFrame()
  const { durationInFrames } = useVideoConfig()
  const p = interpolate(frame, [0, durationInFrames], [0, 1], { extrapolateRight: 'clamp' })

  switch (motion) {
    case 'zoom_in':
      return `scale(${1 + 0.08 * p})`
    case 'zoom_out':
      return `scale(${1.08 - 0.08 * p})`
    case 'pan_left':
      return `translate(${-4 * p}%, 0) scale(1.05)`
    case 'pan_right':
      return `translate(${4 * p}%, 0) scale(1.05)`
    default:
      return 'scale(1)'
  }
}

// ── Segment renk şeması ──────────────────────────────────────
function segmentStyle(type: ReelSegmentType | undefined): {
  accent: string; badge: string; badgeText: string; labelText: string
} {
  switch (type) {
    case 'hook':    return { accent: '#1E40AF', badge: '#1E40AF', badgeText: WHITE, labelText: '⚡ BUGÜN ÖĞRENECEKSİN' }
    case 'context': return { accent: '#0369A1', badge: '#0369A1', badgeText: WHITE, labelText: '📌 NEDEN ÖNEMLİ?' }
    case 'content': return { accent: ACCENT,    badge: ACCENT,    badgeText: WHITE, labelText: '📖 KONU' }
    case 'mistake': return { accent: '#DC2626', badge: '#DC2626', badgeText: WHITE, labelText: '⚠️ SIK YAPILAN HATA' }
    case 'tip':     return { accent: '#D97706', badge: '#D97706', badgeText: WHITE, labelText: '💡 SINAV İPUCU' }
    case 'outro':   return { accent: '#16A34A', badge: '#16A34A', badgeText: WHITE, labelText: '✅ ÖZET' }
    default:        return { accent: ACCENT,    badge: ACCENT,    badgeText: WHITE, labelText: '' }
  }
}

export function EducationalReelScene({ scene, brand }: Props) {
  const frame = useCurrentFrame()
  const { fps, durationInFrames } = useVideoConfig()
  const progress = interpolate(frame, [0, durationInFrames], [0, 1], { extrapolateRight: 'clamp' })

  const visual   = scene.visual
  const motion   = visual?.motion ?? 'zoom_in'
  const transform = useKenBurns(motion)
  const overlayOpacity = visual?.overlay_opacity ?? 0.45

  const seg = scene.segment_type
  const { accent, badge, badgeText, labelText } = segmentStyle(seg)

  // Animasyon: fade-in
  const fadeIn = interpolate(frame, [0, 18], [0, 1], { extrapolateRight: 'clamp' })
  // Başlık slide-up
  const slideY = interpolate(frame, [0, 22], [30, 0], { extrapolateRight: 'clamp' })

  // Outro: son %15'te fade-out
  const fadeOut = seg === 'outro'
    ? interpolate(frame, [Math.floor(durationInFrames * 0.85), durationInFrames], [1, 0], { extrapolateRight: 'clamp' })
    : 1

  // Hook: büyük vurucu başlık animasyonu
  const hookScale = seg === 'hook'
    ? interpolate(frame, [0, 30], [0.85, 1], { extrapolateRight: 'clamp' })
    : 1

  const audioSrc = scene.tts_url ?? scene.audio_url ?? undefined

  return (
    <AbsoluteFill style={{ overflow: 'hidden', fontFamily: brand.font_body }}>
      {/* ── Arka plan: görsel veya gradyan ── */}
      {visual?.visual_url ? (
        <div style={{
          position: 'absolute', inset: 0,
          transform, transformOrigin: 'center center',
        }}>
          <Img
            src={visual.visual_url}
            style={{ width: '100%', height: '100%', objectFit: 'cover' }}
          />
          {/* Overlay — okunabilirlik için karartma */}
          <div style={{
            position: 'absolute', inset: 0,
            background: `linear-gradient(
              to bottom,
              rgba(0,0,0,${overlayOpacity * 0.6}) 0%,
              rgba(0,0,0,${overlayOpacity}) 40%,
              rgba(0,0,0,${overlayOpacity * 1.3}) 100%
            )`,
          }} />
        </div>
      ) : (
        /* Görsel yoksa lacivert gradyan */
        <div style={{
          position: 'absolute', inset: 0,
          background: 'linear-gradient(160deg, #0B2A4A 0%, #0D1F3C 45%, #0A1628 100%)',
        }} />
      )}

      {/* ── İçerik katmanı ── */}
      <AbsoluteFill style={{ opacity: fadeIn * fadeOut }}>
        {/* Segment etiketi */}
        {labelText && (
          <div style={{
            position: 'absolute', top: 60, left: 28,
            background: badge, color: badgeText,
            borderRadius: 20, padding: '6px 16px',
            fontSize: 13, fontWeight: 800, letterSpacing: 1,
          }}>
            {labelText}
          </div>
        )}

        {/* Ana içerik alanı — ekranın ortasında */}
        <div style={{
          position: 'absolute',
          top: seg === 'hook' ? '25%' : '18%',
          bottom: 120,
          left: 0, right: 0,
          display: 'flex', flexDirection: 'column',
          justifyContent: seg === 'hook' ? 'center' : 'flex-start',
          padding: '0 32px',
          gap: 20,
          transform: `translateY(${slideY}px)`,
        }}>
          {/* Hook: büyük kanca metni */}
          {seg === 'hook' && scene.hook_text && (
            <div style={{
              transform: `scale(${hookScale})`,
              textAlign: 'center',
            }}>
              <div style={{
                fontSize: 52, fontWeight: 900, color: WHITE,
                fontFamily: brand.font_heading,
                lineHeight: 1.2, textAlign: 'center',
                textShadow: '0 2px 20px rgba(0,0,0,0.5)',
              }}>
                {scene.hook_text}
              </div>
              {scene.highlight_stat && (
                <div style={{
                  fontSize: 80, fontWeight: 900,
                  color: accent, fontFamily: brand.font_heading,
                  marginTop: 16, lineHeight: 1,
                  textShadow: `0 0 30px ${accent}60`,
                }}>
                  {scene.highlight_stat}
                </div>
              )}
            </div>
          )}

          {/* Non-hook sahneler: başlık + içerik */}
          {seg !== 'hook' && (
            <>
              {scene.title && (
                <div style={{
                  fontSize: 38, fontWeight: 800, color: WHITE,
                  fontFamily: brand.font_heading,
                  lineHeight: 1.3,
                  borderLeft: `5px solid ${accent}`,
                  paddingLeft: 16,
                }}>
                  {scene.title}
                </div>
              )}

              {/* Bullet points */}
              {scene.bullet_points && scene.bullet_points.length > 0 && (
                <div style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
                  {scene.bullet_points.map((bp, i) => {
                    const bpReveal = interpolate(frame, [22 + i * 18, 40 + i * 18], [0, 1], { extrapolateRight: 'clamp' })
                    return (
                      <div key={i} style={{
                        display: 'flex', alignItems: 'flex-start', gap: 12,
                        opacity: bpReveal, transform: `translateX(${(1 - bpReveal) * 20}px)`,
                      }}>
                        <div style={{
                          width: 8, height: 8, borderRadius: '50%',
                          background: accent, flexShrink: 0, marginTop: 10,
                        }} />
                        <span style={{
                          fontSize: 34, color: 'rgba(255,255,255,0.92)',
                          lineHeight: 1.55, fontWeight: 500,
                        }}>
                          {bp}
                        </span>
                      </div>
                    )
                  })}
                </div>
              )}

              {/* Soru metni (content sahnelerinde) */}
              {scene.question_text && !scene.bullet_points?.length && (
                <div style={{
                  background: 'rgba(255,255,255,0.10)',
                  border: `1.5px solid rgba(255,255,255,0.20)`,
                  borderRadius: 12, padding: '18px 20px',
                }}>
                  <p style={{
                    fontSize: 38, color: WHITE,
                    lineHeight: 1.55, margin: 0, fontFamily: brand.font_heading,
                  }}>
                    {scene.question_text}
                  </p>
                </div>
              )}

              {/* Sık yapılan hata kutusu */}
              {seg === 'mistake' && scene.common_mistake && (
                <div style={{
                  background: 'rgba(220,38,38,0.15)',
                  border: '1.5px solid rgba(220,38,38,0.50)',
                  borderRadius: 12, padding: '14px 18px',
                  display: 'flex', alignItems: 'flex-start', gap: 12,
                }}>
                  <span style={{ fontSize: 24, flexShrink: 0, marginTop: 2 }}>⚠️</span>
                  <span style={{ fontSize: 36, color: '#FCA5A5', lineHeight: 1.5, fontWeight: 600 }}>
                    {scene.common_mistake}
                  </span>
                </div>
              )}

              {/* Sınav ipucu */}
              {seg === 'tip' && scene.exam_tip && (
                <div style={{
                  background: 'rgba(217,119,6,0.15)',
                  border: '1.5px solid rgba(217,119,6,0.50)',
                  borderRadius: 12, padding: '14px 18px',
                  display: 'flex', alignItems: 'flex-start', gap: 12,
                }}>
                  <span style={{ fontSize: 24, flexShrink: 0, marginTop: 2 }}>💡</span>
                  <span style={{ fontSize: 36, color: '#FDE68A', lineHeight: 1.5, fontWeight: 600 }}>
                    {scene.exam_tip}
                  </span>
                </div>
              )}

              {/* Outro: CTA */}
              {seg === 'outro' && scene.cta_text && (
                <div style={{
                  background: `linear-gradient(135deg, ${accent}22, ${accent}44)`,
                  border: `2px solid ${accent}`,
                  borderRadius: 16, padding: '20px 24px', textAlign: 'center',
                }}>
                  <p style={{
                    fontSize: 40, color: WHITE, fontWeight: 800,
                    fontFamily: brand.font_heading, lineHeight: 1.4, margin: 0,
                  }}>
                    {scene.cta_text}
                  </p>
                </div>
              )}

              {/* Genel açıklama / alt not */}
              {scene.explanation && (
                <div style={{
                  fontSize: 30, color: 'rgba(255,255,255,0.72)',
                  lineHeight: 1.65, fontStyle: 'italic',
                }}>
                  {scene.explanation}
                </div>
              )}
            </>
          )}
        </div>

        {/* Alt dekoratif çubuk */}
        <div style={{
          position: 'absolute', bottom: 80, left: 32, right: 32,
          height: 2,
          background: `linear-gradient(90deg, transparent, ${accent}, transparent)`,
          opacity: 0.4,
        }} />
      </AbsoluteFill>

      {audioSrc && <Audio src={audioSrc} />}
    </AbsoluteFill>
  )
}
