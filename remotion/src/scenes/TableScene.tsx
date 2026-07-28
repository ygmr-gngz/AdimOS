/**
 * TableScene — karşılaştırma tablosu (maks. 4 sütun × 6 satır).
 * Satırlar sırayla belirir.
 */
import { AbsoluteFill, useCurrentFrame, interpolate, useVideoConfig } from 'remotion'
import { T } from '../theme/tokens'

interface TableSceneProps {
  title?: string
  subtitle?: string
  headers: string[]
  rows: string[][]
  highlight_col?: number  // vurgulu sütun indeksi (0-bazlı)
  voice_text?: string
}

export function TableScene({ title, subtitle, headers, rows, highlight_col }: TableSceneProps) {
  const frame = useCurrentFrame()
  const { fps } = useVideoConfig()
  const colCount = headers.length

  return (
    <AbsoluteFill style={{ background: T.color.canvas, fontFamily: T.font.body, padding: T.space.lg }}>
      {title && (
        <div style={{ marginBottom: T.space.md }}>
          <div style={{ fontSize: 64, fontWeight: 800, color: T.color.navy900, lineHeight: 1.1 }}>{title}</div>
          {subtitle && <div style={{ fontSize: 44, color: T.color.muted, marginTop: 8 }}>{subtitle}</div>}
        </div>
      )}

      <div style={{
        background: T.color.surface,
        borderRadius: T.radius.card,
        boxShadow: T.shadow.card,
        overflow: 'hidden',
      }}>
        {/* Başlık satırı */}
        <div style={{
          display: 'grid',
          gridTemplateColumns: `repeat(${colCount}, 1fr)`,
          background: T.color.navy900,
        }}>
          {headers.map((h, i) => (
            <div key={i} style={{
              padding: `${T.space.sm}px ${T.space.md}px`,
              fontSize: 38, fontWeight: 700, color: T.color.surface,
              textAlign: 'center',
              borderRight: i < colCount - 1 ? `1px solid ${T.color.navy700}` : undefined,
              background: i === highlight_col ? T.color.gold : undefined,
              color: i === highlight_col ? T.color.navy900 : T.color.surface,
            }}>
              {h}
            </div>
          ))}
        </div>

        {/* Veri satırları */}
        {rows.slice(0, 6).map((row, ri) => {
          const rowDelay = ri * 4
          const rowOpacity = interpolate(frame, [rowDelay, rowDelay + 8], [0, 1], { extrapolateRight: 'clamp' })
          const rowY = interpolate(frame, [rowDelay, rowDelay + 8], [20, 0], { extrapolateRight: 'clamp' })

          return (
            <div key={ri} style={{
              display: 'grid',
              gridTemplateColumns: `repeat(${colCount}, 1fr)`,
              background: ri % 2 === 0 ? T.color.surface : T.color.canvas,
              opacity: rowOpacity,
              transform: `translateY(${rowY}px)`,
              borderTop: `1px solid ${T.color.border}`,
            }}>
              {row.slice(0, 4).map((cell, ci) => (
                <div key={ci} style={{
                  padding: `${T.space.sm}px ${T.space.md}px`,
                  fontSize: 36, color: T.color.text,
                  textAlign: 'center',
                  borderRight: ci < colCount - 1 ? `1px solid ${T.color.border}` : undefined,
                  fontWeight: ci === highlight_col ? 700 : 400,
                  color: ci === highlight_col ? T.color.navy900 : T.color.text,
                }}>
                  {cell}
                </div>
              ))}
            </div>
          )
        })}
      </div>
    </AbsoluteFill>
  )
}
