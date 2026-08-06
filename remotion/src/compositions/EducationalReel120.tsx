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
import { BrandWatermark } from '../components/BrandWatermark'
import { CaptionOverlay } from '../components/CaptionOverlay'
import { EducationalReelScene } from '../scenes/EducationalReelScene'
import { AccountCardScene } from '../scenes/AccountCardScene'
import { TableScene } from '../scenes/TableScene'
import { RuleBoxScene } from '../scenes/RuleBoxScene'
import { CommonMistakeScene } from '../scenes/CommonMistakeScene'
import { JournalEntryScene } from '../scenes/JournalEntryScene'
import { FPS } from '../brand'
import { TRANSITION_FRAMES, resolveSceneDurationSeconds } from '../utils'

interface Props { storyboard: StoryboardJSON }

// Kart tabanlı sahnelerde filigran KAPALI — kartın arkasından geçmesi
// okunabilirliği bozuyor (Motivation sahnelerindeki aynı sorunun karşılığı,
// 2026-08-05). Yalnızca metin/foto sahnelerinde (ReelHookScene, ReelCtaScene,
// vb.) filigran kalır — orada düz lacivert zemin var, filigran zemine gömülür.
const CARD_BASED_COMPONENTS = new Set([
  'AccountCardScene', 'JournalEntryScene', 'TableScene',
  'CommonMistakeScene', 'RuleBoxScene',
])

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
    const safeSec = resolveSceneDurationSeconds(scene.duration_seconds, scene.id)
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
            {!CARD_BASED_COMPONENTS.has(scene.component as string) && (
              <BrandWatermark theme="dark" opacity={0.08} logoUrl={brand?.logo_url} />
            )}
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

      {/* Logo sağ üstte + sosyal footer — filigran per-sahne yukarıda (kart olmayan sahnelerde) */}
      <BrandOverlay brand={brand} theme="dark" logoSize={120} showFooter showWatermark={false} />
    </AbsoluteFill>
  )
}

export function getReelTotalFrames(storyboard: StoryboardJSON | undefined): number {
  const scenes = storyboard?.scenes ?? []
  return scenes.reduce((acc, s) => {
    const safeSec = resolveSceneDurationSeconds(s.duration_seconds, s.id)
    return acc + Math.max(TRANSITION_FRAMES + 1, Math.round(safeSec * FPS) + TRANSITION_FRAMES)
  }, 0)
}
