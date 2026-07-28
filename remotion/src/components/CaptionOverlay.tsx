/**
 * CaptionOverlay — gömülü altyazı (burned-in).
 * 9:16: alt üçte birde, güvenli alan içinde, 52-62px, beyaz + lacivert arka plan.
 * 16:9: opsiyonel, varsayılan kapalı.
 */
import { useCurrentFrame } from 'remotion'
import { T } from '../theme/tokens'

interface CaptionEntry {
  start: number   // saniye
  end: number     // saniye
  text: string
}

interface CaptionOverlayProps {
  captions?: CaptionEntry[]
  fps?: number
  format?: '9:16' | '16:9'
  enabled?: boolean
  fontSize?: number
  maxCharsPerLine?: number
}

export function CaptionOverlay({
  captions = [],
  fps = 30,
  format = '9:16',
  enabled = true,
  fontSize,
  maxCharsPerLine = 32,
}: CaptionOverlayProps) {
  const frame = useCurrentFrame()

  if (!enabled || captions.length === 0) return null

  const currentSec = frame / fps
  const active = captions.filter(c => currentSec >= c.start && currentSec < c.end)
  if (active.length === 0) return null

  const text = active.map(c => c.text).join(' ')
  const fz = fontSize ?? (format === '9:16' ? 56 : 40)

  // Maksimum 2 satır
  const lines: string[] = []
  const words = text.split(' ')
  let line = ''
  for (const word of words) {
    if ((line + ' ' + word).trim().length <= maxCharsPerLine) {
      line = (line + ' ' + word).trim()
    } else {
      if (line) lines.push(line)
      line = word
      if (lines.length >= 1) break
    }
  }
  if (line) lines.push(line)
  const displayLines = lines.slice(0, 2)

  const bottomOffset = format === '9:16' ? T.safe9x16.bottom + 20 : T.safe16x9.bottom + 20

  return (
    <div style={{
      position: 'absolute',
      bottom: bottomOffset,
      left: format === '9:16' ? T.safe9x16.x : T.safe16x9.x,
      right: format === '9:16' ? T.safe9x16.x : T.safe16x9.x,
      display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 6,
      zIndex: 200,
      pointerEvents: 'none',
    }}>
      {displayLines.map((ln, i) => (
        <div key={i} style={{
          background: `${T.color.navy900}D9`,  // %85 opak
          borderRadius: 8,
          padding: '10px 24px',
          fontSize: fz,
          fontWeight: 700,
          color: '#FFFFFF',
          textAlign: 'center',
          fontFamily: T.font.body,
          letterSpacing: '0.01em',
          lineHeight: 1.3,
          maxWidth: '100%',
        }}>
          {ln}
        </div>
      ))}
    </div>
  )
}
