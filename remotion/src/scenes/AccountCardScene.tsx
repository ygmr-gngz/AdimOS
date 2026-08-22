/**
 * AccountCardScene — SGS/muhasebe hesap kartı (9:16 reels).
 *
 * Kart anatomisi (5 satır):
 *   1. Başlık şeridi — kod rozeti (nitelik rengi) + hesap adı + nitelik rozeti (tam daire)
 *   2. Amaç
 *   3. Borç / Alacak — kural cümlesi nature'dan türetilir, props'tan GELMEZ
 *   4. Örnek Yevmiye Kaydı — borçlu girintisiz, alacaklı girintili, tutar sağa hizalı
 *   5. Püf Noktası — nitelik renginin %8 opaklıklı zemini
 *
 * Bölümler arası çizgi yok — ayrım ikon + etiket ile sağlanır. İkonlar SVG
 * (emoji değil), 24×24 viewBox, 2px çizgi, currentColor.
 *
 * Dinamik ölçekleme: sabit token değerleri kısa içerikte boşluk bırakıyor,
 * uzun içerikte taşıyordu (bkz. commit geçmişi — aynı fixture kısa/uzun
 * içerikle test edildi). Tek bir scale katsayısı (T.layout9x16.font.*'daki
 * min/target oranlarının en kısıtlayıcısına kadar) tüm font boyutlarına
 * birlikte uygulanır. Taban altına inmeden sığmıyorsa layout_overflow
 * fırlatılır — sessiz kırpma yok.
 */
import { AbsoluteFill, interpolate, spring, useCurrentFrame, useVideoConfig } from 'remotion'
import { T } from '../theme/tokens'
import { estimateLines, fieldMinScale, solveCardScale } from '../theme/dynamicScale'

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
  journalEntry?: JournalLine[]
  entryCaption?: string
  tip?: string
  /** 9:16 tek sütun, 16:9 iki sütun kullanır. */
  format?: '9:16' | '16:9'
  canvasColor?: string   // still fon override (2026-08-08) — kart zemini etkilenmez
}

// ── İkonlar — SVG, 24×24, 2px çizgi, currentColor (emoji yasak) ──────

function IconTarget() {
  return (
    <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor"
      strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <circle cx="12" cy="12" r="9" />
      <circle cx="12" cy="12" r="5" />
      <circle cx="12" cy="12" r="1.4" fill="currentColor" />
    </svg>
  )
}

function IconScale() {
  return (
    <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor"
      strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M12 3v17" />
      <path d="M7 20h10" />
      <path d="M5 7h14" />
      <path d="M5 7l-3 6a3 3 0 006 0L5 7z" />
      <path d="M19 7l-3 6a3 3 0 006 0l-3-6z" />
    </svg>
  )
}

function IconLedger() {
  return (
    <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor"
      strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M5 3.5A2.5 2.5 0 017.5 1H19v20H7.5A2.5 2.5 0 015 18.5v-15z" />
      <path d="M5 18.5A2.5 2.5 0 007.5 21H19" />
      <path d="M9 7h6M9 11h6" />
    </svg>
  )
}

function IconBulb() {
  return (
    <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor"
      strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M9 18h6" />
      <path d="M10 22h4" />
      <path d="M12 2a7 7 0 00-4 12.7c.6.5 1 1.2 1 2.3h6c0-1.1.4-1.8 1-2.3A7 7 0 0012 2z" />
    </svg>
  )
}

// Referans infografikteki gibi: renkli dairesel rozet içinde beyaz ikon +
// renkli kalın etiket (muted gri/uppercase DEĞİL — referansta etiket rengi
// nitelik rengiyle aynı, harf büyüklüğü normal başlık biçimi).
const ICON_CHIP_SIZE = 30
export const SECTION_INDENT = ICON_CHIP_SIZE + 12

function SectionHeader({ icon, label, color, fontSize }: {
  icon: React.ReactNode; label: string; color: string; fontSize: number
}) {
  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
      <div style={{
        width: ICON_CHIP_SIZE, height: ICON_CHIP_SIZE, borderRadius: '50%',
        background: color, color: '#FFFFFF', flexShrink: 0,
        display: 'flex', alignItems: 'center', justifyContent: 'center',
      }}>
        {icon}
      </div>
      <span style={{ fontSize, fontWeight: 700, color }}>
        {label}
      </span>
    </div>
  )
}

