/**
 * CardShell — kart tabanlı sahnelerin (AccountCardScene, TableScene,
 * CommonMistakeScene, JournalEntryScene) ortak zemin/kart/gölge/kenarlık
 * ve dikey ortalama mantığı. RuleBoxScene KULLANMAZ — koyu zemin tam ekran.
 *
 * canvas (#F4F6FA) sayfa zemini, surface (#FBFBFB) kart zemini — aralarında
 * hafif ama net fark olsun diye kasıtlı ayrı tutuluyor (bkz. AccountCardScene
 * postmortem: canvas eskiden surface'a neredeyse eşitti, kart görünmez kalıyordu).
 */
import { AbsoluteFill } from 'remotion'
import { T } from '../theme/tokens'

interface CardShellProps {
  format?: '9:16' | '16:9'
  opacity: number
  translateY: number
  children: React.ReactNode
  // Sayfa (canvas) zemini override — kart still özelliği (2026-08-08): aynı kart
  // farklı Instagram fonlarında da üretilebilsin diye. Kartın kendi zemini
  // (surface) buradan ETKİLENMEZ — yalnızca dıştaki AbsoluteFill rengi değişir.
  canvasColor?: string
}

export function CardShell({ format = '9:16', opacity, translateY, children, canvasColor }: CardShellProps) {
  const L = format === '16:9' ? T.layout16x9 : T.layout9x16
  return (
    <AbsoluteFill style={{ background: canvasColor ?? T.color.canvas, fontFamily: T.font.body }}>
      <div style={{
        position: 'absolute', top: L.safeTop, bottom: L.safeBottom, left: L.safeX, right: L.safeX,
        display: 'flex', flexDirection: 'column', justifyContent: 'center',
      }}>
        <div style={{
          opacity, transform: `translateY(${translateY}px)`,
          background: T.color.surface,
          borderRadius: L.cardRadius,
          boxShadow: T.shadow.card,
          border: `1.5px solid ${T.color.border}`,
          overflow: 'hidden',
        }}>
          {children}
        </div>
      </div>
    </AbsoluteFill>
  )
}
