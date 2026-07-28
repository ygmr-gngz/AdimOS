/**
 * AccountCardScene — SGS/muhasebe hesap kartı.
 * Hesap kodu, nitelik rozeti (A/P/G/Gi), 4 bölümlü kart.
 */
import { AbsoluteFill, useCurrentFrame, interpolate, spring, useVideoConfig } from 'remotion'
import { T } from '../theme/tokens'

interface JournalLine {
  code: string
  name: string
  side: 'debit' | 'credit'
  amount?: string
}

interface AccountCardSceneProps {
  accountCode?: string
  accountName?: string
  nature?: 'A' | 'P' | 'G' | 'Gi'
  purpose?: string
  debitCredit?: string
  journalEntry?: JournalLine[]
  entryCaption?: string
  tip?: string
  // EducationalReelScene uyumluluğu
  title?: string
  bullet_points?: string[]
  voice_text?: string
}

export function AccountCardScene({
  accountCode = '100',
  accountName = 'HESAP',
  nature = 'A',
  purpose,
  debitCredit,
  journalEntry = [],
  entryCaption,
  tip,
  title,
  bullet_points,
}: AccountCardSceneProps) {
  const frame = useCurrentFrame()
  const { fps } = useVideoConfig()

  const cardProgress = spring({ frame, fps, config: { damping: 14, stiffness: 100 } })
  const cardY = interpolate(cardProgress, [0, 1], [60, 0])
  const cardOpacity = interpolate(cardProgress, [0, 1], [0, 1])

  const displayName = title || accountName
  const nColor = T.natureColor(nature)

  return (
    <AbsoluteFill style={{ background: T.color.canvas, fontFamily: T.font.body }}>
      {/* Üst başlık şeridi */}
      <div style={{
        background: T.color.navy900,
        padding: `${T.space.md}px ${T.space.lg}px`,
        display: 'flex', alignItems: 'center', justifyContent: 'space-between',
      }}>
        {/* Hesap kodu rozeti */}
        <div style={{
          background: T.color.gold, color: T.color.navy900,
          borderRadius: T.radius.badge, padding: '10px 28px',
          fontSize: 52, fontWeight: 900, letterSpacing: '0.04em',
        }}>
          {accountCode}
        </div>
        <div style={{ color: T.color.surface, fontSize: 54, fontWeight: 700, flex: 1, marginLeft: T.space.md }}>
          {displayName}
        </div>
        {/* Nitelik rozeti */}
        <div style={{
          background: nColor, color: '#fff',
          borderRadius: T.radius.badge, padding: '10px 24px',
          fontSize: 44, fontWeight: 800,
        }}>
          {nature}
        </div>
      </div>

      {/* Ana kart */}
      <div style={{
        margin: T.space.md,
        background: T.color.surface,
        borderRadius: T.radius.card,
        boxShadow: T.shadow.card,
        padding: T.space.lg,
        opacity: cardOpacity,
        transform: `translateY(${cardY}px)`,
        display: 'flex', flexDirection: 'column', gap: T.space.md,
      }}>

        {/* Amaç */}
        {purpose && (
          <Section icon="📌" label="Amaç">
            <span style={{ fontSize: 40, color: T.color.text }}>{purpose}</span>
          </Section>
        )}

        {/* Borç / Alacak kuralı */}
        {debitCredit && (
          <Section icon="⚖️" label="Borç / Alacak">
            <span style={{ fontSize: 40, color: T.color.navy700, fontWeight: 600 }}>{debitCredit}</span>
          </Section>
        )}

        {/* Bullet points (genel içerik) */}
        {bullet_points && bullet_points.length > 0 && (
          <Section icon="📋" label="Bilgiler">
            {bullet_points.map((bp, i) => (
              <div key={i} style={{ display: 'flex', alignItems: 'flex-start', gap: 12, marginBottom: 8 }}>
                <span style={{ color: T.color.gold, fontSize: 32, lineHeight: '44px' }}>▶</span>
                <span style={{ fontSize: 38, color: T.color.text }}>{bp}</span>
              </div>
            ))}
          </Section>
        )}

        {/* Yevmiye kaydı */}
        {journalEntry.length > 0 && (
          <Section icon="📒" label="Örnek Yevmiye Kaydı">
            <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
              {journalEntry.map((line, i) => (
                <div key={i} style={{
                  display: 'flex', justifyContent: 'space-between',
                  paddingLeft: line.side === 'credit' ? 56 : 0,
                  borderBottom: i < journalEntry.length - 1 ? `1px solid ${T.color.border}` : undefined,
                  paddingBottom: 6,
                }}>
                  <span style={{ fontSize: 36, color: T.color.text }}>
                    <span style={{ color: T.color.navy500, fontWeight: 700, marginRight: 8 }}>{line.code}</span>
                    {line.name}
                  </span>
                  {line.amount && (
                    <span style={{ fontSize: 36, fontWeight: 700, color: line.side === 'debit' ? T.color.navy900 : T.color.muted }}>
                      {line.amount}
                    </span>
                  )}
                </div>
              ))}
              {entryCaption && (
                <div style={{ fontSize: 32, color: T.color.muted, marginTop: 4, fontStyle: 'italic' }}>
                  {entryCaption}
                </div>
              )}
            </div>
          </Section>
        )}

        {/* Püf Noktası */}
        {tip && (
          <div style={{
            background: `${T.color.gold}22`,
            borderLeft: `6px solid ${T.color.gold}`,
            borderRadius: T.radius.chip,
            padding: `${T.space.sm}px ${T.space.md}px`,
          }}>
            <span style={{ fontSize: 32, marginRight: 8 }}>💡</span>
            <span style={{ fontSize: 38, color: T.color.navy900 }}>{tip}</span>
          </div>
        )}
      </div>
    </AbsoluteFill>
  )
}

function Section({ icon, label, children }: { icon: string; label: string; children: React.ReactNode }) {
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
        <span style={{ fontSize: 34 }}>{icon}</span>
        <span style={{ fontSize: 34, fontWeight: 700, color: T.color.muted, letterSpacing: '0.05em' }}>
          {label.toUpperCase()}
        </span>
      </div>
      <div style={{ paddingLeft: 44 }}>{children}</div>
    </div>
  )
}
