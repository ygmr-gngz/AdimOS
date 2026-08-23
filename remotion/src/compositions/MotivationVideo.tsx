/**
 * MotivationVideo — 120 sn SGS/SMMM motivasyon reels composition
 * Format: 1080×1920 (9:16), 30 fps
 * Sahneler: Hook → Problem → Empathy → Step×2-3 → Focus → Outro
 */
import { AbsoluteFill, Sequence } from 'remotion'
import { StoryboardJSON } from '../types'
import { BrandOverlay } from '../components/BrandOverlay'
import { BrandWatermark } from '../components/BrandWatermark'
import { CaptionOverlay } from '../components/CaptionOverlay'
import { MotivationEditorialScene } from '../scenes/MotivationEditorialScene'
import { ViralTitleScene } from '../scenes/ViralTitleScene'
import { FPS } from '../brand'

interface Props { storyboard: StoryboardJSON }

const DEFAULT_SCENE_SEC = 6

function MotivationSceneDispatcher({
  scene,
  brand,
}: {
  scene: Record<string, unknown>
  brand: unknown
}) {
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const p = { scene: scene as unknown as any, brand: brand as any }
  if (scene.component === 'ViralTitleScene') {
    return <ViralTitleScene scene={p.scene} />
  }
  return <MotivationEditorialScene {...p} />
}

export function MotivationVideo({ storyboard }: Props) {
  const { brand, scenes } = storyboard

  let cursor = 0
  const timings = scenes.map(scene => {
    const start = cursor
    const raw = scene.duration_seconds as number | string | undefined | null
    const safeSec = (typeof raw === 'number' && isFinite(raw) && raw > 0) ? raw
      : (typeof raw === 'string' && Number(raw) > 0) ? Number(raw)
      : DEFAULT_SCENE_SEC
    // Motivasyonda sahne sonuna sessiz geçiş eklemek ses/görüntü kayması yaratıyordu.
    const durationFrames = Math.max(1, Math.round(safeSec * FPS))
    cursor += durationFrames
    return { scene, start, durationFrames }
  })

  return (
    <AbsoluteFill style={{ background: '#FFFEFB', overflow: 'hidden' }}>
      {timings.map(({ scene, start, durationFrames }) => (
        <Sequence key={scene.id} from={start} durationInFrames={durationFrames}>
          <AbsoluteFill>
            {/* eslint-disable-next-line @typescript-eslint/no-explicit-any */}
            <MotivationSceneDispatcher scene={scene as unknown as Record<string, unknown>} brand={brand} />
            <BrandWatermark theme="light" opacity={0.085} rotate={-8} logoUrl={brand?.logo_url} />
          </AbsoluteFill>
        </Sequence>
      ))}

      {/* Altyazılar — sahne captions[] varsa */}
      {timings.map(({ scene, start }) => {
        const captions = scene.captions
        if (!Array.isArray(captions) || captions.length === 0) return null
        const offsetSec = start / FPS
        const shifted = captions.map((c: { start: number; end: number; text: string }) => ({
          ...c,
          start: c.start + offsetSec,
          end:   c.end   + offsetSec,
        }))
        return (
          <CaptionOverlay
            key={`cap-${scene.id}`}
            captions={shifted}
            fps={FPS}
            format="9:16"
            enabled
          />
        )
      })}

      {/* Logo sağ üst + footer — filigran per-sahne yukarıda (fotoğrafsız sahnelerde) */}
      <BrandOverlay brand={brand} theme="light" logoSize={150} showFooter showWatermark={false} />
    </AbsoluteFill>
  )
}

export function getMotivationTotalFrames(storyboard: StoryboardJSON | undefined): number {
  return (storyboard?.scenes ?? []).reduce((acc, s) => {
    const raw = s.duration_seconds as number | string | undefined | null
    const safeSec = (typeof raw === 'number' && isFinite(raw) && raw > 0) ? raw
      : (typeof raw === 'string' && Number(raw) > 0) ? Number(raw)
      : DEFAULT_SCENE_SEC
    return acc + Math.max(1, Math.round(safeSec * FPS))
  }, 0)
}
