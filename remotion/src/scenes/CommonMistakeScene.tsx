/**
 * CommonMistakeScene — sık yapılan hata. Yanlış / Doğru iki sütun.
 * CardShell (zemin/kart/gölge/kenarlık), dinamik ölçekleme, emoji yok (SVG).
 */
import { interpolate, spring, useCurrentFrame, useVideoConfig } from 'remotion'
import { T } from '../theme/tokens'
import { CardShell } from '../components/CardShell'
import { IconWarning, IconCheck } from '../components/CardIcons'
import { estimateLines, fieldMinScale, solveCardScale } from '../theme/dynamicScale'

interface CommonMistakeSceneProps {
  title?: string
  common_mistake?: string
  wrong_example?: string
  correct_example?: string
  explanation?: string
  bullet_points?: string[]
  voice_text?: string
  format?: '9:16' | '16:9'
  canvasColor?: string   // still fon override (2026-08-08) — kart zemini etkilenmez
}

export function CommonMistakeScene({
  title = 'Sık Yapılan Hata',
  common_mistake,
  wrong_example,
  correct_example,
  explanation,
  bullet_points = [],
  format = '9:16',
  canvasColor,
}: CommonMistakeSceneProps) {
  const frame = useCurrentFrame()
  const { fps, height: videoHeight } = useVideoConfig()

  const cardProgress = spring({ frame, fps, config: { damping: 14, stiffness: 100 } })
  const cardY = interpolate(cardProgress, [0, 1], [60, 0])
  const cardOpacity = interpolate(cardProgress, [0, 1], [0, 1])

  const headerProgress = spring({ frame, fps, config: { damping: 14 } })
  const wrongProgress = spring({ frame: Math.max(0, frame - 6), fps, config: { damping: 14 } })
  const rightProgress = spring({ frame: Math.max(0, frame - 12), fps, config: { damping: 14 } })

  const L = format === '16:9' ? T.layout16x9 : T.layout9x16
  const minScale = fieldMinScale(Object.values(L.font))
  const availableHeight = videoHeight - L.safeTop - L.safeBottom
  const innerWidth = L.cardW - 2 * L.cardPad
  const colWidth = (innerWidth - T.space.md) / 2

  const estimateHeight = (scale: number): number => {
    const title_ = L.font.title.target * scale
    const body = L.font.body.target * scale
    const label = L.font.label.target * scale
    let h = T.space.lg * 2 + 40 // üst/alt dolgu + ikon satırı payı

    h += estimateLines(title, title_ * 0.65, innerWidth - 60) * title_ * 0.65 * 1.15
    if (common_mistake) {
      h += 4 + estimateLines(common_mistake, body * 0.75, innerWidth - 60) * body * 0.75 * 1.4
    }
    h += T.space.lg

    if (wrong_example || correct_example) {
      const wrongH = wrong_example
        ? label + 8 + estimateLines(wrong_example, body, colWidth - T.space.md * 2) * body * 1.4 + T.space.md * 2
        : 0
      const correctH = correct_example
        ? label + 8 + estimateLines(correct_example, body, colWidth - T.space.md * 2) * body * 1.4 + T.space.md * 2
        : 0
      h += Math.max(wrongH, correctH)
    }

    if (bullet_points.length > 0) {
      for (const bp of bullet_points) {
        h += estimateLines(bp, body, innerWidth - 60) * body * 1.4 + T.space.sm * 2 + T.space.sm
      }
    }

    if (explanation) {
      h += T.space.md + estimateLines(explanation, body, innerWidth - 40) * body * 1.5 + T.space.md * 2
    }

    return h
  }

  const scale = solveCardScale(estimateHeight, availableHeight, minScale, 'CommonMistakeScene')
  const titleFont = L.font.title.target * scale * 0.65
  const bodyFont = L.font.body.target * scale
  const labelFont = L.font.label.target * scale

  return (
    <CardShell format={format} opacity={cardOpacity} translateY={cardY} canvasColor={canvasColor}>
      <div style={{ padding: `${T.space.lg}px ${L.cardPad}px 0` }}>
        {/* Başlık */}
        <div style={{
          display: 'flex', alignItems: 'center', gap: T.space.sm,
          marginBottom: T.space.lg,
          opacity: interpolate(headerProgress, [0, 1], [0, 1]),
          transform: `translateY(${interpolate(headerProgress, [0, 1], [30, 0])}px)`,
        }}>
          <div style={{
            width: 40, height: 40, borderRadius: '50%', flexShrink: 0,
            background: T.color.crimson, color: '#FFFFFF',
            display: 'flex', alignItems: 'center', justifyContent: 'center',
          }}>
            <IconWarning />
          </div>
          <div>
            <div style={{ fontSize: titleFont, fontWeight: 800, color: T.color.crimson, lineHeight: 1.2 }}>{title}</div>
            {common_mistake && (
              <div style={{ fontSize: bodyFont * 0.75, color: T.color.text, marginTop: 4 }}>{common_mistake}</div>
            )}
          </div>
        </div>

        {(wrong_example || correct_example) && (
          <div style={{ display: 'flex', gap: T.space.md, marginBottom: T.space.lg }}>
            {/* Yanlış kutusu */}
            {wrong_example && (
              <div style={{
                flex: 1,
                background: '#FFF5F5',
                border: `2px solid ${T.color.crimson}`,
                borderRadius: T.radius.chip,
                padding: T.space.md,
                opacity: interpolate(wrongProgress, [0, 1], [0, 1]),
                transform: `translateX(${interpolate(wrongProgress, [0, 1], [-40, 0])}px)`,
              }}>
                <div style={{ fontSize: labelFont, fontWeight: 700, color: T.color.crimson, marginBottom: 8 }}>
                  YANLIŞ
                </div>
                <div style={{
                  fontSize: bodyFont, color: T.color.text,
                  textDecoration: 'line-through', textDecorationColor: T.color.crimson,
                  lineHeight: 1.4,
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
                border: `2px solid ${T.color.green700}`,
                borderRadius: T.radius.chip,
                padding: T.space.md,
                opacity: interpolate(rightProgress, [0, 1], [0, 1]),
                transform: `translateX(${interpolate(rightProgress, [0, 1], [40, 0])}px)`,
              }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: 6, marginBottom: 8 }}>
                  <div style={{ color: T.color.green700 }}><IconCheck /></div>
                  <span style={{ fontSize: labelFont, fontWeight: 700, color: T.color.green700 }}>DOĞRU</span>
                </div>
                <div style={{ fontSize: bodyFont, color: T.color.text, lineHeight: 1.4 }}>{correct_example}</div>
              </div>
            )}
          </div>
        )}

        {/* Bullet points modu */}
        {bullet_points.map((bp, i) => {
          const op = interpolate(frame, [i * 4 + 8, i * 4 + 16], [0, 1], { extrapolateRight: 'clamp' })
          return (
            <div key={i} style={{
              opacity: op,
              background: '#FFF5F5',
              border: `1.5px solid ${T.color.crimson}44`,
              borderRadius: T.radius.chip,
              padding: `${T.space.sm}px ${T.space.md}px`,
              marginBottom: T.space.sm,
              display: 'flex', alignItems: 'flex-start', gap: 12,
            }}>
              <div style={{ color: T.color.crimson, flexShrink: 0, marginTop: 2 }}><IconWarning /></div>
              <span style={{ fontSize: bodyFont, color: T.color.text, lineHeight: 1.4 }}>{bp}</span>
            </div>
          )
        })}
      </div>

      {explanation && (
        <div style={{
          margin: `0 ${L.cardPad}px ${T.space.lg}px`,
          background: `${T.color.gold500}22`,
          borderLeft: `5px solid ${T.color.gold500}`,
          borderRadius: T.radius.chip,
          padding: T.space.md,
        }}>
          <span style={{ fontSize: bodyFont, color: T.color.navy900, lineHeight: 1.5 }}>{explanation}</span>
        </div>
      )}
    </CardShell>
  )
}
