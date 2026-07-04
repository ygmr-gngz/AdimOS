/**
 * TAccountScene — T hesabı tam ekran bileşeni
 * Klasik T biçimi, Borç sol / Alacak sağ, animasyonlu
 */
import { interpolate, spring, useCurrentFrame, useVideoConfig, Audio } from 'remotion'
import { BrandConfig, Scene } from '../types'
import { PALETTE } from '../brand'

const ACCENT = PALETTE.ACCENT
const BG_DARK = PALETTE.BG_DARK

interface Props { scene: Scene; brand: BrandConfig }

export function TAccountScene({ scene, brand }: Props) {
  const frame = useCurrentFrame()
  const { fps, width, height } = useVideoConfig()
  const isVertical = height > width

  const debitItems  = scene.debit_items  ?? []
  const creditItems = scene.credit_items ?? []

  const headerOpacity = interpolate(frame, [0, 20], [0, 1], { extrapolateRight: 'clamp' })
  const tScale = spring({ frame, fps, config: { damping: 18, stiffness: 150 }, from: 0.88, to: 1 })
  const tOpacity = interpolate(frame, [12, 32], [0, 1], { extrapolateRight: 'clamp' })

  const totalDebit  = debitItems.reduce((s, r) => s + r.amount, 0)
  const totalCredit = creditItems.reduce((s, r) => s + r.amount, 0)
  const balance = totalDebit - totalCredit

  const padH = isVertical ? 44 : 110

  return (
    <div style={{
      width: '100%', height: '100%',
      background: `linear-gradient(150deg, ${BG_DARK} 0%, #0D1E38 100%)`,
      display: 'flex', flexDirection: 'column',
      alignItems: 'center', justifyContent: 'center',
      padding: `56px ${padH}px`,
      fontFamily: brand.font_body, position: 'relative', overflow: 'hidden',
    }}>
      {/* Ambient */}
      <div style={{
        position: 'absolute', inset: 0,
        background: `radial-gradient(ellipse at 50% 35%, ${ACCENT}08 0%, transparent 60%)`,
        pointerEvents: 'none',
      }} />

      {/* Başlık */}
      <div style={{ opacity: headerOpacity, textAlign: 'center', marginBottom: 28, width: '100%' }}>
        <p style={{ fontSize: 11, fontWeight: 800, color: ACCENT, letterSpacing: 4, textTransform: 'uppercase' as const, margin: '0 0 8px' }}>
          T Hesabı
        </p>
        <h2 style={{
          fontSize: isVertical ? 28 : 36,
          fontFamily: brand.font_heading, fontWeight: 700,
          color: '#FFFFFF', margin: 0,
        }}>
          {scene.account_name ?? scene.title ?? 'Hesap'}
        </h2>
      </div>

      {/* T yapısı */}
      <div style={{
        width: '100%', transform: `scale(${tScale})`, opacity: tOpacity,
        display: 'flex', gap: 0,
        borderRadius: 16, overflow: 'hidden',
        border: `1px solid ${ACCENT}30`,
        boxShadow: `0 8px 40px rgba(0,0,0,0.35)`,
      }}>
        {/* Borç (sol) */}
        <div style={{ flex: 1, background: '#091828', borderRight: `2px solid ${ACCENT}40` }}>
          {/* Başlık */}
          <div style={{
            background: `${PALETTE.CORRECT}22`, borderBottom: `2px solid ${PALETTE.CORRECT}40`,
            padding: '12px 18px', textAlign: 'center',
          }}>
            <span style={{ fontSize: 12, fontWeight: 800, color: PALETTE.CORRECT, letterSpacing: 3 }}>
              BORÇ (+)
            </span>
          </div>
          {/* Satırlar */}
          <div style={{ minHeight: isVertical ? 140 : 180 }}>
            {debitItems.map((item, i) => {
              const dOpacity = interpolate(frame, [32 + i * 10, 48 + i * 10], [0, 1], { extrapolateRight: 'clamp' })
              return (
                <div key={i} style={{
                  display: 'flex', justifyContent: 'space-between', alignItems: 'center',
                  padding: '9px 18px', opacity: dOpacity,
                  borderBottom: `1px solid ${ACCENT}0C`,
                }}>
                  <span style={{ fontSize: isVertical ? 13 : 15, color: 'rgba(255,255,255,0.82)' }}>{item.label}</span>
                  <span style={{ fontSize: isVertical ? 13 : 15, color: PALETTE.CORRECT, fontWeight: 700, fontVariantNumeric: 'tabular-nums' }}>
                    {item.amount.toLocaleString('tr-TR')} ₺
                  </span>
                </div>
              )
            })}
          </div>
          {/* Toplam */}
          <div style={{
            borderTop: `2px solid ${PALETTE.CORRECT}40`,
            padding: '10px 18px',
            display: 'flex', justifyContent: 'space-between',
            opacity: interpolate(frame, [60, 75], [0, 1], { extrapolateRight: 'clamp' }),
          }}>
            <span style={{ fontSize: 12, fontWeight: 800, color: PALETTE.TEXT_DIM, letterSpacing: 1 }}>TOPLAM</span>
            <span style={{ fontSize: 15, color: PALETTE.CORRECT, fontWeight: 800, fontVariantNumeric: 'tabular-nums' }}>
              {totalDebit.toLocaleString('tr-TR')} ₺
            </span>
          </div>
        </div>

        {/* Alacak (sağ) */}
        <div style={{ flex: 1, background: BG_DARK }}>
          <div style={{
            background: `${ACCENT}18`, borderBottom: `2px solid ${ACCENT}40`,
            padding: '12px 18px', textAlign: 'center',
          }}>
            <span style={{ fontSize: 12, fontWeight: 800, color: PALETTE.ACCENT_LT, letterSpacing: 3 }}>
              ALACAK (−)
            </span>
          </div>
          <div style={{ minHeight: isVertical ? 140 : 180 }}>
            {creditItems.map((item, i) => {
              const cOpacity = interpolate(frame, [38 + i * 10, 54 + i * 10], [0, 1], { extrapolateRight: 'clamp' })
              return (
                <div key={i} style={{
                  display: 'flex', justifyContent: 'space-between', alignItems: 'center',
                  padding: '9px 18px', opacity: cOpacity,
                  borderBottom: `1px solid ${ACCENT}0C`,
                }}>
                  <span style={{ fontSize: isVertical ? 13 : 15, color: 'rgba(255,255,255,0.72)' }}>{item.label}</span>
                  <span style={{ fontSize: isVertical ? 13 : 15, color: PALETTE.ACCENT_LT, fontWeight: 700, fontVariantNumeric: 'tabular-nums' }}>
                    {item.amount.toLocaleString('tr-TR')} ₺
                  </span>
                </div>
              )
            })}
          </div>
          <div style={{
            borderTop: `2px solid ${ACCENT}40`,
            padding: '10px 18px',
            display: 'flex', justifyContent: 'space-between',
            opacity: interpolate(frame, [60, 75], [0, 1], { extrapolateRight: 'clamp' }),
          }}>
            <span style={{ fontSize: 12, fontWeight: 800, color: PALETTE.TEXT_DIM, letterSpacing: 1 }}>TOPLAM</span>
            <span style={{ fontSize: 15, color: PALETTE.ACCENT_LT, fontWeight: 800, fontVariantNumeric: 'tabular-nums' }}>
              {totalCredit.toLocaleString('tr-TR')} ₺
            </span>
          </div>
        </div>
      </div>

      {/* Bakiye */}
      {(totalDebit > 0 || totalCredit > 0) && (
        <div style={{
          marginTop: 20,
          opacity: interpolate(frame, [72, 90], [0, 1], { extrapolateRight: 'clamp' }),
          display: 'flex', alignItems: 'center', gap: 16,
          background: balance >= 0 ? 'rgba(34,197,94,0.10)' : `${ACCENT}10`,
          border: `1px solid ${balance >= 0 ? PALETTE.CORRECT : ACCENT}35`,
          borderRadius: 10, padding: '10px 20px',
        }}>
          <span style={{ fontSize: 12, fontWeight: 800, color: PALETTE.TEXT_DIM, letterSpacing: 2 }}>BAKİYE</span>
          <span style={{ fontSize: 17, fontWeight: 800, color: balance >= 0 ? PALETTE.CORRECT : PALETTE.ACCENT_LT, fontVariantNumeric: 'tabular-nums' }}>
            {Math.abs(balance).toLocaleString('tr-TR')} ₺ {balance >= 0 ? '(Borç)' : '(Alacak)'}
          </span>
        </div>
      )}

      {scene.explanation && (
        <div style={{
          width: '100%', marginTop: 16,
          background: `${ACCENT}08`, border: `1px solid ${ACCENT}20`, borderLeft: `4px solid ${ACCENT}`,
          borderRadius: 10, padding: '11px 15px',
          opacity: interpolate(frame, [82, 100], [0, 1], { extrapolateRight: 'clamp' }),
        }}>
          <p style={{ fontSize: isVertical ? 12 : 14, color: PALETTE.TEXT_MID, lineHeight: 1.65, margin: 0 }}>{scene.explanation}</p>
        </div>
      )}

      {scene.tts_url && <Audio src={scene.tts_url} />}
    </div>
  )
}
