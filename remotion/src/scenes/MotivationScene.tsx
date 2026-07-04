/**
 * MotivationScene — Kinetik yazı motivasyon sahnesi (Shorts/Reels)
 * Koyu lacivert zemin + marka filigran dokusu + kelime kelime açılan mesaj
 * Seslendirmeli (tts_url) veya sessiz (yalnız metin) varyant
 */
import { interpolate, spring, useCurrentFrame, useVideoConfig, Audio } from 'remotion'
import { BrandConfig, Scene } from '../types'
import { PALETTE } from '../brand'

const ACCENT = PALETTE.ACCENT
const BG_DARK = PALETTE.BG_DARK
const BG_MID  = PALETTE.BG_MID

interface Props { scene: Scene; brand: BrandConfig }

// Kelime kelime animasyon
function KineticText({ text, startFrame, fps, fontSize, color }: {
  text: string
  startFrame: number
  fps: number
  fontSize: number
  color: string
}) {
  const frame = useCurrentFrame()
  const words = text.split(' ')

  return (
    <div style={{ display: 'flex', flexWrap: 'wrap' as const, gap: '0 10px', justifyContent: 'center' }}>
      {words.map((word, i) => {
        const delay = startFrame + i * 5
        const wScale = spring({ frame, fps, config: { damping: 16, stiffness: 260 }, from: 0.4, to: 1, delay })
        const wOp = interpolate(frame, [delay, delay + 10], [0, 1], { extrapolateRight: 'clamp' })
        const wY = interpolate(frame, [delay, delay + 12], [20, 0], { extrapolateRight: 'clamp' })

        return (
          <span key={i} style={{
            fontSize, fontWeight: 700, color,
            opacity: wOp,
            transform: `scale(${wScale}) translateY(${wY}px)`,
            display: 'inline-block',
            lineHeight: 1.3,
          }}>
            {word}
          </span>
        )
      })}
    </div>
  )
}

export function MotivationScene({ scene, brand }: Props) {
  const frame = useCurrentFrame()
  const { fps, width, height } = useVideoConfig()
  const isVertical = height > width

  const message = scene.message ?? scene.title ?? ''
  const author  = scene.message_author

  // Filigran döngüsü — arka planda sabit metin "ADIM MÜŞAVİR" tekrarlanır
  const patternCount = 6

  const brandOpacity = interpolate(frame, [0, 30], [0, 1], { extrapolateRight: 'clamp' })
  const lineW = interpolate(frame, [15, 50], [0, isVertical ? 160 : 200], { extrapolateRight: 'clamp' })
  const ctaOpacity = interpolate(frame, [Math.round(message.split(' ').length * 5) + 40, Math.round(message.split(' ').length * 5) + 60], [0, 1], { extrapolateRight: 'clamp' })

  const msgFontSize = isVertical
    ? (message.length > 80 ? 36 : message.length > 50 ? 44 : 54)
    : (message.length > 80 ? 48 : message.length > 50 ? 60 : 72)

  return (
    <div style={{
      width: '100%', height: '100%',
      background: `linear-gradient(145deg, ${BG_DARK} 0%, #0A1628 50%, ${BG_DARK} 100%)`,
      display: 'flex', flexDirection: 'column',
      alignItems: 'center', justifyContent: 'center',
      fontFamily: brand.font_heading,
      position: 'relative', overflow: 'hidden',
    }}>
      {/* Filigran arka plan — düşük opaklık "ADIM MÜŞAVİR" tekrar deseni */}
      <div style={{
        position: 'absolute', inset: 0,
        display: 'flex', flexDirection: 'column', justifyContent: 'space-around',
        padding: '20px 0', opacity: 0.04,
        transform: 'rotate(-8deg) scale(1.2)',
        pointerEvents: 'none',
      }}>
        {Array.from({ length: patternCount }).map((_, row) => (
          <div key={row} style={{ display: 'flex', justifyContent: 'space-around', gap: 40 }}>
            {Array.from({ length: 4 }).map((_, col) => (
              <span key={col} style={{
                fontSize: 32, fontWeight: 800, color: '#fff',
                letterSpacing: 4, whiteSpace: 'nowrap' as const,
              }}>
                ADIM MÜŞAVİR
              </span>
            ))}
          </div>
        ))}
      </div>

      {/* Üst accent bar */}
      <div style={{
        position: 'absolute', top: 0, left: 0, right: 0, height: 4,
        background: `linear-gradient(90deg, transparent, ${ACCENT}, transparent)`,
        opacity: brandOpacity,
      }} />

      {/* Marka etiketi üstte */}
      <div style={{
        position: 'absolute', top: isVertical ? 28 : 24,
        display: 'flex', alignItems: 'center', gap: 8,
        opacity: brandOpacity,
      }}>
        <div style={{ width: 28, height: 28, borderRadius: '50%', background: ACCENT, opacity: 0.9 }} />
        <span style={{
          fontSize: 13, fontWeight: 800, color: 'rgba(255,255,255,0.6)',
          letterSpacing: 2, textTransform: 'uppercase' as const, fontFamily: brand.font_body,
        }}>
          @adimmusavir
        </span>
      </div>

      {/* Ana mesaj */}
      <div style={{
        padding: isVertical ? '0 36px' : '0 100px',
        textAlign: 'center', maxWidth: isVertical ? '90%' : '75%',
        display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 0,
      }}>
        {/* Üst çizgi */}
        <div style={{
          width: lineW, height: 3,
          background: ACCENT, borderRadius: 2,
          marginBottom: 28, opacity: 0.8,
        }} />

        <KineticText
          text={message}
          startFrame={20}
          fps={fps}
          fontSize={msgFontSize}
          color="#FFFFFF"
        />

        {/* Alt çizgi */}
        <div style={{
          width: lineW, height: 3,
          background: ACCENT, borderRadius: 2,
          marginTop: 28, opacity: 0.8,
        }} />
      </div>

      {/* İmza — mesaj_author */}
      {author && (
        <div style={{
          marginTop: 28, opacity: ctaOpacity,
          textAlign: 'center',
        }}>
          <span style={{
            fontSize: isVertical ? 16 : 20, fontWeight: 600,
            color: PALETTE.ACCENT_LT, fontFamily: brand.font_body,
            fontStyle: 'italic',
          }}>
            — {author}
          </span>
        </div>
      )}

      {/* Alt: kategorik CTA */}
      <div style={{
        position: 'absolute', bottom: isVertical ? 28 : 24,
        opacity: ctaOpacity, textAlign: 'center',
        display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 6,
      }}>
        <span style={{
          fontSize: 11, color: PALETTE.TEXT_DIM,
          fontFamily: brand.font_body, letterSpacing: 1.5,
          textTransform: 'uppercase' as const,
        }}>
          SGS · SMMM Yolculuğunda
        </span>
        <span style={{
          fontSize: 13, color: ACCENT, fontWeight: 700,
          fontFamily: brand.font_body, letterSpacing: 1,
        }}>
          Başar — Adım Müşavir ile
        </span>
      </div>

      {/* Alt accent bar */}
      <div style={{
        position: 'absolute', bottom: 0, left: 0, right: 0, height: 4,
        background: `linear-gradient(90deg, transparent, ${ACCENT}, transparent)`,
        opacity: brandOpacity * 0.4,
      }} />

      {scene.tts_url && <Audio src={scene.tts_url} />}
    </div>
  )
}
