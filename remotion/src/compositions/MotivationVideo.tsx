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
import { MotivationScene } from '../scenes/MotivationScene'
import { MotivationHookScene }    from '../scenes/MotivationHookScene'
import { MotivationProblemScene } from '../scenes/MotivationProblemScene'
import { MotivationEmpathyScene } from '../scenes/MotivationEmpathyScene'
import { MotivationStepScene }    from '../scenes/MotivationStepScene'
import { MotivationFocusScene }   from '../scenes/MotivationFocusScene'
import { MotivationOutroScene }   from '../scenes/MotivationOutroScene'
import { FPS } from '../brand'
import { TRANSITION_FRAMES } from '../utils'

interface Props { storyboard: StoryboardJSON }

const DEFAULT_SCENE_SEC = 6

function MotivationSceneDispatcher({
  scene,
  brand,
}: {
  scene: Record<string, unknown>
  brand: unknown
}) {
  const comp = scene.component as string
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const p = { scene: scene as unknown as any, brand: brand as any }

  switch (comp) {
    case 'MotivationHookScene':    return <MotivationHookScene    {...p} />
    case 'MotivationProblemScene': return <MotivationProblemScene {...p} />
    case 'MotivationEmpathyScene': return <MotivationEmpathyScene {...p} />
    case 'MotivationStepScene':    return <MotivationStepScene    {...p} />
    case 'MotivationFocusScene':   return <MotivationFocusScene   {...p} />
    case 'MotivationOutroScene':   return <MotivationOutroScene   {...p} />
    case 'MotivationScene':
    default:
      return <MotivationScene {...p} />
  }
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
    const durationFrames = Math.max(TRANSITION_FRAMES + 1, Math.round(safeSec * FPS) + TRANSITION_FRAMES)
    cursor += durationFrames
    return { scene, start, durationFrames }
  })

  return (
    <AbsoluteFill style={{ background: '#0B2545', overflow: 'hidden' }}>
      {timings.map(({ scene, start, durationFrames }) => (
        <Sequence key={scene.id} from={start} durationInFrames={durationFrames}>
          <AbsoluteFill>
            {/* eslint-disable-next-line @typescript-eslint/no-explicit-any */}
            <MotivationSceneDispatcher scene={scene as unknown as Record<string, unknown>} brand={brand} />
            {/* Filigran yalnızca fotoğrafsız sahnelerde — fotoğraf üzerinde
                mixBlendMode parlak dikdörtgene dönüşüp metni okunmaz kılıyordu. */}
            {scene.visual_source !== 'photo' && (
              <BrandWatermark theme="dark" opacity={0.10} logoUrl={brand?.logo_url} />
            )}
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
      <BrandOverlay brand={brand} theme="dark" logoSize={140} showFooter showWatermark={false} />
    </AbsoluteFill>
  )
}

export function getMotivationTotalFrames(storyboard: StoryboardJSON | undefined): number {
  return (storyboard?.scenes ?? []).reduce((acc, s) => {
    const raw = s.duration_seconds as number | string | undefined | null
    const safeSec = (typeof raw === 'number' && isFinite(raw) && raw > 0) ? raw
      : (typeof raw === 'string' && Number(raw) > 0) ? Number(raw)
      : DEFAULT_SCENE_SEC
    return acc + Math.max(TRANSITION_FRAMES + 1, Math.round(safeSec * FPS) + TRANSITION_FRAMES)
  }, 0)
}
