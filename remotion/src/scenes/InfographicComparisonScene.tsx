/**
 * InfographicComparisonScene — İki sütun karşılaştırma (Aktif vs Pasif vb.)
 */
import { interpolate, spring, useCurrentFrame, useVideoConfig, Audio } from 'remotion'
import { BrandConfig, Scene } from '../types'
import { PALETTE } from '../brand'

const ACCENT = PALETTE.ACCENT
const BG_DARK = PALETTE.BG_DARK

interface Props { scene: Scene; brand: BrandConfig }

export function InfographicComparisonScene({ scene, brand }: Props) {
  const frame = useCurrentFrame()
  const { fps, width, height } = useVideoConfig()
  const isVertical = height > width

  const left  = scene.comparison_left  ?? { title: 'Sol', items: [] }
  const right = scene.comparison_right ?? { title: 'Sağ', items: [] }

  const headerOpacity = interpolate(frame, [0, 22], [0, 1], { extrapolateRight: 'clamp' })
  const dividerH = interpolate(frame, [28, 50], [0, isVertical ? 400 : 500], { extrapolateRight: 'clamp' })
  const leftOpacity  = interpolate(frame, [32, 50], [0, 1], { extrapolateRight: 'clamp' })
  const rightOpacity = interpolate(frame, [44, 62], [0, 1], { extrapolateRight: 'clamp' })

  const leftColor  = PALETTE.CORRECT   // yeşil — sol
  const rightColor = PALETTE.ACCENT_LT // mavi — sağ

  return (
    <div style={{
      width: '100%', height: '100%',
      background: BG_DARK, display: 'flex', flexDirection: 'column',
      fontFamily: brand.font_body, overflow: 'hidden', position: 'relative',
      padding: isVertical ? '28px 24px' : '36px 60px',
    }}>
      <div style={{
        position: 'absolute', inset: 0,
        background: `radial-gradient(ellipse at 50% 40%, ${ACCENT}07 0%, transparent 60%)`,
        pointerEvents: 'none',
      }} />

      {/* Başlık */}
      <div style={{ opacity: headerOpacity, marginBottom: isVertical ? 20 : 28, textAlign: 'center' }}>
        {scene.infographic_subtitle && (
          <p style={{ fontSize: 10, fontWeight: 800, color: ACCENT, letterSpacing: 3, margin: '0 0 6px', textTransform: 'uppercase' as const }}>
            {scene.infographic_subtitle}
          </p>
        )}
        <h1 style={{
          fontSize: isVertical ? 24 : 32,
          fontFamily: brand.font_heading, fontWeight: 700,
          color: '#FFFFFF', margin: 0,
        }}>
          {scene.infographic_title ?? scene.title}
        </h1>
      </div>

      {/* İki sütun */}
      <div style={{
        flex: 1, display: 'flex', gap: 0, position: 'relative',
        alignItems: isVertical ? 'flex-start' : 'stretch',
        flexDirection: isVertical ? 'column' : 'row',
      }}>
        {/* Sol sütun */}
        <div style={{ flex: 1, opacity: leftOpacity, padding: isVertical ? '0 0 12px' : '0 32px 0 0' }}>
          <div style={{
            background: `${leftColor}15`, border: `1px solid ${leftColor}35`,
            borderRadius: 14, padding: '16px 20px', height: '100%',
          }}>
            <div style={{
              display: 'flex', alignItems: 'center', gap: 10, marginBottom: 16,
              paddingBottom: 12, borderBottom: `1px solid ${leftColor}30`,
            }}>
              <div style={{
                width: 28, height: 28, borderRadius: '50%', background: leftColor,
                display: 'flex', alignItems: 'center', justifyContent: 'center',
              }}>
                <svg width="14" height="14" viewBox="0 0 14 14" fill="none">
                  <path d="M2 7h10M8 3l4 4-4 4" stroke="#fff" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round"/>
                </svg>
              </div>
              <span style={{ fontSize: 15, fontWeight: 800, color: leftColor }}>{left.title}</span>
            </div>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
              {left.items.map((item, i) => {
                const iOp = interpolate(frame, [50 + i * 10, 65 + i * 10], [0, 1], { extrapolateRight: 'clamp' })
                const iX = interpolate(frame, [50 + i * 10, 65 + i * 10], [-16, 0], { extrapolateRight: 'clamp' })
                return (
                  <div key={i} style={{ display: 'flex', gap: 10, opacity: iOp, transform: `translateX(${iX}px)` }}>
                    <div style={{ width: 6, height: 6, borderRadius: '50%', background: leftColor, marginTop: 8, flexShrink: 0 }} />
                    <span style={{ fontSize: isVertical ? 12 : 14, color: '#FFFFFF', lineHeight: 1.55 }}>{item}</span>
                  </div>
                )
              })}
            </div>
          </div>
        </div>

        {/* Orta ayraç */}
        {!isVertical && (
          <div style={{
            width: 2, height: dividerH, background: `${ACCENT}30`,
            alignSelf: 'center', borderRadius: 2, flexShrink: 0,
          }} />
        )}
        {isVertical && (
          <div style={{ height: 1, background: `${ACCENT}30`, margin: '4px 0', borderRadius: 1 }} />
        )}

        {/* Sağ sütun */}
        <div style={{ flex: 1, opacity: rightOpacity, padding: isVertical ? '12px 0 0' : '0 0 0 32px' }}>
          <div style={{
            background: `${rightColor}12`, border: `1px solid ${rightColor}30`,
            borderRadius: 14, padding: '16px 20px', height: '100%',
          }}>
            <div style={{
              display: 'flex', alignItems: 'center', gap: 10, marginBottom: 16,
              paddingBottom: 12, borderBottom: `1px solid ${rightColor}25`,
            }}>
              <div style={{
                width: 28, height: 28, borderRadius: '50%', background: rightColor,
                display: 'flex', alignItems: 'center', justifyContent: 'center',
              }}>
                <svg width="14" height="14" viewBox="0 0 14 14" fill="none">
                  <path d="M12 7H2M6 11l-4-4 4-4" stroke="#fff" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round"/>
                </svg>
              </div>
              <span style={{ fontSize: 15, fontWeight: 800, color: rightColor }}>{right.title}</span>
            </div>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
              {right.items.map((item, i) => {
                const iOp = interpolate(frame, [62 + i * 10, 77 + i * 10], [0, 1], { extrapolateRight: 'clamp' })
                const iX = interpolate(frame, [62 + i * 10, 77 + i * 10], [16, 0], { extrapolateRight: 'clamp' })
                return (
                  <div key={i} style={{ display: 'flex', gap: 10, opacity: iOp, transform: `translateX(${iX}px)` }}>
                    <div style={{ width: 6, height: 6, borderRadius: '50%', background: rightColor, marginTop: 8, flexShrink: 0 }} />
                    <span style={{ fontSize: isVertical ? 12 : 14, color: '#FFFFFF', lineHeight: 1.55 }}>{item}</span>
                  </div>
                )
              })}
            </div>
          </div>
        </div>
      </div>

      {/* Alt imza şeridi — logo sol + @handle sağ */}
      <div style={{
        marginTop: 14, paddingTop: 10,
        borderTop: `1px solid ${ACCENT}25`,
        display: 'flex', justifyContent: 'space-between', alignItems: 'center',
        opacity: interpolate(frame, [85, 100], [0, 1], { extrapolateRight: 'clamp' }),
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
