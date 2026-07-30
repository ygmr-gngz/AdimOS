/**
 * EducationalReel120 — 2 dakikalık (120s) SGS eğitim Reels composition
 * Format: 1080×1920 (9:16), 30 fps
 * Desteklenen sahneler:
 *   ReelHookScene, ReelConceptScene, ReelExampleScene, ReelMistakeScene,
 *   ReelExamTipScene, ReelCtaScene — özel layout sahneleri (segment_type inject)
 *   AccountCardScene, TableScene, JournalEntryScene, RuleBoxScene, CommonMistakeScene
 *   EducationalReelScene — genel amaçlı (eski storyboard'lar için)
 */
import { AbsoluteFill, Sequence } from 'remotion'
import { StoryboardJSON } from '../types'
import { BrandOverlay } from '../components/BrandOverlay'
import { CaptionOverlay } from '../components/CaptionOverlay'
import { EducationalReelScene } from '../scenes/EducationalReelScene'
import { AccountCardScene } from '../scenes/AccountCardScene'
import { TableScene } from '../scenes/TableScene'
import { RuleBoxScene } from '../scenes/RuleBoxScene'
import { CommonMistakeScene } from '../scenes/CommonMistakeScene'
import { JournalEntryScene } from '../scenes/JournalEntryScene'
import { FPS } from '../brand'
import { TRANSITION_FRAMES } from '../utils'

interface Props { storyboard: StoryboardJSON }

const DEFAULT_DURATION_SECONDS = 15

function ReelScene({ scene, brand }: { scene: Record<string, unknown>; brand: unknown }) {
  const comp = scene.component as string
  const p = scene as Record<string, unknown>

  switch (comp) {
    case 'AccountCardScene':
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      return <AccountCardScene {...p as any} />
    case 'TableScene':
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      return <TableScene {...p as any} />
    case 'RuleBoxScene':
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      return <RuleBoxScene {...p as any} />
    case 'CommonMistakeScene':
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      return <CommonMistakeScene {...p as any} />
    case 'JournalEntryScene':
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      return <JournalEntryScene {...p as any} />
    case 'ReelHookScene':
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      return <EducationalReelScene scene={{ ...scene, segment_type: 'hook' } as any} brand={brand as any} />
    case 'ReelConceptScene':
    case 'ReelExampleScene':
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      return <EducationalReelScene scene={{ ...scene, segment_type: (scene.segment_type as string) || 'content' } as any} brand={brand as any} />
    case 'ReelMistakeScene':
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      return <EducationalReelScene scene={{ ...scene, segment_type: 'mistake' } as any} brand={brand as any} />
    case 'ReelExamTipScene':
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      return <EducationalReelScene scene={{ ...scene, segment_type: 'tip' } as any} brand={brand as any} />
    case 'ReelCtaScene':
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      return <EducationalReelScene scene={{ ...scene, segment_type: 'outro' } as any} brand={brand as any} />
    case 'EducationalReelScene':
    default:
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      return <EducationalReelScene scene={scene as any} brand={brand as any} />
  }
}

export function EducationalReel120({ storyboard }: Props) {
  const { brand, scenes } = storyboard

  // Tüm sahnelerden altyazı birleştirme
  const allCaptions = scenes.flatMap((s) => {
    const captions = s.captions
    if (!Array.isArray(captions)) return []
    return captions
  })

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
            {/* eslint-disable-next-line @typescript-eslint/no-explicit-any */}
            <ReelScene scene={scene as any} brand={brand} />
          </AbsoluteFill>
        </Sequence>
      ))}

      {/* Altyazı — sahne başına captions[] varsa */}
      {timings.map(({ scene, start }) => {
        const captions = scene.captions
        if (!Array.isArray(captions) || captions.length === 0) return null
        const offsetSec = start / FPS
        const shiftedCaptions = captions.map((c: { start: number; end: number; text: string }) => ({
          ...c,
          start: c.start + offsetSec,
          end: c.end + offsetSec,
        }))
        return (
          <CaptionOverlay
            key={`cap-${scene.id}`}
            captions={shiftedCaptions}
            fps={FPS}
            format="9:16"
            enabled
          />
        )
      })}

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
