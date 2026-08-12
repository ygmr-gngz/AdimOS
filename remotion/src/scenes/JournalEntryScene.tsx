/**
 * JournalEntryScene — tam ekran yevmiye kaydı.
 *
 * İKİ ÇAĞRI DESENİ bir arada desteklenir:
 *  - EducationalReel120: sahne alanlarını DÜZ prop olarak yayıyor ({...p}) —
 *    bu yolda eski {scene,brand} imzası hiç çalışmıyordu (undefined, ilk
 *    erişimde çökerdi). Bu gerçek, düzeltilmesi gereken bir hataydı.
 *  - LessonVideo / QuizVideo: {scene, brand} sarmalayıcısı ile çağırıyor,
 *    scene.journal_rows (code/name/debit?/credit? — AYRI alanlar) kullanıyor.
 *    Bu yol GERÇEKTEN ÇALIŞIYORDU — kart sistemi yeniden tasarımı bunu
 *    KIRMAMALI, kapsam dışı bir composition ailesi.
 * normalizeProps() ikisini de AccountCardScene'in journalEntry şekline
 * (code/name/side/amount) çevirir — CardShell/dinamik ölçekleme/denklik
 * çubuğu her iki çağrı yolunda da aynı şekilde çalışır.
 */
import { interpolate, spring, useCurrentFrame, useVideoConfig } from 'remotion'
import { T } from '../theme/tokens'
import { CardShell } from '../components/CardShell'
import { IconCheck } from '../components/CardIcons'
import { estimateLines, fieldMinScale, solveCardScale } from '../theme/dynamicScale'

interface JournalLine {
  code: string
  name: string
  side: 'debit' | 'credit'
  amount?: string
}

interface FlatProps {
  title?: string
  journalEntry?: JournalLine[]
  entryCaption?: string
  explanation?: string
  voice_text?: string
  format?: '9:16' | '16:9'
  canvasColor?: string   // still fon override (2026-08-08) — kart zemini etkilenmez
}

interface LegacyJournalRow {
  code?: string
  name: string
  debit?: number
  credit?: number
}

interface LegacyProps {
  scene: {
    title?: string
    journal_rows?: LegacyJournalRow[]
    explanation?: string
    entryCaption?: string
  }
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  brand?: any
  format?: '9:16' | '16:9'
}

type JournalEntrySceneProps = FlatProps | LegacyProps

const SECTION_INDENT = 0

function parseTurkishAmount(raw: string | undefined): number {
  if (!raw) return 0
  const s = raw.trim().replace(/\./g, '').replace(',', '.')
  const n = parseFloat(s)
  return isNaN(n) ? 0 : n
}

function formatTurkishAmount(n: number): string {
  return n.toLocaleString('tr-TR', { maximumFractionDigits: 2 })
}

function normalizeProps(props: JournalEntrySceneProps): FlatProps {
  if ('scene' in props && props.scene) {
    const s = props.scene
    const journalEntry: JournalLine[] = (s.journal_rows ?? []).map(r => ({
      code: r.code ?? '',
      name: r.name,
      side: r.debit !== undefined ? 'debit' as const : 'credit' as const,
      amount: formatTurkishAmount(r.debit !== undefined ? r.debit : (r.credit ?? 0)),
    }))
    return {
      title: s.title,
      journalEntry,
      entryCaption: s.entryCaption,
      explanation: s.explanation,
      format: props.format,
    }
  }
  return props
}

