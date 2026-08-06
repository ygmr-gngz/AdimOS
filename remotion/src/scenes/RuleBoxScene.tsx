/**
 * RuleBoxScene — kural kutusu (Borç–Alacak çalışma mantığı vb.)
 * Koyu zemin (kasıtlı — diğer 3 kardeşten farklı, CardShell KULLANMAZ),
 * dinamik ölçekleme, emoji yok (SVG ok ikonu).
 */
import { AbsoluteFill, interpolate, useCurrentFrame, useVideoConfig } from 'remotion'
import { T } from '../theme/tokens'
import { IconArrowRight } from '../components/CardIcons'
import { estimateLines, fieldMinScale, solveCardScale } from '../theme/dynamicScale'

interface RuleItem {
  label: string
  left: string   // örn. "Borç → ARTAR"
  right: string  // örn. "Alacak → AZALIR"
}

interface RuleBoxSceneProps {
  title?: string
  subtitle?: string
  rules?: RuleItem[]
  bullet_points?: string[]
  nature?: 'A' | 'P' | 'G' | 'Gi'
  voice_text?: string
  format?: '9:16' | '16:9'
}

export function RuleBoxScene({
  title, subtitle, rules = [], bullet_points = [], nature, format = '9:16',
}: RuleBoxSceneProps) {
  const frame = useCurrentFrame()
  const { height: videoHeight } = useVideoConfig()

  const L = format === '16:9' ? T.layout16x9 : T.layout9x16
  const minScale = fieldMinScale(Object.values(L.font))
  const availableHeight = videoHeight - L.safeTop - L.safeBottom
  const innerWidth = L.cardW - 2 * L.cardPad

  const estimateHeight = (scale: number): number => {
    const title_ = L.font.title.target * scale * 0.7
    const body = L.font.body.target * scale
    const entry = L.font.entry.target * scale
    let h = T.space.lg

    if (title) h += estimateLines(title, title_, innerWidth) * title_ * 1.15
    if (subtitle) h += 8 + estimateLines(subtitle, body * 0.85, innerWidth) * body * 0.85 * 1.4
    if (nature) h += T.space.sm + entry + 16
    h += T.space.lg

    for (const _r of rules) {
      h += entry * 1.5 + T.space.sm * 2 + T.space.sm
    }
    for (const bp of bullet_points) {
      h += estimateLines(bp, body, innerWidth - 60) * body * 1.4 + T.space.sm * 2 + T.space.sm
    }

    return h
  }

  const scale = solveCardScale(estimateHeight, availableHeight, minScale, 'RuleBoxScene')
  const titleFont = L.font.title.target * scale * 0.7
  const bodyFont = L.font.body.target * scale
  const entryFont = L.font.entry.target * scale

  return (
    <AbsoluteFill style={{
      background: T.color.navy900,
      fontFamily: T.font.body,
    }}>
      <div style={{
        position: 'absolute', top: L.safeTop, bottom: L.safeBottom, left: L.safeX, right: L.safeX,
        display: 'flex', flexDirection: 'column', justifyContent: 'center',
      }}>
        {/* Başlık */}
        <div style={{ marginBottom: T.space.lg }}>
          {title && (
            <div style={{ fontSize: titleFont, fontWeight: 800, color: T.color.gold500, lineHeight: 1.15 }}>{title}</div>
          )}
          {subtitle && (
            <div style={{ fontSize: bodyFont * 0.85, color: `${T.color.surface}CC`, marginTop: 8 }}>{subtitle}</div>
          )}
          {nature && (
            <div style={{
              display: 'inline-block', marginTop: T.space.sm,
              background: T.natureColor(nature), color: '#fff',
              borderRadius: T.radius.badge, padding: '8px 24px',
              fontSize: entryFont, fontWeight: 800,
            }}>
              {nature === 'A' ? 'Aktif' : nature === 'P' ? 'Pasif' : nature === 'G' ? 'Gelir' : 'Gider'}
            </div>
          )}
        </div>

        {/* Kural satırları */}
        {rules.map((rule, i) => {
          const delay = i * 5
          const op = interpolate(frame, [delay, delay + 8], [0, 1], { extrapolateRight: 'clamp' })
          return (
            <div key={i} style={{
              opacity: op,
              background: `${T.color.surface}14`,
              border: `1px solid ${T.color.surface}30`,
              borderRadius: T.radius.chip,
              padding: `${T.space.sm}px ${T.space.md}px`,
              marginBottom: T.space.sm,
              display: 'flex', alignItems: 'center', gap: T.space.md,
            }}>
              <div style={{ flex: 1, fontSize: entryFont, fontWeight: 700, color: T.color.gold500 }}>{rule.label}</div>
              <div style={{ fontSize: entryFont * 0.9, color: '#4FC3F7' }}>{rule.left}</div>
              <div style={{ width: 2, height: 32, background: `${T.color.surface}40` }} />
              <div style={{ fontSize: entryFont * 0.9, color: '#EF9A9A' }}>{rule.right}</div>
            </div>
          )
        })}

        {/* Bullet points modu */}
        {bullet_points.map((bp, i) => {
          const delay = i * 5
          const op = interpolate(frame, [delay, delay + 8], [0, 1], { extrapolateRight: 'clamp' })
          return (
            <div key={i} style={{
              opacity: op,
              background: `${T.color.surface}14`,
              border: `1px solid ${T.color.surface}30`,
              borderRadius: T.radius.chip,
              padding: `${T.space.sm}px ${T.space.md}px`,
              marginBottom: T.space.sm,
              display: 'flex', alignItems: 'center', gap: 16,
            }}>
              <div style={{ color: T.color.gold500, flexShrink: 0 }}><IconArrowRight /></div>
              <span style={{ fontSize: bodyFont, color: T.color.surface }}>{bp}</span>
            </div>
          )
        })}
      </div>
    </AbsoluteFill>
  )
}
