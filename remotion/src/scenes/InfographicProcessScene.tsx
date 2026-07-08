/**
 * InfographicProcessScene — Adım adım süreç şeridi
 * Ör: "Yevmiye kaydı nasıl yapılır?" — numaralı adım zinciri
 */
import { interpolate, spring, useCurrentFrame, useVideoConfig, Audio } from 'remotion'
import { BrandConfig, Scene } from '../types'
import { PALETTE } from '../brand'

const ACCENT = PALETTE.ACCENT
const BG_DARK = PALETTE.BG_DARK

interface Props { scene: Scene; brand: BrandConfig }

export function InfographicProcessScene({ scene, brand }: Props) {
  const frame = useCurrentFrame()
  const { fps, width, height } = useVideoConfig()
  const isVertical = height > width

  const steps = scene.process_steps ?? []
  const headerOpacity = interpolate(frame, [0, 22], [0, 1], { extrapolateRight: 'clamp' })

  // Bağlantı çizgisi uzunluğu (dikey için yükseklik, yatay için genişlik)
  const connectorLength = interpolate(frame, [30, 70], [0, 100], { extrapolateRight: 'clamp' })

  return (
    <div style={{
      width: '100%', height: '100%',
      background: BG_DARK, display: 'flex', flexDirection: 'column',
      fontFamily: brand.font_body, overflow: 'hidden', position: 'relative',
      padding: isVertical ? '28px 28px' : '36px 60px',
    }}>
      <div style={{
        position: 'absolute', inset: 0,
        background: `radial-gradient(ellipse at 50% 30%, ${ACCENT}06 0%, transparent 60%)`,
        pointerEvents: 'none',
      }} />

      {/* Başlık */}
      <div style={{ opacity: headerOpacity, marginBottom: isVertical ? 20 : 28 }}>
        {scene.infographic_subtitle && (
          <p style={{ fontSize: 10, fontWeight: 800, color: ACCENT, letterSpacing: 3, margin: '0 0 6px', textTransform: 'uppercase' as const }}>
            {scene.infographic_subtitle}
          </p>
        )}
        <h1 style={{
          fontSize: isVertical ? 22 : 30,
          fontFamily: brand.font_heading, fontWeight: 700,
          color: '#FFFFFF', margin: 0,
        }}>
          {scene.infographic_title ?? scene.title}
        </h1>
      </div>

      {/* Adım zinciri */}
      <div style={{
        flex: 1,
        display: 'flex',
        flexDirection: isVertical ? 'column' : 'row',
        gap: 0, alignItems: isVertical ? 'stretch' : 'flex-start',
      }}>
        {steps.map((step, i) => {
          const delay = 28 + i * 16
          const sc = spring({ frame, fps, config: { damping: 18, stiffness: 200 }, from: 0, to: 1, delay })
          const op = interpolate(frame, [delay, delay + 16], [0, 1], { extrapolateRight: 'clamp' })
          const isLast = i === steps.length - 1

          return (
            <div key={i} style={{
              display: 'flex',
              flexDirection: isVertical ? 'row' : 'column',
              flex: 1, gap: 0, alignItems: isVertical ? 'flex-start' : 'center',
            }}>
              {/* Kart */}
              <div style={{
                background: `linear-gradient(135deg, #112038 0%, #0D1B30 100%)`,
                border: `1px solid ${ACCENT}${i === 0 ? '50' : '22'}`,
                borderRadius: 14, padding: isVertical ? '14px 16px' : '18px 16px',
                flex: isVertical ? 'none' : 1,
                opacity: op, transform: `scale(${sc})`,
                boxShadow: `0 4px 20px rgba(0,0,0,0.3)`,
                position: 'relative' as const,
              }}>
                {/* Numara badge */}
                <div style={{
                  position: 'absolute' as const,
                  top: isVertical ? 14 : -14,
                  transform: isVertical ? 'none' : 'translateX(-50%)',
                  left: isVertical ? undefined : '50%',
                  right: isVertical ? 16 : undefined,
                  width: 28, height: 28, borderRadius: '50%',
                  background: ACCENT, color: '#fff',
                  fontWeight: 800, fontSize: 13,
                  display: 'flex', alignItems: 'center', justifyContent: 'center',
                  boxShadow: `0 0 12px ${ACCENT}50`,
                }}>
                  {step.number}
                </div>
                <h3 style={{
                  fontSize: isVertical ? 14 : 13, fontWeight: 700,
                  color: '#FFFFFF', margin: isVertical ? '0 40px 6px 0' : `24px 0 8px`,
                  lineHeight: 1.3,
                }}>
                  {step.title}
                </h3>
                <p style={{
                  fontSize: isVertical ? 11 : 11,
                  color: PALETTE.TEXT_MID, lineHeight: 1.6, margin: 0,
                }}>
                  {step.desc}
                </p>
              </div>

              {/* Bağlantı ok */}
              {!isLast && (
                <div style={{
                  display: 'flex', alignItems: 'center', justifyContent: 'center',
                  flexShrink: 0,
                  width: isVertical ? 'auto' : 24,
                  height: isVertical ? 24 : 'auto',
                  padding: isVertical ? '4px 0' : '0 4px',
                }}>
                  <div style={{
                    background: `${ACCENT}50`,
                    borderRadius: 2,
                    width: isVertical ? 2 : `${connectorLength}%`,
                    height: isVertical ? `${connectorLength}%` : 2,
                  }} />
                  <span style={{
                    color: ACCENT, fontSize: 14,
                    transform: isVertical ? 'rotate(90deg)' : 'none',
                    marginLeft: isVertical ? 0 : -2,
                  }}>›</span>
                </div>
              )}
            </div>
          )
        })}
      </div>

      {/* Alt imza şeridi — logo sol + @handle sağ */}
      <div style={{
        marginTop: 14, paddingTop: 10,
        borderTop: `1px solid ${ACCENT}25`,
        display: 'flex', justifyContent: 'space-between', alignItems: 'center',
        opacity: interpolate(frame, [90, 108], [0, 1], { extrapolateRight: 'clamp' }),
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 7 }}>
          {brand.logo_url ? (
            <img src={brand.logo_url} style={{ height: 16, opacity: 0.75, objectFit: 'contain' }} alt="" />
          ) : (
            <span style={{ fontSize: 9, fontWeight: 800, color: PALETTE.TEXT_MID, letterSpacing: 2, textTransform: 'uppercase' as const }}>
              ADIM MÜŞAVİR
            </span>
          )}
          <span style={{ fontSize: 9, color: PALETTE.TEXT_DIM, letterSpacing: 0.5 }}>
            {scene.footer_note ?? 'Eğitim amaçlı hazırlanmıştır.'}
          </span>
        </div>
        <span style={{ fontSize: 10, color: ACCENT, fontWeight: 800, letterSpacing: 1 }}>
          {brand.handle ?? '@adimmusavir'}
        </span>
      </div>

      {scene.tts_url && <Audio src={scene.tts_url} />}
    </div>
  )
}
