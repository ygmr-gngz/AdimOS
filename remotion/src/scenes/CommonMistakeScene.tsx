/**
 * CommonMistakeScene — sık yapılan hata.
 * Kırmızı uyarı ikonu, "Yanlış" ve "Doğru" iki sütun.
 */
import { AbsoluteFill, useCurrentFrame, interpolate, spring, useVideoConfig } from 'remotion'
import { T } from '../theme/tokens'

interface CommonMistakeSceneProps {
  title?: string
  common_mistake?: string
  wrong_example?: string
  correct_example?: string
  explanation?: string
  bullet_points?: string[]
  voice_text?: string
}

export function CommonMistakeScene({
  title = 'Sık Yapılan Hata',
  common_mistake,
  wrong_example,
  correct_example,
  explanation,
  bullet_points = [],
}: CommonMistakeSceneProps) {
  const frame = useCurrentFrame()
  const { fps } = useVideoConfig()

  const headerProgress = spring({ frame, fps, config: { damping: 14 } })
  const wrongProgress = spring({ frame: Math.max(0, frame - 6), fps, config: { damping: 14 } })
  const rightProgress = spring({ frame: Math.max(0, frame - 12), fps, config: { damping: 14 } })

  return (
    <AbsoluteFill style={{ background: T.color.canvas, fontFamily: T.font.body, padding: T.space.lg }}>
      {/* Başlık */}
      <div style={{
        display: 'flex', alignItems: 'center', gap: T.space.sm,
        marginBottom: T.space.lg,
        opacity: interpolate(headerProgress, [0, 1], [0, 1]),
        transform: `translateY(${interpolate(headerProgress, [0, 1], [30, 0])}px)`,
      }}>
        <span style={{ fontSize: 64 }}>⚠️</span>
        <div>
          <div style={{ fontSize: 60, fontWeight: 800, color: T.color.danger }}>{title}</div>
          {common_mistake && (
            <div style={{ fontSize: 40, color: T.color.text, marginTop: 4 }}>{common_mistake}</div>
          )}
        </div>
      </div>

      <div style={{ display: 'flex', gap: T.space.md, flex: 1 }}>
        {/* Yanlış kutusu */}
        {wrong_example && (
          <div style={{
            flex: 1,
            background: '#FFF5F5',
            border: `3px solid ${T.color.danger}`,
            borderRadius: T.radius.card,
            padding: T.space.md,
            opacity: interpolate(wrongProgress, [0, 1], [0, 1]),
            transform: `translateX(${interpolate(wrongProgress, [0, 1], [-40, 0])}px)`,
          }}>
            <div style={{ fontSize: 36, fontWeight: 700, color: T.color.danger, marginBottom: T.space.sm }}>
              ✗ YANLIŞ
            </div>
            <div style={{
              fontSize: 38, color: T.color.text,
              textDecoration: 'line-through',
              textDecorationColor: T.color.danger,
            }}>
              {wrong_example}
            </div>
          </div>
        )}

        {/* Doğru kutusu */}
        {correct_example && (
          <div style={{
            flex: 1,
            background: '#F0FFF4',
            border: `3px solid ${T.color.green}`,
            borderRadius: T.radius.card,
            padding: T.space.md,
            opacity: interpolate(rightProgress, [0, 1], [0, 1]),
            transform: `translateX(${interpolate(rightProgress, [0, 1], [40, 0])}px)`,
          }}>
            <div style={{ fontSize: 36, fontWeight: 700, color: T.color.green, marginBottom: T.space.sm }}>
              ✓ DOĞRU
            </div>
            <div style={{ fontSize: 38, color: T.color.text }}>{correct_example}</div>
          </div>
        )}
      </div>

      {/* Bullet points modu */}
      {bullet_points.map((bp, i) => {
        const op = interpolate(frame, [i * 4 + 8, i * 4 + 16], [0, 1], { extrapolateRight: 'clamp' })
        return (
          <div key={i} style={{
            opacity: op,
            background: '#FFF5F5',
            border: `2px solid ${T.color.danger}44`,
            borderRadius: T.radius.chip,
            padding: `${T.space.sm}px ${T.space.md}px`,
            marginBottom: T.space.sm,
            display: 'flex', alignItems: 'flex-start', gap: 12,
          }}>
            <span style={{ color: T.color.danger, fontSize: 36 }}>⚠</span>
            <span style={{ fontSize: 40, color: T.color.text }}>{bp}</span>
          </div>
        )
      })}

      {explanation && (
        <div style={{
          marginTop: T.space.md,
          background: `${T.color.gold}22`,
          borderLeft: `6px solid ${T.color.gold}`,
          borderRadius: T.radius.chip,
          padding: T.space.md,
        }}>
          <span style={{ fontSize: 38, color: T.color.navy900 }}>{explanation}</span>
        </div>
      )}
    </AbsoluteFill>
  )
}
