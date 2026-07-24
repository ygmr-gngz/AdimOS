/**
 * EducationalReel120 — 2 dakikalık (120s) SGS eğitim Reels composition
 * Format: 1080×1920 (9:16), 30 fps
 * Hedef: 105–125 saniye, en az 8 sahne
 *
 * Akış:
 *   0–5s   : hook    — güçlü kanca
 *   5–20s  : context — konunun önemi
 *   20–45s : content — 1. bilgi / çözüm adımı
 *   45–70s : content — 2. bilgi / örnek
 *   70–95s : mistake — sık yapılan hata
 *   95–110s: tip     — sınav ipucu
 *   110–120s: outro  — özet + logo + yönlendirme
 */
import { AbsoluteFill, Sequence } from 'remotion'
import { StoryboardJSON } from '../types'
import { BrandOverlay } from '../components/BrandOverlay'
import { EducationalReelScene } from '../scenes/EducationalReelScene'
import { FPS } from '../brand'
import { TRANSITION_FRAMES } from '../utils'

interface Props { storyboard: StoryboardJSON }

const DEFAULT_DURATION_SECONDS = 15

export function EducationalReel120({ storyboard }: Props) {
  const { brand, scenes } = storyboard

  let cursor = 0
  const timings = scenes.map(scene => {
    const start = cursor
    const raw = scene.duration_seconds as number | string | undefined | null
    const safeSec = (typeof raw === 'number' && isFinite(raw) && raw > 0) ? raw
      : (typeof raw === 'string' && Number(raw) > 0) ? Number(raw)
      : DEFAULT_DURATION_SECONDS
    const durationFrames = Math.max(TRANSITION_FRAMES + 1, Math.round(safeSec * FPS) + TRANSITION_FRAMES)
    cursor += durationFrames
    return { scene, start, durationFrames }
  })

  return (
    <AbsoluteFill style={{ background: '#0B2A4A', overflow: 'hidden' }}>
      {timings.map(({ scene, start, durationFrames }) => (
        <Sequence key={scene.id} from={start} durationInFrames={durationFrames}>
          <AbsoluteFill>
            <EducationalReelScene scene={scene} brand={brand} />
          </AbsoluteFill>
        </Sequence>
      ))}
      {/* Logo sağ üstte, watermark + sosyal footer */}
      <BrandOverlay brand={brand} theme="dark" logoSize={120} watermarkOpacity={0.08} showFooter />
    </AbsoluteFill>
  )
}

export function getReelTotalFrames(storyboard: StoryboardJSON | undefined): number {
  return (storyboard?.scenes ?? []).reduce((acc, s) => {
    const raw = s.duration_seconds as number | string | undefined | null
    const safeSec = (typeof raw === 'number' && isFinite(raw) && raw > 0) ? raw
      : (typeof raw === 'string' && Number(raw) > 0) ? Number(raw)
      : DEFAULT_DURATION_SECONDS
    return acc + Math.max(TRANSITION_FRAMES + 1, Math.round(safeSec * FPS) + TRANSITION_FRAMES)
  }, 0)
}
