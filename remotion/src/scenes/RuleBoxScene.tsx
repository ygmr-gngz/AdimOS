/**
 * RuleBoxScene — kural kutusu (Borç–Alacak çalışma mantığı vb.)
 * Koyu zemin, 4 kural satırı, sol/sağ (artar/azalır) ayrımı.
 */
import { AbsoluteFill, useCurrentFrame, interpolate } from 'remotion'
import { T } from '../theme/tokens'

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
}

export function RuleBoxScene({ title, subtitle, rules = [], bullet_points = [], nature }: RuleBoxSceneProps) {
  const frame = useCurrentFrame()

  return (
    <AbsoluteFill style={{
      background: T.color.navy900,
      fontFamily: T.font.body,
      padding: T.space.lg,
      display: 'flex', flexDirection: 'column',
    }}>
      {/* Başlık */}
      <div style={{ marginBottom: T.space.lg }}>
        {title && (
          <div style={{ fontSize: 64, fontWeight: 800, color: T.color.gold, lineHeight: 1.1 }}>{title}</div>
        )}
        {subtitle && (
          <div style={{ fontSize: 42, color: `${T.color.surface}CC`, marginTop: 8 }}>{subtitle}</div>
        )}
        {nature && (
          <div style={{
            display: 'inline-block', marginTop: T.space.sm,
            background: T.natureColor(nature), color: '#fff',
            borderRadius: T.radius.badge, padding: '8px 24px',
            fontSize: 40, fontWeight: 800,
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
            <div style={{ flex: 1, fontSize: 40, fontWeight: 700, color: T.color.gold }}>{rule.label}</div>
            <div style={{ fontSize: 36, color: '#4FC3F7' }}>{rule.left}</div>
            <div style={{ width: 2, height: 32, background: `${T.color.surface}40` }} />
            <div style={{ fontSize: 36, color: '#EF9A9A' }}>{rule.right}</div>
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
            <span style={{ color: T.color.gold, fontSize: 36 }}>▶</span>
            <span style={{ fontSize: 40, color: T.color.surface }}>{bp}</span>
          </div>
        )
      })}
    </AbsoluteFill>
  )
}
