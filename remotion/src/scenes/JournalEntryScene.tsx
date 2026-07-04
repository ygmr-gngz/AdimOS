/**
 * JournalEntryScene — Yevmiye kaydı tam ekran bileşeni
 * Borç/Alacak iki sütun, hesap kodu + ad + tutar hizalı, animasyonlu
 */
import { interpolate, spring, useCurrentFrame, useVideoConfig, Audio } from 'remotion'
import { BrandConfig, Scene } from '../types'
import { PALETTE } from '../brand'

const ACCENT = PALETTE.ACCENT
const BG_DARK = PALETTE.BG_DARK
const BG_MID = PALETTE.BG_MID

interface Props { scene: Scene; brand: BrandConfig }

export function JournalEntryScene({ scene, brand }: Props) {
  const frame = useCurrentFrame()
  const { fps, width, height } = useVideoConfig()
  const isVertical = height > width

  const rows = scene.journal_rows ?? []
  const debitRows  = rows.filter(r => r.debit  !== undefined)
  const creditRows = rows.filter(r => r.credit !== undefined)

  const headerOpacity = interpolate(frame, [0, 22], [0, 1], { extrapolateRight: 'clamp' })
  const tableScale = spring({ frame, fps, config: { damping: 20, stiffness: 160 }, from: 0.92, to: 1 })
  const tableOpacity = interpolate(frame, [14, 34], [0, 1], { extrapolateRight: 'clamp' })

  const padH = isVertical ? 48 : 120
  const padV = isVertical ? 60 : 56

  const totalDebit  = debitRows.reduce((s, r) => s + (r.debit ?? 0), 0)
  const totalCredit = creditRows.reduce((s, r) => s + (r.credit ?? 0), 0)

  return (
    <div style={{
      width: '100%', height: '100%',
      background: `linear-gradient(145deg, ${BG_DARK} 0%, #0C1E36 100%)`,
      display: 'flex', flexDirection: 'column',
      alignItems: 'center', justifyContent: 'center',
      padding: `${padV}px ${padH}px`,
      fontFamily: brand.font_body, position: 'relative', overflow: 'hidden',
    }}>
      {/* Background glow */}
      <div style={{
        position: 'absolute', inset: 0,
        background: `radial-gradient(ellipse at 50% 30%, ${ACCENT}08 0%, transparent 65%)`,
        pointerEvents: 'none',
      }} />

      {/* Top bar */}
      <div style={{
        position: 'absolute', top: 0, left: 0, right: 0, height: 4,
        background: `linear-gradient(90deg, transparent, ${ACCENT}, transparent)`,
        opacity: 0.7,
      }} />

      {/* Başlık */}
      <div style={{ opacity: headerOpacity, textAlign: 'center', marginBottom: isVertical ? 36 : 32, width: '100%' }}>
        <p style={{
          fontSize: 12, fontWeight: 800, color: ACCENT,
          letterSpacing: 4, textTransform: 'uppercase' as const, margin: '0 0 8px',
        }}>
          Yevmiye Kaydı
        </p>
        {scene.title && (
          <h2 style={{
            fontSize: isVertical ? 28 : 32,
            fontFamily: brand.font_heading, fontWeight: 700,
            color: '#FFFFFF', margin: 0, lineHeight: 1.3,
          }}>
            {scene.title}
          </h2>
        )}
      </div>

      {/* Tablo */}
      <div style={{
        width: '100%', transform: `scale(${tableScale})`,
        opacity: tableOpacity,
        borderRadius: 16, overflow: 'hidden',
        border: `1px solid ${ACCENT}25`,
        boxShadow: `0 8px 40px rgba(0,0,0,0.4)`,
      }}>
        {/* Tablo başlığı */}
        <div style={{
          display: 'grid', gridTemplateColumns: isVertical ? '50px 1fr 100px' : '80px 1fr 130px',
          background: ACCENT, padding: '12px 20px', gap: 10,
        }}>
          <span style={{ fontSize: 11, fontWeight: 800, color: '#fff', letterSpacing: 2 }}>KOD</span>
          <span style={{ fontSize: 11, fontWeight: 800, color: '#fff', letterSpacing: 2 }}>HESAP ADI</span>
          <span style={{ fontSize: 11, fontWeight: 800, color: '#fff', letterSpacing: 2, textAlign: 'right' }}>TUTAR</span>
        </div>

        {/* Borç satırları */}
        {debitRows.map((row, i) => {
          const rOpacity = interpolate(frame, [34 + i * 12, 50 + i * 12], [0, 1], { extrapolateRight: 'clamp' })
          const rX = interpolate(frame, [34 + i * 12, 50 + i * 12], [-20, 0], { extrapolateRight: 'clamp' })
          return (
            <div key={`d${i}`} style={{
              display: 'grid',
              gridTemplateColumns: isVertical ? '50px 1fr 100px' : '80px 1fr 130px',
              padding: '11px 20px', gap: 10,
              background: i % 2 === 0 ? BG_MID : `${BG_MID}AA`,
              borderBottom: `1px solid ${ACCENT}12`,
              opacity: rOpacity, transform: `translateX(${rX}px)`,
            }}>
              <span style={{ fontSize: isVertical ? 12 : 14, color: ACCENT, fontWeight: 600, fontVariantNumeric: 'tabular-nums' }}>
                {row.code ?? '—'}
              </span>
              <span style={{ fontSize: isVertical ? 13 : 15, color: '#FFFFFF', fontWeight: 500 }}>
                {row.name}
              </span>
              <span style={{
                fontSize: isVertical ? 13 : 15, color: PALETTE.CORRECT,
                fontWeight: 700, textAlign: 'right', fontVariantNumeric: 'tabular-nums',
              }}>
                {(row.debit ?? 0).toLocaleString('tr-TR')} ₺
              </span>
            </div>
          )
        })}

        {/* Alacak satırları (girintili) */}
        {creditRows.map((row, i) => {
          const delay = 34 + debitRows.length * 12 + i * 12
          const rOpacity = interpolate(frame, [delay, delay + 16], [0, 1], { extrapolateRight: 'clamp' })
          const rX = interpolate(frame, [delay, delay + 16], [20, 0], { extrapolateRight: 'clamp' })
          return (
            <div key={`c${i}`} style={{
              display: 'grid',
              gridTemplateColumns: isVertical ? '50px 1fr 100px' : '80px 1fr 130px',
              padding: '11px 20px', gap: 10,
              background: i % 2 === 0 ? '#0B1E35' : BG_DARK,
              borderBottom: i < creditRows.length - 1 ? `1px solid ${ACCENT}10` : 'none',
              opacity: rOpacity, transform: `translateX(${rX}px)`,
            }}>
              <span style={{ fontSize: isVertical ? 12 : 14, color: `${ACCENT}80`, fontWeight: 600 }}>
                {row.code ?? '—'}
              </span>
              <span style={{ fontSize: isVertical ? 13 : 15, color: 'rgba(255,255,255,0.72)', paddingLeft: 16, fontStyle: 'italic' }}>
                {row.name}
              </span>
              <span style={{
                fontSize: isVertical ? 13 : 15, color: PALETTE.ACCENT_LT,
                fontWeight: 700, textAlign: 'right', fontVariantNumeric: 'tabular-nums',
              }}>
                {(row.credit ?? 0).toLocaleString('tr-TR')} ₺
              </span>
            </div>
          )
        })}

        {/* Toplam satırı */}
        {rows.length > 0 && (
          <div style={{
            display: 'grid',
            gridTemplateColumns: isVertical ? '50px 1fr 100px' : '80px 1fr 130px',
            padding: '12px 20px', gap: 10,
            background: `${ACCENT}15`,
            borderTop: `2px solid ${ACCENT}40`,
            opacity: interpolate(frame, [60 + rows.length * 10, 76 + rows.length * 10], [0, 1], { extrapolateRight: 'clamp' }),
          }}>
            <span />
            <span style={{ fontSize: isVertical ? 12 : 13, fontWeight: 800, color: PALETTE.TEXT_DIM, letterSpacing: 2 }}>
              TOPLAM
            </span>
            <div style={{ textAlign: 'right' }}>
              <div style={{ fontSize: isVertical ? 11 : 12, color: PALETTE.CORRECT, fontWeight: 700, fontVariantNumeric: 'tabular-nums' }}>
                B: {totalDebit.toLocaleString('tr-TR')} ₺
              </div>
              <div style={{ fontSize: isVertical ? 11 : 12, color: PALETTE.ACCENT_LT, fontWeight: 700, fontVariantNumeric: 'tabular-nums' }}>
                A: {totalCredit.toLocaleString('tr-TR')} ₺
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Açıklama */}
      {scene.explanation && (
        <div style={{
          width: '100%', marginTop: isVertical ? 20 : 18,
          background: `${ACCENT}0A`, border: `1px solid ${ACCENT}20`,
          borderLeft: `4px solid ${ACCENT}`, borderRadius: 10,
          padding: '12px 16px',
          opacity: interpolate(frame, [80, 100], [0, 1], { extrapolateRight: 'clamp' }),
        }}>
          <p style={{ fontSize: isVertical ? 13 : 14, color: PALETTE.TEXT_MID, lineHeight: 1.65, margin: 0 }}>
            {scene.explanation}
          </p>
        </div>
      )}

      {scene.tts_url && <Audio src={scene.tts_url} />}
    </div>
  )
}