export function JournalEntryScene(rawProps: JournalEntrySceneProps) {
  const { title, journalEntry = [], entryCaption, explanation, format = '9:16', canvasColor } = normalizeProps(rawProps)
  const frame = useCurrentFrame()
  const { fps, height: videoHeight } = useVideoConfig()

  const cardProgress = spring({ frame, fps, config: { damping: 14, stiffness: 100 } })
  const cardY = interpolate(cardProgress, [0, 1], [60, 0])
  const cardOpacity = interpolate(cardProgress, [0, 1], [0, 1])

  const L = format === '16:9' ? T.layout16x9 : T.layout9x16
  const minScale = fieldMinScale(Object.values(L.font))
  const availableHeight = videoHeight - L.safeTop - L.safeBottom
  const innerWidth = L.cardW - 2 * L.cardPad

  const debitTotal = journalEntry.filter(l => l.side === 'debit').reduce((s, l) => s + parseTurkishAmount(l.amount), 0)
  const creditTotal = journalEntry.filter(l => l.side === 'credit').reduce((s, l) => s + parseTurkishAmount(l.amount), 0)
  const balanced = Math.abs(debitTotal - creditTotal) < 0.01

  const estimateHeight = (scale: number): number => {
    const title_ = L.font.title.target * scale * 0.75
    const entry = L.font.entry.target * scale
    let h = T.space.lg * 2

    if (title) h += estimateLines(title, title_, innerWidth) * title_ * 1.15 + T.space.lg
    h += entry * 1.2 + T.space.sm * 2  // yevmiye tablosu başlık satırı
    h += journalEntry.length * (entry * 1.7)
    if (entryCaption) h += L.captionFont * 1.4 + 6
    h += T.space.md + entry * 1.5 + T.space.md * 2  // denklik çubuğu
    if (explanation) {
      h += T.space.md + estimateLines(explanation, L.font.body.target * scale, innerWidth - 40) * L.font.body.target * scale * 1.5 + T.space.md * 2
    }

    return h
  }

  const scale = solveCardScale(estimateHeight, availableHeight, minScale, 'JournalEntryScene')
  const titleFont = L.font.title.target * scale * 0.75
  const bodyFont = L.font.body.target * scale
  const entryFont = L.font.entry.target * scale

  return (
    <CardShell format={format} opacity={cardOpacity} translateY={cardY} canvasColor={canvasColor}>
      <div style={{ padding: `${T.space.lg}px ${L.cardPad}px 0` }}>
        {title && (
          <div style={{
            fontSize: titleFont, fontWeight: 800, color: T.color.navy900,
            lineHeight: 1.15, marginBottom: T.space.lg,
          }}>
            {title}
          </div>
        )}

        {/* Yevmiye kaydı tablosu */}
        <div style={{
          borderRadius: T.radius.chip, overflow: 'hidden', border: `1px solid ${T.color.border}`,
        }}>
          <div style={{
            display: 'flex', justifyContent: 'space-between',
            background: T.color.navy900, color: T.color.surface,
            padding: `${T.space.sm}px ${T.space.md}px`,
            fontSize: entryFont * 0.7, fontWeight: 700, letterSpacing: 1,
            textTransform: 'uppercase' as const,
          }}>
            <span>Hesap</span>
            <span>Tutar</span>
          </div>
          <div style={{ padding: `${T.space.sm}px ${T.space.md}px`, display: 'flex', flexDirection: 'column', gap: 10 }}>
            {journalEntry.map((line, i) => {
              const delay = i * 6
              const op = interpolate(frame, [delay, delay + 12], [0, 1], { extrapolateRight: 'clamp' })
              return (
                <div key={i} style={{
                  display: 'flex', justifyContent: 'space-between', alignItems: 'baseline',
                  paddingLeft: line.side === 'credit' ? L.entryIndent : SECTION_INDENT,
                  opacity: op,
                }}>
                  <span style={{ fontSize: entryFont, color: T.color.text }}>
                    <span style={{ color: T.color.navy500, fontWeight: 700, marginRight: 8 }}>{line.code}</span>
                    {line.name}
                  </span>
                  {line.amount && (
                    <span style={{
                      fontSize: entryFont, fontWeight: 700, color: T.color.navy900,
                      fontVariantNumeric: 'tabular-nums',
                    }}>
                      {line.amount}
                    </span>
                  )}
                </div>
              )
            })}
          </div>
          {entryCaption && (
            <div style={{
              padding: `0 ${T.space.md}px ${T.space.sm}px`,
              fontSize: L.captionFont, color: T.color.muted, fontStyle: 'italic',
            }}>
              {entryCaption}
            </div>
          )}
        </div>

        {/* Borç = Alacak denklik çubuğu */}
        {journalEntry.length > 0 && (
          <div style={{
            marginTop: T.space.md,
            background: balanced ? `${T.color.green700}14` : `${T.color.crimson}14`,
            border: `1.5px solid ${balanced ? T.color.green700 : T.color.crimson}`,
            borderRadius: T.radius.chip,
            padding: `${T.space.sm}px ${T.space.md}px`,
            display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 12,
          }}>
            <div style={{ color: balanced ? T.color.green700 : T.color.crimson, flexShrink: 0 }}>
              <IconCheck />
            </div>
            <span style={{
              fontSize: entryFont, fontWeight: 700,
              color: balanced ? T.color.green700 : T.color.crimson,
              fontVariantNumeric: 'tabular-nums',
            }}>
              Borç {formatTurkishAmount(debitTotal)} = Alacak {formatTurkishAmount(creditTotal)}
            </span>
          </div>
        )}
      </div>

      {explanation && (
        <div style={{
          margin: `${T.space.lg}px ${L.cardPad}px ${T.space.lg}px`,
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
