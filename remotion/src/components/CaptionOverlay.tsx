/**
 * CaptionOverlay — gömülü altyazı (burned-in).
 * ADIM 4 spec (BÖLÜM 5):
 *   - Anlam grubu bazlı, 3–7 kelime, maks. 2 satır, 54–72 px
 *   - Büyük harf oranı ≤ %35 (aşılırsa title-case'e düşürülür)
 *   - Harf harf karaoke yasak — grup bazlı görünür/kaybolur
 *   - Ses–altyazı farkı: backend gruplaması ≤ 150 ms için başlar
 *   - Kelime ortasında kaybolma yasak (grup bazlı bölme garantisi)
 *   - Alt güvenli alanın (320 px) üstünde
 * 9:16: alttan 340 px + 20 px iç pay.
 * 16:9: opsiyonel, varsayılan kapalı.
 */
import { useCurrentFrame } from 'remotion'
import { interpolate } from 'remotion'
import { T } from '../theme/tokens'

const UPPERCASE_RATIO_LIMIT = 0.35
const FADE_FRAMES = 4     // caption değişiminde fade süresi (kare)

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

function uppercaseRatio(text: string): number {
  const letters = [...text].filter(c => /\p{L}/u.test(c))
  if (letters.length === 0) return 0
  const uppers = letters.filter(c => c === c.toUpperCase() && c !== c.toLowerCase())
  return uppers.length / letters.length
}

function normalizeCaseForDisplay(text: string): string {
  if (uppercaseRatio(text) <= UPPERCASE_RATIO_LIMIT) return text
  // Kısaltmalar (SGS, KDV, TL, KBS ≤4 harf tamamen büyük) korunur
  return text
    .split(' ')
    .map(w => (w.length <= 4 && w === w.toUpperCase())
      ? w
      : w.charAt(0).toUpperCase() + w.slice(1).toLowerCase())
    .join(' ')
}

function wrapToLines(text: string, maxCharsPerLine: number): string[] {
  const words = text.split(' ')
  const lines: string[] = []
  let line = ''

  for (const word of words) {
    const candidate = line ? `${line} ${word}` : word
    if (candidate.length <= maxCharsPerLine) {
      line = candidate
    } else {
      if (line) lines.push(line)
      line = word
      // Maks 2 satır — kalan kelimeler ikinci satıra sığmazsa kes
      if (lines.length >= 1) {
        // İkinci satır: kalan tüm kelimeler alınır (kelime ortasında kesme yok)
        const remaining = words.slice(words.indexOf(word)).join(' ')
        lines.push(remaining)
        return lines.slice(0, 2)
      }
    }
  }
  if (line) lines.push(line)
  return lines.slice(0, 2)
}

export function CaptionOverlay({
  captions = [],
  fps = 30,
  format = '9:16',
  enabled = true,
  fontSize,
  maxCharsPerLine = 30,
}: CaptionOverlayProps) {
  const frame = useCurrentFrame()

  if (!enabled || captions.length === 0) return null

  const currentSec = frame / fps

  // Aktif altyazıyı bul
  const activeIdx = captions.findIndex(
    c => currentSec >= c.start && currentSec < c.end,
  )
  if (activeIdx === -1) return null

  const active = captions[activeIdx]
  const displayText = normalizeCaseForDisplay(active.text)
  const fz = fontSize ?? (format === '9:16' ? T.size9x16.caption : T.size16x9.caption)

  // Fade-in: sahnenin ilk FADE_FRAMES karesi
  const sceneStartFrame = Math.round(active.start * fps)
  const framesIn = frame - sceneStartFrame
  const opacity = framesIn < FADE_FRAMES
    ? interpolate(framesIn, [0, FADE_FRAMES], [0, 1], { extrapolateRight: 'clamp' })
    : 1

  const lines = wrapToLines(displayText, maxCharsPerLine)

  const safe = format === '9:16' ? T.safe9x16 : T.safe16x9

  return (
    <div style={{
      position: 'absolute',
      bottom: safe.bottom + 20,
      left: safe.x,
      right: safe.x,
      display: 'flex',
      flexDirection: 'column',
      alignItems: 'center',
      gap: 6,
      zIndex: 200,
      pointerEvents: 'none',
      opacity,
    }}>
      {lines.map((ln, i) => (
        <div
          key={i}
          style={{
            background: `${T.color.navy900}E0`,   // %88 opak — kontrast ≥ 4.5:1
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
            wordBreak: 'keep-all',    // Türkçe: kelime ortasında satır kırma yasak
          }}
        >
          {ln}
        </div>
      ))}
    </div>
  )
}