export function AccountCardScene({
  accountCode = '100',
  accountName = 'HESAP',
  nature = 'A',
  purpose,
  journalEntry = [],
  entryCaption,
  tip,
  format = '9:16',
  canvasColor,
}: AccountCardSceneProps) {
  const frame = useCurrentFrame()
  const { fps, height: videoHeight } = useVideoConfig()

  const cardProgress = spring({ frame, fps, config: { damping: 14, stiffness: 100 } })
  const cardY = interpolate(cardProgress, [0, 1], [60, 0])
  const cardOpacity = interpolate(cardProgress, [0, 1], [0, 1])

  const nColor = T.natureColor(nature)
  const natureRule = T.natureRule(nature)   // props'tan DEĞİL — LLM yazamaz
  const L = format === '16:9' ? T.layout16x9 : T.layout9x16

  // ── Dinamik ölçek — tek katsayı, tüm scaled fontlara birlikte uygulanır ──
  const minScale = fieldMinScale(Object.values(L.font))
  const availableHeight = videoHeight - L.safeTop - L.safeBottom
  const innerWidth = L.cardW - 2 * L.cardPad
  const sectionTextWidth = innerWidth - SECTION_INDENT
  const HEADER_ROW_V_PAD = T.space.md * 2
  const CONTENT_BOTTOM_PAD = T.space.lg

  const estimateHeight = (scale: number): number => {
    const title = L.font.title.target * scale
    const body = L.font.body.target * scale
    const label = L.font.label.target * scale
    const entry = L.font.entry.target * scale
    const tipSize = L.font.tip.target * scale

    // 1. Başlık şeridi — kod/nitelik rozeti sabit, hesap adı ölçekli
    const titleTextWidth = innerWidth - 200 // kod rozeti + nitelik rozeti + aralıklar için kaba pay
    const titleLines = estimateLines(accountName, title, titleTextWidth)
    const headerRowH = Math.max(L.codeBadgeFont + 16, titleLines * title * 1.15, L.natureBadge) + HEADER_ROW_V_PAD

    let h = headerRowH

    if (format === '16:9') {
      const columnWidth = (innerWidth - L.sectionGap) / 2
      const columnTextWidth = columnWidth - SECTION_INDENT
      let left = 0
      let leftSections = 0
      if (purpose) {
        left += label * 1.3 + 8
        left += estimateLines(purpose, body, columnTextWidth) * body * 1.5
        leftSections++
      }
      left += label * 1.3 + 8
      left += estimateLines(natureRule, body, columnTextWidth) * body * 1.5
      leftSections++
      left += L.sectionGap * Math.max(0, leftSections - 1)

      let right = 0
      let rightSections = 0
      if (journalEntry.length > 0) {
        right += label * 1.3 + 8
        right += journalEntry.length * (entry * 1.6)
        if (entryCaption) right += L.captionFont * 1.4
        rightSections++
      }
      if (tip) {
        right += T.space.sm * 2 + label * 1.3 + 8
        right += estimateLines(tip, tipSize, columnTextWidth) * tipSize * 1.5
        rightSections++
      }
      right += L.sectionGap * Math.max(0, rightSections - 1)
      return h + Math.max(left, right) + CONTENT_BOTTOM_PAD
    }

    let sections = 0

    // 2. Amaç
    if (purpose) {
      h += label * 1.3 + 8
      h += estimateLines(purpose, body, sectionTextWidth) * body * 1.5
      sections++
    }

    // 3. Borç / Alacak — natureRule sabit, her zaman ~1 satır
    h += label * 1.3 + 8
    h += estimateLines(natureRule, body, sectionTextWidth) * body * 1.5
    sections++

    // 4. Örnek Yevmiye Kaydı
    if (journalEntry.length > 0) {
      h += label * 1.3 + 8
      h += journalEntry.length * (entry * 1.6)
      if (entryCaption) h += L.captionFont * 1.4
      sections++
    }

    // 5. Püf Noktası — kutu iç dolgusu + başlık + metin
    if (tip) {
      h += T.space.sm * 2
      h += label * 1.3 + 8
      h += estimateLines(tip, tipSize, sectionTextWidth) * tipSize * 1.5
      sections++
    }

    h += L.sectionGap * Math.max(0, sections - 1)
    h += CONTENT_BOTTOM_PAD

    return h
  }

  let scale: number
  try {
    scale = solveCardScale(estimateHeight, availableHeight, minScale, 'AccountCardScene')
  } catch (exc) {
    // Remotion render'ı hata olarak yakalasın — sessiz kırpma yok (v4 spec).
    throw exc
  }

  const titleFont = L.font.title.target * scale
  const bodyFont  = L.font.body.target  * scale
  const labelFont = L.font.label.target * scale
  const entryFont = L.font.entry.target * scale
  const tipFont   = L.font.tip.target   * scale

  return (
    <AbsoluteFill style={{ background: canvasColor ?? T.color.canvas, fontFamily: T.font.body }}>
      {/* Güvenli alan bandı (top→bottom) içinde dikey ortalama — kart artık
          üste sıkışıp altta boşluk bırakmıyor, kendi yüksekliği ne olursa
          olsun bu bant içinde ortalanıyor. */}
      <div style={{
        position: 'absolute', top: L.safeTop, bottom: L.safeBottom, left: L.safeX, right: L.safeX,
        display: 'flex', flexDirection: 'column', justifyContent: 'center',
      }}>
      <div style={{
        opacity: cardOpacity, transform: `translateY(${cardY}px)`,
        background: T.color.surface,
        borderRadius: L.cardRadius,
        boxShadow: T.shadow.card,
        border: `1.5px solid ${T.color.border}`,
        overflow: 'hidden',
      }}>
        {/* 1. Başlık şeridi */}
        <div style={{
          display: 'flex', alignItems: 'center', gap: T.space.md,
          padding: `${T.space.md}px ${L.cardPad}px`,
        }}>
          {/* Hesap kodu rozeti — zemin DAİMA nitelik rengi, sabit boyut */}
          <div style={{
            background: nColor, color: '#FFFFFF',
            borderRadius: 14, padding: '8px 20px',
            fontSize: L.codeBadgeFont, fontWeight: 900,
            fontVariantNumeric: 'tabular-nums',
            flexShrink: 0,
          }}>
            {accountCode}
          </div>
          {/* Hesap adı — ölçekli */}
          <div style={{
            color: T.color.navy900, fontSize: titleFont, fontWeight: 800,
            textTransform: 'uppercase' as const, flex: 1, lineHeight: 1.15,
          }}>
            {accountName}
          </div>
          {/* Nitelik rozeti — tam daire, sabit boyut */}
          <div style={{
            background: nColor, color: '#FFFFFF',
            borderRadius: '50%', width: L.natureBadge, height: L.natureBadge,
            display: 'flex', alignItems: 'center', justifyContent: 'center',
            fontSize: L.natureBadge * 0.42, fontWeight: 800, flexShrink: 0,
          }}>
            {nature}
          </div>
        </div>

        {/* 2–5: içerik bölümleri */}
        <div style={{
          padding: `0 ${L.cardPad}px ${T.space.lg}px`,
          display: format === '16:9' ? 'grid' : 'flex',
          gridTemplateColumns: format === '16:9' ? '1fr 1fr' : undefined,
          gridTemplateAreas: format === '16:9' ? '"purpose journal" "rule tip"' : undefined,
          alignItems: 'start',
          flexDirection: 'column', gap: L.sectionGap,
        }}>
          {/* 2. Amaç */}
          {purpose && (
            <div style={{ display: 'flex', flexDirection: 'column', gap: 8, gridArea: 'purpose' }}>
              <SectionHeader icon={<IconTarget />} label="Amaç" color={nColor} fontSize={labelFont} />
              <span style={{
                fontSize: bodyFont, color: T.color.text, lineHeight: 1.5,
                paddingLeft: SECTION_INDENT,
              }}>
                {purpose}
              </span>
            </div>
          )}

          {/* 3. Borç / Alacak — kural her zaman nature'dan türetilir */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: 8, gridArea: 'rule' }}>
            <SectionHeader icon={<IconScale />} label="Borç / Alacak" color={nColor} fontSize={labelFont} />
            <span style={{
              fontSize: bodyFont, color: nColor, fontWeight: 700, lineHeight: 1.5,
              paddingLeft: SECTION_INDENT,
            }}>
              {natureRule}
            </span>
          </div>

          {/* 4. Örnek Yevmiye Kaydı */}
          {journalEntry.length > 0 && (
            <div style={{ display: 'flex', flexDirection: 'column', gap: 8, gridArea: 'journal' }}>
              <SectionHeader icon={<IconLedger />} label="Örnek Yevmiye Kaydı" color={nColor} fontSize={labelFont} />
              <div style={{
                display: 'flex', flexDirection: 'column', gap: 10,
                paddingLeft: SECTION_INDENT,
              }}>
                {journalEntry.map((line, i) => (
                  <div key={i} style={{
                    display: 'flex', justifyContent: 'space-between', alignItems: 'baseline',
                    paddingLeft: line.side === 'credit' ? L.entryIndent : 0,
                  }}>
                    <span style={{ fontSize: entryFont, color: T.color.text }}>
                      <span style={{ color: T.color.navy500, fontWeight: 700, marginRight: 8 }}>
                        {line.code}
                      </span>
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
                ))}
              </div>
              {entryCaption && (
                <span style={{
                  fontSize: L.captionFont, color: T.color.muted, fontStyle: 'italic',
                  paddingLeft: SECTION_INDENT,
                }}>
                  {entryCaption}
                </span>
              )}
            </div>
          )}

          {/* 5. Püf Noktası — nitelik renginin %8 opaklıklı zemini */}
          {tip && (
            <div style={{
              background: `${nColor}14`,   // ~%8 opaklık (hex alpha 14 ≈ 8%)
              borderRadius: T.radius.chip,
              padding: `${T.space.sm}px ${T.space.md}px`,
              display: 'flex', flexDirection: 'column', gap: 8, gridArea: 'tip',
            }}>
              <SectionHeader icon={<IconBulb />} label="Püf Noktası" color={nColor} fontSize={labelFont} />
              <span style={{
                fontSize: tipFont, color: T.color.navy900, lineHeight: 1.5,
                paddingLeft: SECTION_INDENT,
              }}>
                {tip}
              </span>
            </div>
          )}
        </div>
      </div>
      </div>
    </AbsoluteFill>
  )
}
