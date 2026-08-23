/**
 * TableScene — karşılaştırma tablosu (maks. 4 sütun × 6 satır).
 * Zebra satırlar, CardShell (zemin/kart/gölge/kenarlık), dinamik ölçekleme.
 */
import { interpolate, useCurrentFrame, useVideoConfig } from 'remotion'
import { T } from '../theme/tokens'
import { CardShell } from '../components/CardShell'
import { estimateLines, fieldMinScale, solveCardScale } from '../theme/dynamicScale'

interface TableSceneProps {
  title?: string
  subtitle?: string
  headers: string[]
  rows: string[][]
  highlight_col?: number  // vurgulu sütun indeksi (0-bazlı)
  voice_text?: string
  format?: '9:16' | '16:9'
  canvasColor?: string   // still fon override (2026-08-08) — kart zemini etkilenmez
}

export function TableScene({
  title, subtitle, headers, rows, highlight_col, format = '9:16', canvasColor,
}: TableSceneProps) {
  const frame = useCurrentFrame()
  const { height: videoHeight } = useVideoConfig()
  const colCount = headers.length
  const visibleRows = rows.slice(0, 6)

  // Tablo geometrisi hareket etmez: çizgiler oluşur, sonra hücreler yazılır.
  const cardOpacity = interpolate(frame, [0, 10], [0, 1], { extrapolateRight: 'clamp' })

  const L = format === '16:9' ? T.layout16x9 : T.layout9x16
  const minScale = fieldMinScale(Object.values(L.font))
  const availableHeight = videoHeight - L.safeTop - L.safeBottom
  const innerWidth = L.cardW - 2 * L.cardPad
  const colWidth = innerWidth / Math.max(1, colCount)

  const estimateHeight = (scale: number): number => {
    const title_ = L.font.title.target * scale
    const body = L.font.body.target * scale
    const entry = L.font.entry.target * scale
    let h = T.space.lg  // üst dolgu

    if (title) {
      h += estimateLines(title, title_, innerWidth) * title_ * 1.15
    }
    if (subtitle) {
      h += 8 + estimateLines(subtitle, body * 0.7, innerWidth) * body * 0.7 * 1.4
    }
    if (title || subtitle) h += T.space.md

    // Başlık satırı
    const headerLines = Math.max(...headers.map(h_ => estimateLines(h_, entry, colWidth)), 1)
    h += headerLines * entry * 1.8 + T.space.sm * 2

    // Veri satırları
    for (const row of visibleRows) {
      const lines = Math.max(...row.slice(0, colCount).map(c => estimateLines(c, entry, colWidth)), 1)
      h += lines * entry * 1.7 + T.space.sm * 2
    }

    h += T.space.lg  // alt dolgu
    return h
  }

  const scale = solveCardScale(estimateHeight, availableHeight, minScale, 'TableScene')
  const titleFont = L.font.title.target * scale
  const bodyFont = L.font.body.target * scale
  const entryFont = L.font.entry.target * scale

  return (
    <CardShell format={format} opacity={cardOpacity} translateY={0} canvasColor={canvasColor}>
      <div style={{ padding: `${T.space.lg}px ${L.cardPad}px 0` }}>
        {title && (
          <div style={{ fontSize: titleFont, fontWeight: 800, color: T.color.navy900, lineHeight: 1.15 }}>
            {title}
          </div>
        )}
        {subtitle && (
          <div style={{ fontSize: bodyFont * 0.7, color: T.color.muted, marginTop: 8 }}>
            {subtitle}
          </div>
        )}
      </div>

      <div style={{ position: 'relative', margin: `${T.space.md}px ${L.cardPad}px ${T.space.lg}px`, borderRadius: T.radius.chip, overflow: 'hidden', border: `1px solid ${T.color.border}` }}>
        {/* Başlık satırı */}
        <div style={{
          display: 'grid',
          gridTemplateColumns: `repeat(${colCount}, 1fr)`,
          background: T.color.navy900,
        }}>
          {headers.map((h, i) => (
            <div key={i} style={{
              padding: `${T.space.sm}px ${T.space.md}px`,
              fontSize: entryFont, fontWeight: 700,
              textAlign: 'center',
              borderRight: i < colCount - 1 ? `1px solid ${T.color.navy700}` : undefined,
              background: i === highlight_col ? T.color.gold500 : undefined,
              color: i === highlight_col ? T.color.navy900 : T.color.surface,
            }}>
              {h.slice(0, Math.ceil(h.length * interpolate(frame, [12 + i * 5, 28 + i * 5], [0, 1], { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' })))}
            </div>
          ))}
        </div>

        {/* Veri satırları — zebra */}
        {visibleRows.map((row, ri) => {
          const rowDelay = 32 + ri * 12

          return (
            <div key={ri} style={{
              display: 'grid',
              gridTemplateColumns: `repeat(${colCount}, 1fr)`,
              background: ri % 2 === 0 ? T.color.surface : T.color.canvas,
              borderTop: `1px solid ${T.color.border}`,
            }}>
              {row.slice(0, colCount).map((cell, ci) => (
                <div key={ci} style={{
                  padding: `${T.space.sm}px ${T.space.md}px`,
                  fontSize: entryFont,
                  textAlign: 'center',
                  borderRight: ci < colCount - 1 ? `1px solid ${T.color.border}` : undefined,
                  fontWeight: ci === highlight_col ? 700 : 400,
                  color: ci === highlight_col ? T.color.navy900 : T.color.text,
                  fontVariantNumeric: 'tabular-nums',
                }}>
                  {cell.slice(0, Math.ceil(cell.length * interpolate(frame, [rowDelay + ci * 3, rowDelay + 10 + ci * 3], [0, 1], { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' })))}
                </div>
              ))}
            </div>
          )
        })}
        <svg viewBox="0 0 1000 1000" preserveAspectRatio="none" style={{ position: 'absolute', inset: 0, width: '100%', height: '100%', pointerEvents: 'none' }}>
          <rect x="3" y="3" width="994" height="994" rx="24" fill="none" stroke={T.color.navy900} strokeWidth="6" vectorEffect="non-scaling-stroke" strokeDasharray="4000" strokeDashoffset={4000 * (1 - interpolate(frame, [0, 24], [0, 1], { extrapolateRight: 'clamp' }))} />
        </svg>
      </div>
    </CardShell>
  )
}
